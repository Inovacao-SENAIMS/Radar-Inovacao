#!/usr/bin/env python3
"""
send_newsletter.py — Envia o digest semanal do Radar de Editais por e-mail.

Arquitetura 100% gratuita (Google):
  assinantes  → Google Sheets (via Web App do Apps Script — appsscript_subscribers.gs)
  envio       → Gmail SMTP (App Password) — smtplib da stdlib
  conteúdo    → data/editais.json (fonte única de verdade) → scripts/email_template.py

USO
  python scripts/send_newsletter.py --preview
      Gera newsletter/preview_<data>.html para revisão no navegador (não envia nada).

  python scripts/send_newsletter.py --test-to seu@email.com
      Envia o digest real apenas para um endereço de teste.

  python scripts/send_newsletter.py --send
      Envia para todos os assinantes ativos (respeita a cota diária do Gmail:
      lote de `batch_size` por execução, com log de envio que evita duplicatas —
      reexecute no dia seguinte para continuar o lote).

  Flags: --force (envia mesmo sem novidades)  --dry-run (monta tudo, não envia)

VARIÁVEIS DE AMBIENTE (segredos — nunca comitar)
  GMAIL_USER          conta Gmail remetente (ex.: radar.editais@gmail.com)
  GMAIL_APP_PASSWORD  senha de app (2FA ativo → minhasenha → Senhas de app)
  NEWSLETTER_API_KEY  a mesma API_KEY definida no Apps Script

  Alternativa local: scripts/newsletter_secrets.json (gitignored), formato:
      {"gmail_user": "...", "gmail_app_password": "...", "newsletter_api_key": "..."}
"""

import argparse
import json
import os
import smtplib
import ssl
import sys
import time
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import email_template as tpl  # noqa: E402

CONFIG_PATH = ROOT / "scripts" / "newsletter_config.json"
SECRETS_PATH = ROOT / "scripts" / "newsletter_secrets.json"
SENT_LOG_PATH = ROOT / "newsletter" / "sent_log.json"


def die(msg):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(1)


def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_secrets():
    """Segredos: variáveis de ambiente têm prioridade sobre newsletter_secrets.json."""
    file_secrets = load_json(SECRETS_PATH, {})
    secrets = {
        "gmail_user": os.environ.get("GMAIL_USER") or file_secrets.get("gmail_user", ""),
        "gmail_app_password": os.environ.get("GMAIL_APP_PASSWORD") or file_secrets.get("gmail_app_password", ""),
        "newsletter_api_key": os.environ.get("NEWSLETTER_API_KEY") or file_secrets.get("newsletter_api_key", ""),
    }
    return secrets


def load_cfg():
    cfg = load_json(CONFIG_PATH)
    cfg.setdefault("webapp_url", "")
    cfg.setdefault("site_url", "")
    cfg.setdefault("sender_name", "Radar de Editais — SENAI MS")
    cfg.setdefault("smtp_host", "smtp.gmail.com")
    cfg.setdefault("smtp_port", 465)
    cfg.setdefault("batch_size", 90)
    cfg.setdefault("delay_segundos", 0.4)
    cfg.setdefault("preview_dir", "newsletter")
    return cfg


def has_updates(data):
    nov = tpl.novos_editais(data)
    alt = tpl.alterados(data)
    enc = tpl.encerrados(data)
    urg = tpl.urgentes(data)
    alerta = (data.get("alerta_prazo") or "").strip()
    return bool(nov or alt or enc or urg or alerta)


def fetch_subscribers(cfg, api_key):
    """Busca assinantes ativos no Web App do Apps Script (?action=list&key=...)."""
    if not cfg.get("webapp_url"):
        die("webapp_url vazio em scripts/newsletter_config.json — veja PRD.md § Configuração.")
    if not api_key:
        die("NEWSLETTER_API_KEY não definida (variável de ambiente ou newsletter_secrets.json).")
    url = cfg["webapp_url"] + "?" + urlencode({"action": "list", "key": api_key})
    try:
        with urlopen(url, timeout=30, context=ssl.create_default_context()) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        die(f"Falha ao consultar o Apps Script ({e}). Verifique a implantação e a URL.")
    if "error" in payload:
        die(f"Apps Script recusou a chave ({payload['error']}). Confira NEWSLETTER_API_KEY.")
    subs = payload.get("assinantes", [])
    # saneamento + dedupe
    seen, out = set(), []
    for s in subs:
        email = str(s.get("email", "")).strip().lower()
        if email and email not in seen:
            seen.add(email)
            out.append({"nome": str(s.get("nome", "")).strip(), "email": email, "token": str(s.get("token", ""))})
    return out


def load_sent_log():
    return load_json(SENT_LOG_PATH, {})


def save_sent_log(log):
    SENT_LOG_PATH.parent.mkdir(exist_ok=True)
    SENT_LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


def connect_smtp(cfg, secrets):
    if not secrets.get("gmail_user") or not secrets.get("gmail_app_password"):
        die("GMAIL_USER / GMAIL_APP_PASSWORD ausentes — veja PRD.md § Configuração (Senha de App).")
    try:
        ctx = ssl.create_default_context()
        smtp = smtplib.SMTP_SSL(cfg["smtp_host"], int(cfg["smtp_port"]), timeout=30, context=ctx)
        smtp.login(secrets["gmail_user"], secrets["gmail_app_password"])
        return smtp
    except Exception as e:
        die(f"Falha ao conectar ao SMTP ({e}). Confira a Senha de App e o 2FA da conta.")


def send_to(smtp, cfg, secrets, sub, mail):
    msg = EmailMessage()
    msg["Subject"] = mail["subject"]
    msg["From"] = formataddr((cfg["sender_name"], secrets["gmail_user"]))
    msg["To"] = sub["email"]
    msg.set_content(mail["text"])
    msg.add_alternative(mail["html"], subtype="html")
    smtp.send_message(msg)


def main():
    ap = argparse.ArgumentParser(description="Envio do digest semanal do Radar de Editais (100% gratuito).")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--preview", action="store_true", help="gera HTML de pré-visualização (não envia)")
    g.add_argument("--test-to", metavar="EMAIL", help="envia apenas para um endereço de teste")
    g.add_argument("--send", action="store_true", help="envia para os assinantes ativos")
    ap.add_argument("--force", action="store_true", help="envia mesmo sem novidades")
    ap.add_argument("--dry-run", action="store_true", help="monta tudo, mostra resumo, não envia")
    args = ap.parse_args()

    cfg = load_cfg()
    secrets = load_secrets()
    data = tpl.load_data()

    if not has_updates(data) and not args.force and not args.preview:
        print("Nada relevante para enviar nesta rodada (sem novidades/alertas).")
        print("Use --force para enviar mesmo assim.")
        return

    mail = tpl.build_email(data, cfg)
    ref = tpl.ref_date(data) or "preview"

    # ---------- PREVIEW ----------
    if args.preview:
        prev_sub = {"nome": "Leitor de Pré-visualização", "email": "teste@example.com", "token": "TOKEN-TESTE"}
        prev_mail = tpl.build_email(data, cfg, prev_sub)
        out_dir = ROOT / cfg["preview_dir"]
        out_dir.mkdir(exist_ok=True)
        out = out_dir / f"preview_{ref}.html"
        out.write_text(prev_mail["html"], encoding="utf-8")
        print(f"Assunto: {prev_mail['subject']}")
        print(f"Pré-visualização gerada: {out}")
        print("Abra o arquivo no navegador para revisar o design antes do envio.")
        return

    # ---------- TESTE ----------
    if args.test_to:
        sub = {"nome": "Teste", "email": args.test_to.strip().lower(), "token": ""}
        test_mail = tpl.build_email(data, cfg, sub)
        smtp = connect_smtp(cfg, secrets)
        try:
            send_to(smtp, cfg, secrets, sub, test_mail)
        finally:
            smtp.quit()
        print(f"Digest de teste enviado para {sub['email']} — confira a caixa de entrada (e o spam).")
        return

    # ---------- ENVIO ----------
    subs = fetch_subscribers(cfg, secrets["newsletter_api_key"])
    if not subs:
        print("Nenhum assinante ativo no momento — nada a enviar.")
        return

    log = load_sent_log()
    ja_enviados = set(log.get(ref, []))
    pendentes = [s for s in subs if s["email"] not in ja_enviados]

    print(f"Assunto: {mail['subject']}")
    print(f"Assinantes ativos: {len(subs)} | já receberam esta edição: {len(ja_enviados)} | pendentes: {len(pendentes)}")

    if not pendentes:
        print("Todos os assinantes já receberam esta edição. Nada a fazer.")
        return

    lote = pendentes[: int(cfg["batch_size"]) - len(ja_enviados)] if len(ja_enviados) < int(cfg["batch_size"]) else []
    restantes_apos_lote = len(pendentes) - len(lote)
    if not lote:
        print(f"Lote diário de {cfg['batch_size']} e-mails já consumido para {ref}.")
        print("Reexecute amanhã para enviar ao restante (o log evita duplicatas).")
        return

    if args.dry_run:
        for s in lote:
            print(f"  [dry-run] enviaria para {s['email']} ({s['nome'] or 'sem nome'})")
        print(f"(dry-run) {len(lote)} envios simulados; restariam {restantes_apos_lote}.")
        return

    smtp = connect_smtp(cfg, secrets)
    enviados, falhas = [], []
    try:
        for s in lote:
            m = tpl.build_email(data, cfg, s)  # e-mail individual (saudação + unsubscribe tokenizado)
            try:
                send_to(smtp, cfg, secrets, s, m)
                enviados.append(s["email"])
                print(f"  OK  {s['email']}")
            except Exception as e:
                falhas.append((s["email"], str(e)))
                print(f"  ERR {s['email']} — {e}")
            time.sleep(float(cfg["delay_segundos"]))
    finally:
        smtp.quit()

    log.setdefault(ref, [])
    log[ref] = sorted(set(log[ref]) | set(enviados))
    save_sent_log(log)

    print()
    print(f"Enviados: {len(enviados)} | Falhas: {len(falhas)} | Restantes p/ próximo lote: {restantes_apos_lote}")
    if restantes_apos_lote > 0:
        print("Cota diária do Gmail: reexecute o comando amanhã para enviar ao restante.")
    if falhas:
        print("Falhas (reexecutar resolve — o log evita duplicatas):")
        for email, err in falhas:
            print(f"  - {email}: {err}")


if __name__ == "__main__":
    main()
