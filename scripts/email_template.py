#!/usr/bin/env python3
"""
email_template.py — Gera o e-mail "digest" do Radar de Editais (HTML + texto),
com design institucional SENAI MS (azul #003876 + laranja #E84910), formato
email-safe: tabelas aninhadas, estilos inline, largura 600px, fontes web-safe.

Entrada: data/editais.json (fonte única de verdade) + configuração.
Saída:   {subject, html, text} — usada por scripts/send_newsletter.py.

Não depende de bibliotecas externas (stdlib only).
"""

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Palette SENAI (tokens.css)
AZUL_900 = "#0E2C63"
AZUL_800 = "#123675"
AZUL_700 = "#164194"
AZUL_100 = "#E4EFFB"
AZUL_50 = "#F2F7FD"
LARANJA_700 = "#B6390C"
LARANJA_600 = "#CF4110"
LARANJA_500 = "#E84910"
LARANJA_100 = "#FCE3D7"
VERDE_OK = "#2E8B4F"
CINZA_900 = "#131C2E"
CINZA_700 = "#3B475F"
CINZA_600 = "#5A667D"
CINZA_200 = "#E3E7ED"
BRANCO = "#FFFFFF"

FONT = "Arial,Helvetica,sans-serif"


def esc(v):
    return escape(str(v if v is not None else ""), quote=True)


def load_data(path=None):
    path = Path(path) if path else ROOT / "data" / "editais.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_config(path=None):
    path = Path(path) if path else ROOT / "scripts" / "newsletter_config.json"
    cfg = {}
    if path.exists():
        cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg.setdefault("site_url", "")
    cfg.setdefault("webapp_url", "")
    return cfg


# ---------------------------------------------------------------- dados ----

def _first(d, *keys, default=""):
    """Retorna o primeiro campo não-vazio (aceita Chave e chave)."""
    for k in keys:
        for key in (k, k.lower(), k.capitalize()):
            v = d.get(key)
            if v not in (None, "", []):
                return v
    return default


def novos_editais(data):
    return (data.get("novidades") or {}).get("novos_editais") or []


def encerrados(data):
    return (data.get("novidades") or {}).get("editais_encerrados") or []


def alterados(data):
    return (data.get("novidades") or {}).get("alteracoes_prazo") or []


def urgentes(data, limite=7):
    """Editais abertos que encerram em `limite` dias (ou hoje)."""
    out = []
    for e in data.get("editais", []):
        if e.get("status") != "aberto":
            continue
        dias = str(e.get("dias") or "").strip()
        m = re.match(r"^(\d+)", dias)
        if m and int(m.group(1)) <= limite:
            out.append((int(m.group(1)), e))
        elif "hoje" in dias.lower():
            out.append((0, e))
    out.sort(key=lambda pair: pair[0])
    return [e for _, e in out]


def ref_date(data):
    return (data.get("meta") or {}).get("reference_date", "")


def ref_date_fmt(data):
    raw = (data.get("meta") or {}).get("reference_date_formatted", "") or ref_date(data)
    # reduz "2026-09-01 · terça-feira — base para..." para "2026-09-01 · terça-feira"
    return raw.split("—")[0].strip()


def build_subject(data):
    n = len(novos_editais(data))
    u = len(urgentes(data))
    d = ref_date(data) or "atualização"
    parts = []
    if n:
        parts.append(f"{n} novo{'s' if n > 1 else ''} {'editais' if n > 1 else 'edital'}")
    if u:
        parts.append(f"{u} encerram em ≤ 7 dias")
    if parts:
        return f"Radar de Editais {d} — " + " · ".join(parts)
    return f"Radar de Editais {d} — atualização semanal"


# ------------------------------------------------------------- blocos ----

def _preheader(data):
    n, c, a = len(novos_editais(data)), len(encerrados(data)), len(alterados(data))
    bits = []
    if n: bits.append(f"{n} novo(s) edital(is)")
    if c: bits.append(f"{c} encerrado(s)")
    if a: bits.append(f"{a} prazo(s) alterado(s)")
    u = len(urgentes(data))
    if u: bits.append(f"{u} encerram em ≤ 7 dias")
    txt = ", ".join(bits) if bits else "panorama semanal de editais de inovação"
    return f"Radar de Editais de {ref_date(data)}: {txt}."


def _section_title(text):
    return (
        f'<p style="margin:0 0 14px;font-size:12px;font-weight:bold;letter-spacing:.1em;'
        f'text-transform:uppercase;color:{LARANJA_700}">{esc(text)}</p>'
    )


def _chip(label, bg):
    return (
        f'<span style="display:inline-block;background:{bg};color:{BRANCO};'
        f'font-size:10px;font-weight:bold;letter-spacing:.06em;padding:3px 9px;'
        f'border-radius:3px;text-transform:uppercase">{esc(label)}</span>'
    )


def _item_box(inner, border=CINZA_200, bg=BRANCO):
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="margin:0 0 10px"><tr><td style="background:{bg};border:1px solid {border};'
        f'border-radius:8px;padding:14px 16px">{inner}</td></tr></table>'
    )


def _edital_block(nome, meta, extra="", link="", chip_html=""):
    parts = [
        f'<div style="margin:0 0 6px">{chip_html}<span style="font-size:14px;font-weight:bold;'
        f'color:{AZUL_800};line-height:1.4">{esc(nome)}</span></div>'
    ]
    if meta:
        parts.append(
            f'<div style="margin:0 0 6px;font-size:12px;color:{CINZA_600};line-height:1.5">{meta}</div>'
        )
    if extra:
        parts.append(
            f'<div style="margin:0;font-size:13px;color:{CINZA_700};line-height:1.55">{extra}</div>'
        )
    if link:
        parts.append(
            f'<div style="margin:8px 0 0"><a href="{esc(link)}" style="font-size:12px;'
            f'font-weight:bold;color:{LARANJA_600};text-decoration:none">Abrir edital →</a></div>'
        )
    return "".join(parts)


def _meta_line(*pairs):
    return " · ".join(
        f'<b style="color:{CINZA_700}">{esc(k)}:</b> {esc(v)}' for k, v in pairs if v
    )


def _kpis(data):
    s = data.get("stats") or {}
    cells = [
        (s.get("abertos", "—"), "Editais abertos", AZUL_700),
        (s.get("continuos", "—"), "Fluxo contínuo", VERDE_OK),
        (s.get("em_breve", "—"), "Em breve", CINZA_600),
        (s.get("encerram_7d", "—"), "Encerram em ≤ 7 dias", LARANJA_500),
    ]
    tds = []
    for num, label, cor in cells:
        tds.append(
            f'<td width="25%" style="background:{AZUL_50};border:1px solid {CINZA_200};'
            f'padding:14px 10px;text-align:center">'
            f'<div style="font-size:24px;font-weight:bold;color:{cor};line-height:1">{esc(num)}</div>'
            f'<div style="font-size:10px;color:{CINZA_600};line-height:1.4;margin-top:6px;'
            f'letter-spacing:.04em;text-transform:uppercase">{esc(label)}</div>'
            f'</td>'
        )
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="8" border="0">'
        f'<tr>{"".join(tds)}</tr></table>'
    )


def _novidades_blocks(data):
    html = ""
    for e in novos_editais(data):
        nome = _first(e, "Edital", "edital")
        fonte = _first(e, "Fonte", "fonte")
        abertura = _first(e, "Abertura", "abertura")
        encerr = _first(e, "Encerramento", "encerramento")
        destaque = _first(e, "Destaque", "destaque")
        link = _first(e, "Link", "link")
        meta = _meta_line(("Fonte", fonte), ("Abre", abertura), ("Encerra", encerr))
        html += _item_box(_edital_block(nome, meta, esc(destaque), link, _chip("Novo", VERDE_OK)))
    for e in alterados(data):
        nome = _first(e, "Edital", "edital")
        alt = _first(e, "Alteração", "alteracao")
        html += _item_box(_edital_block(nome, "", esc(alt), "", _chip("Prazo alterado", LARANJA_500)))
    for e in encerrados(data):
        nome = _first(e, "Edital", "edital")
        fonte = _first(e, "Fonte", "fonte")
        motivo = _first(e, "Motivo do encerramento", "Motivo", "motivo")
        html += _item_box(
            _edital_block(nome, _meta_line(("Fonte", fonte)), esc(motivo), "", _chip("Encerrado", CINZA_600)),
            border=CINZA_200, bg="#FBFCFE",
        )
    return html


def _alerta_block(data):
    alerta = (data.get("alerta_prazo") or "").strip()
    if not alerta:
        return ""
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="margin:0 0 28px"><tr><td style="background:{LARANJA_100};'
        f'border-left:4px solid {LARANJA_500};border-radius:6px;padding:14px 16px">'
        f'<div style="margin:0 0 6px;font-size:11px;font-weight:bold;letter-spacing:.1em;'
        f'text-transform:uppercase;color:{LARANJA_700}">Alerta de prazo</div>'
        f'<div style="margin:0;font-size:13px;line-height:1.6;color:{CINZA_900}">{esc(alerta)}</div>'
        f'</td></tr></table>'
    )


def _urgentes_blocks(data):
    html = ""
    for e in urgentes(data):
        meta = _meta_line(
            ("Fonte", e.get("fonte")),
            ("Encerra", e.get("encerramento")),
            ("Valor", e.get("valor")),
        )
        extra = e.get("publico", "")
        link = e.get("link", "")
        html += _item_box(
            _edital_block(e.get("edital", ""), meta, esc(extra) if extra else "", link, ""),
            border=LARANJA_100, bg="#FFFBF9",
        )
    return html


def _resumo_blocks(data, max_items=3):
    linhas = (data.get("resumo_executivo") or [])[:max_items]
    if not linhas:
        return ""
    items = "".join(
        f'<tr><td style="padding:0 0 8px;font-size:13px;line-height:1.6;color:{CINZA_900}">'
        f'<span style="color:{LARANJA_500};font-weight:bold">•</span>&nbsp; {esc(l)}</td></tr>'
        for l in linhas
    )
    return f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{items}</table>'


def _header(cfg, data):
    site = (cfg.get("site_url") or "").strip()
    if site:
        logo = (
            f'<img src="{esc(site)}assets/logo-senai-fiems.png" alt="SENAI MS — Sistema FIEMS" '
            f'width="150" style="display:block;border:0;max-width:150px;height:auto">'
        )
    else:
        logo = (
            f'<span style="font-size:20px;font-weight:bold;color:{AZUL_800}">SENAI MS</span>'
        )
    return (
        # cabeçalho claro (logo funciona sobre fundo claro, como no site)
        f'<tr><td style="background:{BRANCO};padding:22px 28px 18px">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td align="left" valign="middle">{logo}</td>'
        f'<td align="right" valign="middle">'
        f'<div style="font-size:11px;font-weight:bold;color:{LARANJA_500};letter-spacing:.12em;'
        f'text-transform:uppercase">Radar de Editais</div>'
        f'<div style="font-size:12px;color:{CINZA_600};margin-top:3px">{esc(ref_date_fmt(data))}</div>'
        f'</td></tr></table></td></tr>'
        # barra laranja (assim como as "bars" do site)
        f'<tr><td height="4" bgcolor="{LARANJA_500}" style="font-size:0;line-height:0">&nbsp;</td></tr>'
    )


def _cta(cfg, data):
    site = (cfg.get("site_url") or "").strip()
    total = len(data.get("editais", []))
    nota = f"{total} editais mapeados · filtros por instituto SENAI, status e prazo" if total else ""
    if site:
        botao = (
            f'<a href="{esc(site)}" style="display:inline-block;background:{LARANJA_500};'
            f'color:{BRANCO};text-decoration:none;font-weight:bold;font-size:15px;'
            f'padding:15px 36px;border-radius:6px">Ver painel completo de editais</a>'
        )
    else:
        botao = (
            f'<span style="display:inline-block;background:{AZUL_50};color:{AZUL_700};'
            f'font-size:13px;padding:12px 24px;border-radius:6px">'
            f'Painel completo disponível na intranet SENAI MS</span>'
        )
    return (
        f'<tr><td style="padding:8px 28px 30px;text-align:center">'
        f'<p style="margin:0 0 16px">{botao}</p>'
        f'<p style="margin:0;font-size:12px;color:{CINZA_600}">{esc(nota)}</p>'
        f'</td></tr>'
    )


def _footer(cfg, sub):
    webapp = (cfg.get("webapp_url") or "").strip()
    if webapp and sub and sub.get("token"):
        cancel = f'{esc(webapp)}?cancel={esc(sub["token"])}'
        cancel_link = f'<a href="{cancel}" style="color:#F06B37;text-decoration:underline">Cancelar inscrição</a>'
    else:
        cancel_link = "Responder este e-mail pedindo o cancelamento"
    return (
        f'<tr><td style="background:{AZUL_900};padding:24px 28px;color:{BRANCO};'
        f'font-size:11px;line-height:1.7">'
        f'<b style="color:{BRANCO}">SENAI MS · Sistema FIEMS — Radar de Editais de Inovação</b><br>'
        f'Você recebe este e-mail porque assinou as atualizações do Radar de Editais.<br>'
        f'{cancel_link} · respondendo este e-mail você fala com a equipe de monitoramento.<br>'
        f'<span style="color:#A6AFBE">Tratamos seus dados (nome e e-mail) exclusivamente para este envio, '
        f'com consentimento confirmado por e-mail, conforme a LGPD (Lei nº 13.709/2018). '
        f'Campo Grande · MS · Brasil · © 2026</span>'
        f'</td></tr>'
    )


# ------------------------------------------------------------- e-mail ----

def build_email(data, cfg, sub=None):
    """Monta o e-mail completo.

    data : dict — conteúdo de data/editais.json
    cfg  : dict — newsletter_config.json (site_url, webapp_url, ...)
    sub  : dict|None — {nome, email, token} do assinante (None = pré-visualização)
    """
    nome = (sub or {}).get("nome") or ""
    saudacao = f"Olá, {esc(nome)}!" if nome else "Olá!"
    nov = novos_editais(data)
    alt = alterados(data)
    enc = encerrados(data)
    urg = urgentes(data)

    # Pré-header (escondido) + saudação
    intro = []
    if nov or alt or enc:
        intro.append("o que mudou desde a última rodada do radar")
    if urg:
        intro.append(f"{len(urg)} edital(is) encerrando em ≤ 7 dias")
    intro_txt = " e ".join(intro) if intro else "o panorama semanal de editais"

    body = []

    body.append(
        f'<tr><td style="padding:28px 28px 6px">'
        f'<div style="font-size:19px;font-weight:bold;color:{AZUL_900};margin:0 0 8px">{saudacao}</div>'
        f'<div style="font-size:14px;line-height:1.6;color:{CINZA_700};margin:0">'
        f'Aqui está a atualização de <b>{esc(ref_date_fmt(data))}</b> — {esc(intro_txt)}.</div>'
        f'</td></tr>'
    )

    body.append(f'<tr><td style="padding:22px 28px 0">{_kpis(data)}</td></tr>')

    if nov or alt or enc:
        body.append(
            f'<tr><td style="padding:28px 28px 0">'
            + _section_title("O que mudou nesta rodada")
            + _novidades_blocks(data)
            + "</td></tr>"
        )

    alerta = _alerta_block(data)
    if alerta:
        body.append(f'<tr><td style="padding:12px 28px 0">{alerta}</td></tr>')

    if urg:
        body.append(
            f'<tr><td style="padding:12px 28px 0">'
            + _section_title("Encerram em ≤ 7 dias — prioridade")
            + _urgentes_blocks(data)
            + "</td></tr>"
        )

    resumo = _resumo_blocks(data)
    if resumo:
        body.append(
            f'<tr><td style="padding:12px 28px 0">'
            + _section_title("Resumo executivo")
            + resumo + "</td></tr>"
        )

    body.append(_cta(cfg, data))
    body.append(_footer(cfg, sub))

    html = (
        '<!DOCTYPE html>\n<html lang="pt-BR">\n'
        f'<body style="margin:0;padding:0;background:{AZUL_50}">\n'
        # pré-header invisível (resumo exibido ao lado do assunto)
        f'<div style="display:none;max-height:0;overflow:hidden;opacity:0">{esc(_preheader(data))}</div>\n'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{AZUL_50}">\n'
        f'<tr><td align="center" style="padding:24px 10px">\n'
        f'<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" '
        f'style="width:600px;max-width:600px;background:{BRANCO};border-radius:12px;overflow:hidden;'
        f'font-family:{FONT}">\n'
        + "".join(body)
        + "\n</table>\n</td></tr>\n</table>\n</body>\n</html>"
    )

    text = _build_text(data, cfg, sub)
    return {"subject": build_subject(data), "html": html, "text": text}


def _build_text(data, cfg, sub):
    site = (cfg.get("site_url") or "").strip()
    webapp = (cfg.get("webapp_url") or "").strip()
    nome = (sub or {}).get("nome") or ""
    lines = []
    lines.append(f"RADAR DE EDITAIS DE INOVACAO - SENAI MS / Sistema FIEMS")
    lines.append(f"Atualizacao de {ref_date_fmt(data)}")
    lines.append("")
    if nome:
        lines.append(f"Ola, {nome}!")
        lines.append("")
    s = data.get("stats") or {}
    lines.append(f"- Editais abertos: {s.get('abertos', '—')}")
    lines.append(f"- Fluxo continuo: {s.get('continuos', '—')}")
    lines.append(f"- Em breve: {s.get('em_breve', '—')}")
    lines.append(f"- Encerram em <= 7 dias: {s.get('encerram_7d', '—')}")
    lines.append("")
    nov, alt, enc, urg = novos_editais(data), alterados(data), encerrados(data), urgentes(data)
    if nov or alt or enc:
        lines.append("O QUE MUDOU NESTA RODADA")
        for e in nov:
            lines.append(f"[NOVO] {_first(e, 'Edital', 'edital')} — {_first(e, 'Fonte', 'fonte')}")
            d = _first(e, "Destaque", "destaque")
            if d:
                lines.append(f"       {d}")
        for e in alt:
            lines.append(f"[PRAZO ALTERADO] {_first(e, 'Edital', 'edital')}: {_first(e, 'Alteração', 'alteracao')}")
        for e in enc:
            lines.append(f"[ENCERRADO] {_first(e, 'Edital', 'edital')} — {_first(e, 'Motivo do encerramento', 'Motivo', 'motivo')}")
        lines.append("")
    if (data.get("alerta_prazo") or "").strip():
        lines.append("ALERTA DE PRAZO")
        lines.append(data["alerta_prazo"].strip())
        lines.append("")
    if urg:
        lines.append("ENCERRAM EM <= 7 DIAS")
        for e in urg:
            lines.append(f"- {e.get('edital', '')} ({e.get('fonte', '')}) — encerra: {e.get('encerramento', '')}")
            if e.get("link"):
                lines.append(f"  {e['link']}")
        lines.append("")
    for l in (data.get("resumo_executivo") or [])[:3]:
        lines.append(f"* {l}")
    lines.append("")
    if site:
        lines.append(f"Ver painel completo: {site}")
    if webapp and sub and sub.get("token"):
        lines.append(f"Cancelar inscricao: {webapp}?cancel={sub['token']}")
    lines.append("")
    lines.append("Voce recebe este e-mail porque assinou as atualizacoes do Radar de Editais.")
    lines.append("SENAI MS - Sistema FIEMS - Campo Grande, MS - Brasil")
    return "\n".join(lines)


if __name__ == "__main__":
    # Pré-visualização rápida: python scripts/email_template.py
    data = load_data()
    cfg = load_config()
    out = build_email(data, cfg, {"nome": "Leitor de Pré-visualização", "email": "teste@teste", "token": "TOKEN-TESTE"})
    dest = ROOT / "newsletter" / "preview_standalone.html"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(out["html"], encoding="utf-8")
    print(f"Assunto: {out['subject']}")
    print(f"Gerado: {dest}")
