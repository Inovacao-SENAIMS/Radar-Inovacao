#!/usr/bin/env python3
"""Consolida a rodada de monitoramento de 05/09/2026.

Fontes oficiais rechecadas nesta rodada:
- Finep: Transformação Mineral (prorrogação para 30/11) e Brasil-Noruega.
- FAPERJ: Prioridade Indústria RJ 4.0, cronograma do Centelha 3 RJ e WBI Bélgica.
- BNDES: Prêmio BNDES Ferrovias.
- Observatório Nacional/MCTI: bolsas de Doutorado do projeto RSBR.

O script recebe a base estruturada de 01/09, atualiza os prazos em relação à
data de referência e produz o Markdown auditável que o md_to_json.py converte
em data/editais.json e data/editais.js.
"""

import json
import re
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REF = date(2026, 9, 8)
SOURCE = ROOT / "data" / "editais.json"
OUT = ROOT / "data" / "Monitoramento_Editais_Inovacao_2026-09-08.md"


def first_date(value):
    match = re.search(r"(\d{2}/\d{2}/\d{4})", str(value))
    return datetime.strptime(match.group(1), "%d/%m/%Y").date() if match else None


def days(value):
    deadline = first_date(value)
    if not deadline:
        return "—"
    return "0 (hoje)" if deadline == REF else str((deadline - REF).days)


def cell(value):
    return str(value or "—").replace("|", "/").replace("\n", " ")


def table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(cell(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def edital_row(item):
    labels = {"aberto": "Aberto", "continuo": "Fluxo contínuo", "breve": "Em breve"}
    return {
        "Edital": item["edital"], "Fonte": item["fonte"], "Status": labels[item["status"]],
        "Abertura": item["abertura"], "Encerramento": item["encerramento"],
        "Dias restantes": item["dias"], "Público-alvo": item["publico"],
        "Valor/Faixa": item["valor"], "Contrapartida": item["contrapartida"],
        "Principais exigências": item["exigencias"], "Link": item["link"],
    }


def main():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    removed = {
        "Programa Desafios da Amazônia (Amazônia+10)": "Pré-proposta encerrada em 01/09/2026; a etapa final é restrita às pré-propostas selecionadas.",
        "FAPESP PIPE Jornada Tecnológica – Transição Energética (Fase 1)": "Prazo de pré-proposta encerrado em 02/09/2026.",
        "FINEP Mais Inovação Brasil R2 – Transição Energética": "Prazo prorrogado encerrou em 02/09/2026.",
        "FAPESP – JSPS Japão 2026 (Projetos Conjuntos)": "Prazo de submissão encerrado em 03/09/2026.",
    }
    active = [item.copy() for item in source["editais"] if item["edital"] not in removed]
    # Reclassifica automaticamente a rodada para a data de referência: prazos
    # anteriores a hoje deixam de aparecer como oportunidades ativas.
    active = [item for item in active if not (item["status"] == "aberto" and first_date(item["encerramento"]) and first_date(item["encerramento"]) < REF)]

    # A Finep publicou nova prorrogação em 04/09/2026.
    for item in active:
        if item["edital"] == "FINEP Mais Inovação Brasil R2 – Transformação Mineral":
            item["encerramento"] = "30/11/2026"
            item["dias"] = days(item["encerramento"])
            item["valor"] = "R$ 215 mi (subvenção econômica)"
            item["exigencias"] = "Projetos de PD&I; risco tecnológico; cinco linhas temáticas; prazo prorrogado em 04/09"
            item["link"] = "https://faleconosco.finep.gov.br/web/guest/w/prazo-prorrogado-chamada-transforma%C3%A7%C3%A3o-mineral"

        # O cronograma oficial corrigiu o enquadramento desta fase como futura.
        if item["edital"] == "FAPERJ nº 12/2026 – Centelha 3 RJ (Fase 2)":
            item["status"] = "breve"
            item["abertura"] = "23/09/2026"
            item["encerramento"] = "22/10/2026"
            item["dias"] = "—"
            item["exigencias"] = "Fase 2 do Programa Centelha; proposta de fomento após seleção da Fase 1; constituir empresa no RJ"
            item["link"] = "https://www.faperj.br/?id=28.5.7"

    additions = [
        {
            "edital": "FAPERJ nº 15/2026 – Prioridade Indústria RJ 4.0", "fonte": "FAPERJ/SECTI-RJ",
            "status": "aberto", "abertura": "06/08/2026", "encerramento": "25/09/2026", "dias": days("25/09/2026"),
            "tipo_publico": "Empresa", "publico": "Startups e empresas industriais sediadas no RJ; parcerias com ICTs", "valor": "Até R$ 200 mil/projeto; R$ 6 mi totais",
            "contrapartida": "Financeira mínima de 5%", "exigencias": "SisFAPERJ; solução Indústria 4.0; TRL ≥ 6; documentos empresariais; projeto de até 24 meses",
            "link": "https://www.faperj.br/rp/downloads/Edital_FAPERJ_N%C2%BA15_2026_%E2%80%93_Programa_Prioridade_Ind%C3%BAstria_RJ_4.0.pdf", "grupo": None,
        },
        {
            "edital": "Prêmio BNDES Ferrovias 2026", "fonte": "BNDES", "status": "aberto", "abertura": "30/03/2026", "encerramento": "30/09/2026", "dias": days("30/09/2026"),
            "tipo_publico": "Pessoa Física", "publico": "Autores individuais ou grupos de até 4 pessoas com diploma superior", "valor": "R$ 40 mil / R$ 15 mil / R$ 10 mil para os três melhores trabalhos",
            "contrapartida": "Não exige", "exigencias": "Estudo aplicado sobre ferrovias de carga; envio eletrônico conforme edital; impedimentos institucionais previstos no regulamento",
            "link": "https://www.bndes.gov.br/wps/portal/site/home/onde-atuamos/infraestrutura/premio-bndes-ferrovias", "grupo": None,
        },
        {
            "edital": "Observatório Nacional – Bolsas de Doutorado RSBR 2026", "fonte": "Observatório Nacional/MCTI", "status": "aberto", "abertura": "02/09/2026", "encerramento": "08/09/2026", "dias": days("08/09/2026"),
            "tipo_publico": "Pessoa Física", "publico": "Doutores em Geofísica com experiência em sismologia ou instrumentação geofísica", "valor": "2 bolsas de R$ 6,5 mil/mês por 14 meses",
            "contrapartida": "Não exige", "exigencias": "Inscrição por e-mail; perfis para UFRN e UnB; requisitos técnicos descritos no edital",
            "link": "https://www.gov.br/observatorio/pt-br/assuntos/noticias/observatorio-nacional-lanca-edital-para-selecao-de-bolsistas-com-doutorado-em-projeto-da-rede-sismografica-brasileira/", "grupo": None,
        },
        {
            "edital": "FAPERJ – Chamada CONFAP–WBI Bélgica 2026", "fonte": "FAPERJ/CONFAP/WBI", "status": "aberto", "abertura": "22/06/2026", "encerramento": "30/09/2026", "dias": days("30/09/2026"),
            "tipo_publico": "Pessoa Física", "publico": "Pesquisadores doutores vinculados a instituições de ensino e pesquisa do RJ, com equipe belga", "valor": "Até 4 bolsas de mobilidade internacional por projeto; deslocamento de R$ 9 mil e seguro",
            "contrapartida": "Cooperação Brasil–Bélgica", "exigencias": "Projeto conjunto; submissão na plataforma parceira; elegibilidade estadual do RJ",
            "link": "https://confap.org.br/pt/editais/111/chamada-confap-wbi-belgica-2026", "grupo": None,
        },
    ]
    existing = {item["edital"] for item in active}
    active.extend(item for item in additions if item["edital"] not in existing)

    # Chamada nova confirmada na página oficial do CNPq.
    if not any("ANR" in item["edital"] for item in active):
        active.append({
            "edital": "CNPq/MCTI/ANR nº 32/2026 — Cooperação Brasil-França",
            "fonte": "CNPq/MCTI/ANR", "status": "aberto", "abertura": "03/09/2026",
            "encerramento": "31/03/2027", "dias": days("31/03/2027"),
            "tipo_publico": "Pessoa Física", "publico": "Grupos de pesquisa brasileiros e franceses",
            "valor": "Não encontrado", "contrapartida": "Não encontrado",
            "exigencias": "Projeto conjunto Brasil-França; regras específicas do edital e da ANR",
            "link": "https://www.gov.br/cnpq/pt-br/chamadas/abertas-para-submissao", "grupo": None,
        })
    for item in active:
        if "Water4All" in item["edital"]:
            item["status"] = "aberto"
            item["abertura"] = "08/09/2026"
            item["dias"] = days(item["encerramento"])

    # Recalcula somente editais efetivamente abertos; chamadas futuras não exibem dias restantes.
    for item in active:
        if item["status"] == "aberto" and first_date(item["encerramento"]):
            item["dias"] = days(item["encerramento"])
        if item["status"] == "continuo":
            item["dias"] = "—"
            item["grupo"] = "contínuo"

    rank = {"aberto": 0, "continuo": 1, "breve": 2}
    active.sort(key=lambda item: (rank[item["status"]], first_date(item["encerramento"]) or date.max, item["edital"]))

    previous_adh = {item["edital"]: item for item in source["aderencia"]}
    adh = []
    adh_new = {
        "FAPERJ nº 15/2026 – Prioridade Indústria RJ 4.0": ("—", "none", "Não", "Transformação digital industrial é aderente ao tema, mas o edital exige sede e execução no RJ."),
        "Prêmio BNDES Ferrovias 2026": ("IST Eficiência Operacional", "media", "Não", "Pesquisa aplicada em logística ferroviária e produtividade tem aderência indireta ao escopo de eficiência operacional."),
        "Observatório Nacional – Bolsas de Doutorado RSBR 2026": ("—", "none", "Sim (bolsa de pesquisa)", "Seleção individual em geofísica e sismologia; fora do escopo de PD&I industrial dos institutos."),
        "FAPERJ – Chamada CONFAP–WBI Bélgica 2026": ("—", "none", "Não", "Cooperação internacional relevante, mas a elegibilidade é restrita a pesquisadores vinculados ao RJ."),
    }
    for item in active:
        old = previous_adh.get(item["edital"])
        if old:
            adh.append(old.copy())
        else:
            institutos, grau, foco, justificativa = adh_new.get(
                item["edital"],
                ("Não avaliado com confiança", "none", "Não", "Chamada bilateral de pesquisa; o recorte temático específico deve ser confirmado no edital e não foi atribuído a um instituto sem evidência suficiente."),
            )
            adh.append({"edital": item["edital"], "institutos": institutos, "grau": grau, "foco_educacional": foco, "justificativa": justificativa})
    adh.sort(key=lambda item: item["edital"])

    nao_confirmado = [item for item in source["nao_confirmado"] if item["edital"] != "FAPERJ nº 15/2026 – Prioridade Indústria RJ 4.0"]
    abertos = [item for item in active if item["status"] == "aberto"]
    continuos = [item for item in active if item["status"] == "continuo"]
    breves = [item for item in active if item["status"] == "breve"]
    urgentes = [item for item in abertos if 0 <= int(item["dias"].split()[0]) <= 7]

    novas = [item for item in additions]
    encerrados = [{"Edital": name, "Fonte": next((item["fonte"] for item in source["editais"] if item["edital"] == name), "Não encontrado"), "Motivo do encerramento": reason} for name, reason in removed.items()]
    alert_text = "; ".join(f"{item['edital']} ({item['encerramento']})" for item in urgentes)

    lines = [
        "# Monitoramento de Editais de Inovação",
        "**Data de referência:** 2026-09-08 · terça-feira — base para toda classificação de status/prazos.",
        "**Escopo:** Nacional (BR), estadual (prioridade MS/Centro-Oeste) e internacional com elegibilidade do Brasil.",
        "**Metodologia:** Pesquisa e revalidação em fontes oficiais em 08/09/2026; status e prazos comparados com a data do sistema. Campos ausentes foram mantidos como Não encontrado ou —.",
        "",
        "## Novidades desde a última atualização (01/09/2026)", "",
        "### Novos editais abertos desde 01/09", "",
        table(["Edital", "Fonte", "Abertura", "Encerramento", "Destaque"], [{"Edital": item["edital"], "Fonte": item["fonte"], "Abertura": item["abertura"], "Encerramento": item["encerramento"], "Destaque": item["valor"]} for item in novas]),
        "", "### Editais encerrados desde 01/09", "",
        table(["Edital", "Fonte", "Motivo do encerramento"], encerrados),
        "", "### Alterações de prazo", "",
        table(["Edital", "Alteração"], [
            {"Edital": "FINEP Mais Inovação Brasil R2 – Transformação Mineral", "Alteração": "Finep prorrogou novamente a data-limite para 30/11/2026 em comunicado de 04/09; valor atualizado para R$ 215 mi."},
            {"Edital": "FAPERJ nº 12/2026 – Centelha 3 RJ", "Alteração": "Cronograma oficial indica Fase 2 de 23/09 a 22/10; reclassificado como Em breve."},
        ]),
        "", "## Resumo Executivo", "",
        f"- **Abertos agora:** {len(abertos)} editais com inscrições vigentes em 08/09/2026, mais {len(continuos)} linhas de fluxo contínuo.",
        f"- **Em breve:** {len(breves)} chamadas com abertura programada.",
        f"- **Alerta (encerramento em ≤ 7 dias):** {len(urgentes)} editais fecham em até 7 dias: {alert_text}.",
        f"- **Não confirmado:** {len(nao_confirmado)} itens permanecem sem cronograma oficial claro após busca aprofundada; estão listados ao final.",
        "", f"> **Alerta de prazo:** {alert_text}.", "",
        "## Tabela de Editais (ordenada por encerramento mais próximo)", "",
        table(["Edital", "Fonte", "Status", "Abertura", "Encerramento", "Dias restantes", "Público-alvo", "Valor/Faixa", "Contrapartida", "Principais exigências", "Link"], [edital_row(item) for item in active]),
        "", "## Editais \"Não confirmado\" (datas não extraídas após busca aprofundada)", "",
        table(["Edital", "Fonte", "Motivo"], [{"Edital": item["edital"], "Fonte": item["fonte"], "Motivo": item["motivo"]} for item in nao_confirmado]),
        "", "## Aderência com os institutos SENAI/MS", "",
        table(["Edital", "Instituto(s) com maior aderência", "Grau de aderência", "Foco educacional?", "Justificativa"], [{"Edital": item["edital"], "Instituto(s) com maior aderência": item["institutos"], "Grau de aderência": {"alta": "Alta", "media": "Média", "baixa": "Baixa", "none": "Sem aderência identificada"}[item["grau"]], "Foco educacional?": item["foco_educacional"], "Justificativa": item["justificativa"]} for item in adh]),
        "", "## Observações de método", "",
        "> A busca mantém escopo amplo; a aderência é uma camada de sinalização e não exclui editais da tabela principal.",
        "> Fontes oficiais consultadas nesta rodada: Finep, FAPERJ, BNDES, CNPq/MCTI, FAPESP e Horizon Europe/CONFAP. Prazos foram reclassificados pela data de referência de 08/09/2026.",
        "> O prazo de cadastro prévio da chamada Brasil–Noruega foi 02/09; a submissão internacional segue até 09/09. Confirme a elegibilidade cadastral antes de submeter.",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Gerado: {OUT}")
    print(f"Abertos: {len(abertos)} | Contínuos: {len(continuos)} | Em breve: {len(breves)} | Urgentes: {len(urgentes)} | Não confirmado: {len(nao_confirmado)}")


if __name__ == "__main__":
    main()
