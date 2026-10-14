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
import re
import sys
import time
import unicodedata
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gemini_client as gc           # noqa: E402
import groq_client as gq             # noqa: E402
import research_prompt as rp         # noqa: E402
import web_search as ws              # noqa: E402
from monitor_report import build_markdown, compute_stats, compute_dias  # noqa: E402
from validate_editais import validate, ValidationError  # noqa: E402

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

DEFAULT_SCOPE = "Nacional (BR), estadual (prioridade MS/Centro-Oeste) e internacional com elegibilidade do Brasil."
DEFAULT_METHOD = ("Revisão automática em fontes oficiais (FAPESP, CNPq, CONFAP, FAPERJ, "
                  "FINEP/MCTI, FUNDECT-MS e outras) com LLM + busca web; prazos comparados "
                  "com a data de referência. O monitor não é inventário exaustivo.")


def _load_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return default if default is not None else {}
    return json.loads(p.read_text(encoding="utf-8"))


def _groq_generate(prompt, *, model, api_key, attempts=3, delay=65, **kwargs):
    """Chama o Groq com retry em 429/413/503 (limite de TPM do plano gratuito)."""
    last = None
    for attempt in range(attempts):
        try:
            return gq.generate(prompt, model=model, api_key=api_key, **kwargs)
        except gq._HttpError as exc:
            last = exc
            if exc.code in (429, 413, 503) and attempt < attempts - 1:
                time.sleep(delay)
                continue
            raise
    raise last


def _norm_key(value):
    """Normaliza um nome de campo: sem acento, minúsculo, separado por '_'."""
    s = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.strip().lower()).strip("_")


_EDITAL_FIELDS = {
    "edital": ["edital", "nome", "title", "nome_do_edital"],
    "fonte": ["fonte", "source", "instituicao", "instituicao_fonte"],
    "status": ["status", "situacao"],
    "abertura": ["abertura", "inicio", "start", "data_de_abertura", "data_abertura"],
    "encerramento": ["encerramento", "prazo", "deadline", "fim", "data_de_encerramento", "data_encerramento"],
    "publico": ["publico", "publico_alvo"],
    "valor": ["valor", "valor_faixa", "faixa", "investimento"],
    "contrapartida": ["contrapartida"],
    "exigencias": ["exigencias", "principais_exigencias"],
    "link": ["link", "url"],
}
_STATUS_MAP = {"aberto": "aberto", "aberta": "aberto", "em_breve": "breve", "breve": "breve",
               "fluxo_continuo": "continuo", "continuo": "continuo"}
_GRAU_MAP = {"alta": "alta", "media": "media", "baixa": "baixa"}
_PLACEHOLDER_RE = re.compile(r"\b(TODO|TBD|PENDENTE|LOREM)\b", re.I)


def _sanitize(value, default="Não encontrado"):
    """Troca vazio ou placeholder por um valor aceitável."""
    text = str(value if value is not None else "").strip()
    if not text or _PLACEHOLDER_RE.search(text):
        return default
    return text


def _pick(low, aliases, default=""):
    for alias in aliases:
        val = low.get(alias)
        if val not in (None, ""):
            return val
    return default


def _norm_status(value):
    return _STATUS_MAP.get(_norm_key(value), _norm_key(value))


def _normalize_edital(raw):
    low = {_norm_key(k): v for k, v in (raw or {}).items()}
    out = {field: _pick(low, aliases) for field, aliases in _EDITAL_FIELDS.items()}
    out["status"] = _norm_status(out["status"])
    out["edital"] = str(out["edital"] or "").strip()
    for field in ("fonte", "abertura", "encerramento", "publico", "valor",
                  "contrapartida", "exigencias"):
        out[field] = _sanitize(out[field])
    return out


def _normalize_aderencia(raw, edital_fallback=""):
    low = {_norm_key(k): v for k, v in (raw or {}).items()}
    grau_raw = str(_pick(low, ["grau", "grau_de_aderencia", "aderencia"])).strip().lower()
    if "sem aderencia" in _norm_key(grau_raw).replace("_", " "):
        grau = "none"
    else:
        grau = _GRAU_MAP.get(_norm_key(grau_raw), "none")
    return {
        "edital": _sanitize(_pick(low, ["edital", "nome"], edital_fallback), ""),
        "institutos": _sanitize(_pick(low, ["institutos", "instituto_s_com_maior_aderencia",
                                            "instituto"]), "—"),
        "grau": grau,
        "foco_educacional": _sanitize(_pick(low, ["foco_educacional"]), "Não"),
        "justificativa": _sanitize(_pick(low, ["justificativa"])),
    }


def _normalize_nao_confirmado(raw):
    low = {_norm_key(k): v for k, v in (raw or {}).items()}
    return {
        "edital": _pick(low, ["edital", "nome"]),
        "fonte": _pick(low, ["fonte", "source"]),
        "motivo": _pick(low, ["motivo", "razao", "razão"]),
    }


def _merge_chunk_payloads(payloads):
    """Funde os blocos normalizando os nomes de campo e deduplicando por edital."""
    editais, aderencia, nao_confirmado = [], [], []
    seen, seen_ader, seen_nc = set(), set(), set()
    for payload in payloads:
        for raw in payload.get("editais", []) or []:
            e = _normalize_edital(raw)
            name = e["edital"].strip()
            key = name.lower()
            if not key:
                continue
            if _PLACEHOLDER_RE.search(name):
                continue
            if e["status"] not in ("aberto", "breve", "continuo"):
                continue
            if not str(e["link"]).lower().startswith("http"):
                continue
            if key not in seen:
                seen.add(key)
                editais.append(e)
            low = {_norm_key(k): v for k, v in (raw or {}).items()}
            embedded = low.get("aderencia")
            if isinstance(embedded, dict) and key not in seen_ader:
                seen_ader.add(key)
                aderencia.append(_normalize_aderencia(embedded, edital_fallback=name))
        for raw in payload.get("aderencia", []) or []:
            a = _normalize_aderencia(raw)
            key = a["edital"].strip().lower()
            if key and key not in seen_ader:
                seen_ader.add(key)
                aderencia.append(a)
        for raw in payload.get("nao_confirmado", []) or []:
            n = _normalize_nao_confirmado(raw)
            key = n["edital"].strip().lower()
            if key and key not in seen_nc:
                seen_nc.add(key)
                nao_confirmado.append(n)
    return {"editais": editais, "aderencia": aderencia, "nao_confirmado": nao_confirmado}


def _synthesize_summary(payload, today):
    """Deriva resumo executivo e alerta de prazo a partir dos editais fundidos."""
    editais = payload.get("editais", [])
    stats = compute_stats(editais, today)
    urgent = [e for e in editais
              if e.get("status") == "aberto"
              and compute_dias(e, today).isdigit() and int(compute_dias(e, today)) <= 7]
    alerta = "; ".join(f"{e.get('edital','')} ({e.get('encerramento','')})" for e in urgent)
    payload["alerta_prazo"] = alerta
    payload["resumo_executivo"] = [
        f"Abertos agora: {stats['abertos']} editais com etapa vigente em {today:%d/%m/%Y}, "
        f"mais {stats['continuos']} linhas de fluxo contínuo sem prazo definido.",
        f"Em breve: {stats['em_breve']} chamadas com abertura programada.",
        f"Alerta (encerramento em ≤ 7 dias): {len(urgent)} editais: {alerta or 'nenhum'}.",
        f"Não confirmado: {len(payload.get('nao_confirmado', []))} itens sem janela de inscrição confirmada.",
    ]
    return payload


def _run_groq_chunked(previous, today, methodology, *, model, api_key,
                      search_provider, search_key, delay, per_chunk=12, base_limit=25):
    """Geração em blocos: 1 requisição por grupo de fontes, com throttle de TPM.

    Usa `reasoning_effort="low"` e `max_tokens` limitado: o gpt-oss tende a gastar
    o orçamento de tokens "raciocinando" e cortar o JSON final (finish_reason=length).
    """
    prov, skey = ws.resolve_provider(search_provider, search_key)
    groups = ws.chunk_groups(today.year)
    payloads = []
    for index, (label, queries) in enumerate(groups):
        context = ws.build_context(queries, provider=prov, api_key=skey, count=2, max_chars=300)
        prompt = rp.build(previous, today.isoformat(), methodology, context=context,
                          focus=label, max_editais=per_chunk, max_base=base_limit)
        payloads.append(_groq_generate(prompt, model=model, api_key=api_key, delay=delay,
                                       reasoning_effort="low", max_tokens=4096))
        if index < len(groups) - 1:
            time.sleep(delay)
    return _synthesize_summary(_merge_chunk_payloads(payloads), today)


def run(today, *, base_path, out_json, out_js, md_dir, offline=None, provider="gemini",
        model=None, api_key="", dry_run=False, min_editais=10,
        search_provider="auto", search_key="", queries=None, chunk=False, chunk_delay=65):
    from md_to_json import parse_markdown

    previous = _load_json(base_path, {}) or {}

    if offline:
        gemini_payload = _load_json(offline)
    else:
        methodology = previous.get("meta", {}).get("methodology", DEFAULT_METHOD)
        if provider == "groq":
            if chunk:
                gemini_payload = _run_groq_chunked(
                    previous, today, methodology, model=model or gq.DEFAULT_MODEL,
                    api_key=api_key or os.environ.get("GROQ_API_KEY", ""),
                    search_provider=search_provider, search_key=search_key, delay=chunk_delay)
            else:
                prov, skey = ws.resolve_provider(search_provider, search_key)
                qs = queries or ws.default_queries(today.year)
                context = ws.build_context(qs, provider=prov, api_key=skey)
                prompt = rp.build(previous, today.isoformat(), methodology, context=context)
                gemini_payload = gq.generate(
                    prompt, model=model or gq.DEFAULT_MODEL,
                    api_key=api_key or os.environ.get("GROQ_API_KEY", ""))
        else:
            prompt = rp.build(previous, today.isoformat(), methodology)
            gemini_payload = gc.generate(prompt, model=model or DEFAULT_GEMINI_MODEL,
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
    ap.add_argument("--provider", choices=["gemini", "groq"], default="gemini",
                    help="Motor que gera o JSON (padrão: gemini).")
    ap.add_argument("--model", default=None, help="Modelo do provedor (padrão conforme --provider).")
    ap.add_argument("--search-provider", choices=["auto", "tavily", "brave"], default="auto",
                    help="Provedor de busca web usado com --provider groq (padrão: auto).")
    ap.add_argument("--chunk", action="store_true",
                    help="Geração em blocos (recomendado no Groq gratuito: TPM ≤ 8k).")
    ap.add_argument("--chunk-delay", type=int, default=65,
                    help="Segundos de espera entre blocos para respeitar o TPM (padrão: 65).")
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
                     md_dir=ROOT / "data", offline=args.offline, provider=args.provider,
                     model=args.model, dry_run=args.dry_run, min_editais=args.min_editais,
                     search_provider=args.search_provider, chunk=args.chunk,
                     chunk_delay=args.chunk_delay)
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
