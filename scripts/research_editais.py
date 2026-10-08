#!/usr/bin/env python3
"""research_editais.py — orquestra a atualização automática do Radar de Editais.

Uso:
    python scripts/research_editais.py [--date YYYY-MM-DD] [--model gemini-2.5-flash]
        [--base data/editais.json] [--offline FILE] [--dry-run]

--offline  usa uma resposta JSON fixa do Gemini (não chama a API) — para testes.
--dry-run  gera e valida, mas não escreve arquivos.
"""
import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gemini_client as gc           # noqa: E402
import research_prompt as rp         # noqa: E402
from monitor_report import build_markdown   # noqa: E402
from validate_editais import validate, ValidationError  # noqa: E402

DEFAULT_SCOPE = "Nacional (BR), estadual (prioridade MS/Centro-Oeste) e internacional com elegibilidade do Brasil."
DEFAULT_METHOD = ("Revisão automática em fontes oficiais (FAPESP, CNPq, CONFAP, FAPERJ, "
                  "FINEP/MCTI, FUNDECT-MS e outras) com Gemini + busca web; prazos comparados "
                  "com a data de referência. O monitor não é inventário exaustivo.")


def _load_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return default if default is not None else {}
    return json.loads(p.read_text(encoding="utf-8"))


def run(today, *, base_path, out_json, out_js, md_dir, offline=None, model="gemini-2.5-flash",
        api_key="", dry_run=False, min_editais=10):
    from md_to_json import parse_markdown

    previous = _load_json(base_path, {}) or {}

    if offline:
        gemini_payload = _load_json(offline)
    else:
        methodology = previous.get("meta", {}).get("methodology", DEFAULT_METHOD)
        prompt = rp.build(previous, today.isoformat(), methodology)
        gemini_payload = gc.generate(prompt, model=model,
                                     api_key=api_key or os.environ.get("GEMINI_API_KEY", ""),
                                     schema=rp.RESPONSE_SCHEMA, use_search=True)

    validate(gemini_payload, previous=previous, min_editais=min_editais)

    scope = previous.get("meta", {}).get("scope", DEFAULT_SCOPE)
    md = build_markdown(gemini_payload, today, previous, scope, DEFAULT_METHOD)

    # Round-trip: o parser canônico revalida o .md gerado.
    parsed = parse_markdown(md)
    if len(parsed["editais"]) < len(gemini_payload["editais"]):
        raise ValidationError(
            f"round-trip perdeu linhas: {len(parsed['editais'])} < {len(gemini_payload['editais'])}")

    if dry_run:
        return parsed

    md_path = Path(md_dir) / f"Monitoramento_Editais_Inovacao_{today.isoformat()}.md"
    md_path.write_text(md, encoding="utf-8")
    Path(out_json).write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(out_js).write_text("window.EDITAIS_DATA = " + json.dumps(parsed, ensure_ascii=False) + ";\n",
                            encoding="utf-8")
    return parsed


def main():
    ap = argparse.ArgumentParser(description="Atualização automática do Radar de Editais.")
    ap.add_argument("--date", help="Data de referência (YYYY-MM-DD). Padrão: hoje.")
    ap.add_argument("--model", default="gemini-2.5-flash")
    ap.add_argument("--base", default=str(ROOT / "data" / "editais.json"))
    ap.add_argument("--offline", help="Arquivo JSON com a resposta do Gemini (sem chamar a API).")
    ap.add_argument("--dry-run", action="store_true", help="Gera e valida, mas não escreve arquivos.")
    ap.add_argument("--min-editais", type=int, default=10)
    args = ap.parse_args()

    today = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else date.today()
    try:
        result = run(today, base_path=args.base,
                     out_json=ROOT / "data" / "editais.json",
                     out_js=ROOT / "data" / "editais.js",
                     md_dir=ROOT / "data", offline=args.offline, model=args.model,
                     api_key=os.environ.get("GEMINI_API_KEY", ""), dry_run=args.dry_run,
                     min_editais=args.min_editais)
    except Exception as exc:  # noqa: BLE001 — a mensagem vira Issue no workflow
        print(f"ERRO na atualização automática: {exc}", file=sys.stderr)
        sys.exit(1)

    tag = " (dry-run)" if args.dry_run else ""
    print(f"OK{tag} — {len(result['editais'])} editais, {result['stats']['abertos']} abertos.")

    if args.dry_run:
        return
    nov = result.get("novidades", {})
    has = bool(nov.get("novos_editais") or nov.get("editais_encerrados")
               or nov.get("alteracoes_prazo") or result.get("alerta_prazo"))
    print("HAS_UPDATES=" + ("1" if has else "0"))


if __name__ == "__main__":
    main()
