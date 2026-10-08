#!/usr/bin/env python3
"""research_prompt.py — schema e prompt para a pesquisa automática (Gemini)."""

_STR = {"type": "STRING"}

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "editais": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "edital": _STR, "fonte": _STR,
                    "status": {"type": "STRING", "enum": ["aberto", "breve", "continuo"]},
                    "abertura": _STR, "encerramento": _STR, "publico": _STR,
                    "valor": _STR, "contrapartida": _STR, "exigencias": _STR, "link": _STR,
                },
                "required": ["edital", "fonte", "status", "abertura", "encerramento",
                             "publico", "valor", "contrapartida", "exigencias", "link"],
            },
        },
        "aderencia": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "edital": _STR, "institutos": _STR,
                    "grau": {"type": "STRING", "enum": ["alta", "media", "baixa", "none"]},
                    "foco_educacional": _STR, "justificativa": _STR,
                },
                "required": ["edital", "institutos", "grau", "foco_educacional", "justificativa"],
            },
        },
        "nao_confirmado": {
            "type": "ARRAY",
            "items": {"type": "OBJECT", "properties": {"edital": _STR, "fonte": _STR, "motivo": _STR},
                      "required": ["edital", "fonte", "motivo"]},
        },
        "resumo_executivo": {"type": "ARRAY", "items": _STR},
        "alerta_prazo": _STR,
    },
    "required": ["editais", "aderencia", "nao_confirmado", "resumo_executivo", "alerta_prazo"],
}

_INSTITUTOS = (
    "IST Alimentos e Bebidas (Dourados/MS), IST Eficiência Operacional (Campo Grande/MS) e "
    "ISI Biomassa (Três Lagoas/MS, Unidade Embrapii)."
)


def _summarize(base):
    rows = []
    for e in base.get("editais", []):
        rows.append(
            f"- {e.get('edital','')} | fonte: {e.get('fonte','')} | "
            f"status: {e.get('status','')} | encerramento: {e.get('encerramento','')} | {e.get('link','')}"
        )
    return "\n".join(rows) if rows else "(base anterior vazia)"


def build(base, today_iso, methodology):
    return f"""Você é o analista de monitoramento de editais de inovação do SENAI MS.
Data de referência (hoje): {today_iso} (America/Cuiaba). Classifique status/prazos comparando com esta data.

METODOLOGIA (obrigatória):
{methodology}

REGRA CRÍTICA DE ESCOPO: a busca é ampla — qualquer área de inovação, qualquer nacionalidade, qualquer público.
Não exclua editais por parecerem fora do escopo dos institutos; a aderência é uma camada extra ao final.

INSTITUTOS-ALVO (para a seção de aderência): {_INSTITUTOS}

REGRAS:
- Use SEMPRE a fonte oficial (não agregadores/blogs).
- NÃO invente dados. Se não encontrar, escreva "Não encontrado" ou "—".
- Reavalie a base anterior: atualize status/prazos, não duplique linhas e remova itens já encerrados.
- status deve ser exatamente um de: aberto | breve | continuo.
- Para cada edital, colete: nome, fonte, status, abertura, encerramento, público-alvo, valor/faixa,
  contrapartida, principais exigências e link oficial (URL completa, começando por http).
- Produza a aderência (alta|media|baixa|none) apenas para editais abertos ou em breve.
- resumo_executivo: 3 a 4 bullets curtos. alerta_prazo: destaque prazos que encerram em ≤ 7 dias.
- NÃO inclua campos calculados (dias restantes, contagens, novidades) — serão derivados depois.

BASE ANTERIOR (para continuidade e reavaliação):
{_summarize(base)}

Responda APENAS com o JSON no schema fornecido."""
