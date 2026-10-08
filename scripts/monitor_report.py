#!/usr/bin/env python3
"""monitor_report.py — cálculos determinísticos e geração do .md do Radar de Editais."""
import re
from datetime import date, datetime

DATE_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


def _first_deadline(encerramento):
    m = DATE_RE.search(encerramento or "")
    return datetime.strptime(m.group(0), "%d/%m/%Y").date() if m else None


def compute_dias(item, today):
    if item.get("status") == "continuo":
        return "—"
    due = _first_deadline(item.get("encerramento", ""))
    if due is None:
        return "—"
    delta = (due - today).days
    return "0 (hoje)" if delta == 0 else str(delta)


def compute_stats(editais, today):
    stats = {"abertos": 0, "continuos": 0, "em_breve": 0, "encerram_7d": 0, "nao_confirmado": 0}
    for e in editais:
        s = e.get("status")
        if s == "aberto":
            stats["abertos"] += 1
        elif s == "continuo":
            stats["continuos"] += 1
        elif s == "breve":
            stats["em_breve"] += 1
        dias = compute_dias(e, today)
        if s == "aberto" and (dias.startswith("0") or (dias.isdigit() and int(dias) <= 7)):
            stats["encerram_7d"] += 1
    return stats


def _nkey(name):
    return (name or "").strip().lower()


def diff_novidades(previous, current):
    prev = {_nkey(e.get("edital")): e for e in previous.get("editais", [])}
    cur = {_nkey(e.get("edital")): e for e in current.get("editais", [])}
    novos, encerrados, alteracoes = [], [], []
    for k, e in cur.items():
        if k not in prev:
            novos.append({
                "Edital": e.get("edital", ""), "Fonte": e.get("fonte", ""),
                "Abertura": e.get("abertura", ""), "Encerramento": e.get("encerramento", ""),
                "Destaque": e.get("valor", ""),
            })
        else:
            old_dead = (prev[k].get("encerramento") or "").strip()
            new_dead = (e.get("encerramento") or "").strip()
            if old_dead != new_dead:
                alteracoes.append({
                    "Edital": e.get("edital", ""),
                    "Alteração": f"Prazo atualizado de {old_dead or '—'} para {new_dead or '—'}.",
                })
    for k, old in prev.items():
        if k not in cur:
            encerrados.append({
                "Edital": old.get("edital", ""), "Fonte": old.get("fonte", ""),
                "Motivo do encerramento": "Não consta na base desta atualização (prazo encerrado ou retirado).",
            })
    return {"novos_editais": novos, "editais_encerrados": encerrados, "alteracoes_prazo": alteracoes}


STATUS_LABEL = {"aberto": "Aberto", "continuo": "Fluxo contínuo", "breve": "Em breve"}
GRADE_LABEL = {"alta": "Alta", "media": "Média", "baixa": "Baixa", "none": "Sem aderência identificada"}
WEEKDAY_PT = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]


def _cell(v):
    val = v if v not in (None, "") else "—"
    return str(val).replace("|", "/").replace("\n", " ").strip()


def _table(headers, rows):
    return "\n".join(
        ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
        + ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    )


def build_markdown(data, today, previous, scope, methodology):
    editais = data.get("editais", [])
    for e in editais:
        e["dias"] = compute_dias(e, today)
    nov = diff_novidades(previous, data)
    urgent = [e for e in editais
              if e.get("status") == "aberto" and e["dias"].isdigit() and int(e["dias"]) <= 7]
    alerta = data.get("alerta_prazo") or "; ".join(f"{e['edital']} ({e['encerramento']})" for e in urgent)
    ref_fmt = f"{today.isoformat()} · {WEEKDAY_PT[today.weekday()]}"
    lines = [
        "# Monitoramento de Editais de Inovação",
        f"**Data de referência:** {ref_fmt} — America/Cuiaba; base para classificação de status/prazos.",
        f"**Escopo:** {scope}",
        f"**Metodologia:** {methodology}",
        "",
        "## Novidades desde a última atualização",
        "",
        "### Novos editais incorporados nesta atualização",
        "",
        _table(["Edital", "Fonte", "Abertura", "Encerramento", "Destaque"],
               [[x["Edital"], x["Fonte"], x["Abertura"], x["Encerramento"], x["Destaque"]]
                for x in nov["novos_editais"]]),
        "",
        "### Editais encerrados ou retirados da lista ativa",
        "",
        _table(["Edital", "Fonte", "Motivo do encerramento"],
               [[x["Edital"], x["Fonte"], x["Motivo do encerramento"]] for x in nov["editais_encerrados"]]),
        "",
        "### Alterações de prazo e status",
        "",
        _table(["Edital", "Alteração"],
               [[x["Edital"], x["Alteração"]] for x in nov["alteracoes_prazo"]]),
        "",
        "## Resumo Executivo",
        "",
        *[f"- {r}" for r in data.get("resumo_executivo", [])],
        "",
        f"> **Alerta de prazo:** {alerta}",
        "",
        "## Tabela de Editais (ordenada por encerramento mais próximo)",
        "",
        _table(["Edital", "Fonte", "Status", "Abertura", "Encerramento", "Dias restantes",
                "Público-alvo", "Valor/Faixa", "Contrapartida", "Principais exigências", "Link"],
               [[e.get("edital"), e.get("fonte"), STATUS_LABEL.get(e.get("status"), e.get("status")),
                 e.get("abertura"), e.get("encerramento"), e.get("dias"), e.get("publico"),
                 e.get("valor"), e.get("contrapartida"), e.get("exigencias"), e.get("link")]
                for e in editais]),
        "",
        '## Editais "Não confirmado" (datas não extraídas após busca)',
        "",
        _table(["Edital", "Fonte", "Motivo"],
               [[n.get("edital"), n.get("fonte"), n.get("motivo")] for n in data.get("nao_confirmado", [])]),
        "",
        "## Aderência com os institutos SENAI/MS",
        "",
        _table(["Edital", "Instituto(s) com maior aderência", "Grau de aderência", "Foco educacional?", "Justificativa"],
               [[a.get("edital"), a.get("institutos"), GRADE_LABEL.get(a.get("grau"), a.get("grau")),
                 a.get("foco_educacional"), a.get("justificativa")] for a in data.get("aderencia", [])]),
        "",
        "## Observações de método",
        "",
        "> Atualização automática (Gemini + busca web). Prazos comparados com a data de referência; "
        "itens sem data oficial em fontes consultadas aparecem como Não confirmado.",
        "",
    ]
    return "\n".join(lines)
