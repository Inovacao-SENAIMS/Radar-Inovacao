#!/usr/bin/env python3
"""Gera o relatório de 28/09/2026 a partir da base de 27/09 e fontes oficiais."""

from datetime import date, datetime
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from md_to_json import parse_markdown

TODAY = date(2026, 9, 28)
OLD = ROOT / "data/Monitoramento_Editais_Inovacao_2026-09-27.md"
OUT = ROOT / "data/Monitoramento_Editais_Inovacao_2026-09-28.md"
data = parse_markdown(OLD.read_text(encoding="utf-8"))


def deadline(item):
    match = re.search(r"\d{2}/\d{2}/\d{4}", item["encerramento"])
    return datetime.strptime(match.group(), "%d/%m/%Y").date() if match else date.max


# Mantém oportunidades cujo prazo é hoje: elas só são encerradas depois do fim do dia.
active, closed = [], []
for item in data["editais"]:
    due = deadline(item)
    if due < TODAY:
        closed.append((item, f"Prazo da etapa pública encerrado em {due:%d/%m/%Y}."))
    else:
        active.append(item)


def add(name, fonte, encerramento, publico, valor, exigencias, link,
        institutos, grau, justificativa, foco="Não", contrapartida="Não encontrado",
        abertura="24/09/2026"):
    active.append({
        "edital": name, "fonte": fonte, "status": "aberto", "abertura": abertura,
        "encerramento": encerramento, "publico": publico, "valor": valor,
        "contrapartida": contrapartida, "exigencias": exigencias, "link": link,
    })
    data["aderencia"].append({
        "edital": name, "institutos": institutos, "grau": grau,
        "foco_educacional": foco, "justificativa": justificativa,
    })


add(
    "FAPESP nº 44/2026 – UNESCO-TWAS Pós-Doutorado para Pesquisadores de Países em Desenvolvimento",
    "FAPESP/TWAS", "01/11/2026",
    "Pesquisadores de países em desenvolvimento para pós-doutorado em instituições de SP",
    "Não encontrado", "Manifestação de interesse; conferir elegibilidade e documentos na chamada oficial",
    "https://fapesp.br/18365", "—", "none",
    "Bolsa de pós-doutorado em instituições de São Paulo; foco educacional e elegibilidade externa aos institutos de MS.",
    "Sim (pós-doutorado)", abertura="Não encontrado",
)
add(
    "FAPERJ nº 18/2026 – Pesquisa em Obesidade (CNE/CNPq A-B)",
    "FAPERJ/SECTI-RJ", "12/10/2026",
    "Pesquisadores CNE/FAPERJ ou CNPq A-B, vinculados a instituições no RJ; rede com no mínimo 5 pesquisadores",
    "Até R$ 1 mi/projeto; R$ 9,5 mi no edital",
    "SisFAPERJ; projeto de até 20 páginas; execução no RJ; rede com ICTs e/ou serviços SUS",
    "https://www.faperj.br/rp/downloads/Edital_FAPERJ_N%C2%BA_18_2026_%E2%80%93_Programa_de_Aux%C3%ADlio_%C3%A0_Pesquisa_em_Obesidade_Para_Pesquisadores_CNE-FAPERJ_ou_CNPq_N%C3%ADveis_A_ou_B.pdf",
    "IST Alimentos", "baixa",
    "Tecnologias diagnósticas e terapêuticas ligadas à obesidade dialogam indiretamente com capacidades laboratoriais, mas o edital é restrito ao RJ.",
)
add(
    "FAPERJ nº 19/2026 – Pesquisa em Obesidade (JCNE/CNPq C-D)",
    "FAPERJ/SECTI-RJ", "12/10/2026",
    "Pesquisadores JCNE/FAPERJ ou CNPq C-D, vinculados a instituições no RJ; rede com no mínimo 3 pesquisadores",
    "Até R$ 500 mil/projeto; R$ 9,5 mi no edital",
    "SisFAPERJ; projeto de até 20 páginas; execução no RJ; rede de pesquisadores elegíveis",
    "https://www.faperj.br/rp/downloads/EDITAL_FAPERJ_N%C2%BA_19_2026_%E2%80%93_Programa_de_Aux%C3%ADlio_%C3%A0_Pesquisa_em_Obesidade_Para_Pesquisadores_JCNE-FAPERJ_ou_CNPq_N%C3%ADveis_C_ou_D.pdf",
    "IST Alimentos", "baixa",
    "Pesquisa em obesidade pode ter interface indireta com alimentos e saúde, mas a elegibilidade e execução são restritas ao RJ.",
)
add(
    "FAPERJ nº 20/2026 – Envelhecimento com Qualidade de Vida (CNE/CNPq A-B)",
    "FAPERJ/SECTI-RJ", "12/10/2026",
    "Pesquisadores CNE/FAPERJ ou CNPq A-B, vinculados a instituições no RJ; rede com no mínimo 5 pesquisadores",
    "Até R$ 1 mi/projeto; R$ 9,5 mi no edital",
    "SisFAPERJ; projeto de até 20 páginas; execução no RJ; rede com ICTs e/ou serviços SUS",
    "https://www.faperj.br/rp/downloads/Edital_FAPERJ_N%C2%BA_20_2026_%E2%80%93_Programa_de_Apoio_ao_Envelhecimento_com_Qualidade_de_Vida_Para_Pesquisadores_CNE-FAPERJ_OU_CNPq_N%C3%ADveis_A_ou_B.pdf",
    "—", "none",
    "Pesquisa em saúde e envelhecimento, com elegibilidade e execução restritas ao RJ; não foi identificada aderência direta aos institutos.",
)
add(
    "FAPERJ nº 21/2026 – Envelhecimento com Qualidade de Vida (JCNE/CNPq C-D)",
    "FAPERJ/SECTI-RJ", "12/10/2026",
    "Pesquisadores JCNE/FAPERJ ou CNPq C-D, vinculados a instituições no RJ; rede com no mínimo 3 pesquisadores",
    "Até R$ 500 mil/projeto; R$ 9,5 mi no edital",
    "SisFAPERJ; projeto de até 20 páginas; execução no RJ; rede de pesquisadores elegíveis",
    "https://www.faperj.br/rp/downloads/Edital_FAPERJ_N%C2%BA_21_2026_%E2%80%93_Programa_de_Apoio_ao_Envelhecimento_com_Qualidade_de_Vida_Para_Pesquisadores_JCNE-FAPERJ_OU_CNPq_N%C3%ADveis_C_ou_D.pdf",
    "—", "none",
    "Pesquisa em saúde e envelhecimento, com elegibilidade e execução restritas ao RJ; não foi identificada aderência direta aos institutos.",
)


for item in active:
    item["dias"] = "—" if item["status"] == "continuo" else str((deadline(item) - TODAY).days)
active.sort(key=lambda item: (item["status"] == "continuo", deadline(item), item["edital"]))
names = {item["edital"] for item in active}
aderencia = sorted((item for item in data["aderencia"] if item["edital"] in names), key=lambda item: item["edital"])
urgent = [item for item in active if item["status"] == "aberto" and item["dias"].isdigit() and int(item["dias"]) <= 7]
count_open = sum(item["status"] == "aberto" for item in active)
count_cont = sum(item["status"] == "continuo" for item in active)
count_soon = sum(item["status"] == "breve" for item in active)
new_names = {
    "FAPESP nº 44/2026 – UNESCO-TWAS Pós-Doutorado para Pesquisadores de Países em Desenvolvimento",
    "FAPERJ nº 18/2026 – Pesquisa em Obesidade (CNE/CNPq A-B)",
    "FAPERJ nº 19/2026 – Pesquisa em Obesidade (JCNE/CNPq C-D)",
    "FAPERJ nº 20/2026 – Envelhecimento com Qualidade de Vida (CNE/CNPq A-B)",
    "FAPERJ nº 21/2026 – Envelhecimento com Qualidade de Vida (JCNE/CNPq C-D)",
}


def table(headers, rows):
    def cell(value):
        return str(value or "—").replace("|", "/").replace("\n", " ")
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "|" + "---|" * len(headers),
        *["| " + " | ".join(cell(value) for value in row) + " |" for row in rows],
    ])


status_label = {"aberto": "Aberto", "continuo": "Fluxo contínuo", "breve": "Em breve"}
grade_label = {"alta": "Alta", "media": "Média", "baixa": "Baixa", "none": "Sem aderência identificada"}
deadline_alert = "; ".join(f"{item['edital']} ({item['encerramento']})" for item in urgent)
lines = [
    "# Monitoramento de Editais de Inovação",
    "**Data de referência:** 2026-09-28 · segunda-feira — America/Cuiaba; base para classificação de status/prazos.",
    "**Escopo:** Nacional (BR), estadual (prioridade MS/Centro-Oeste) e internacional com elegibilidade do Brasil.",
    "**Metodologia:** Revisão em fontes oficiais em 28/09/2026; prazos comparados com a data local. O monitor não é inventário exaustivo; inscrições condicionadas à elegibilidade e à etapa aplicável.",
    "", "## Novidades desde a última atualização (27/09/2026)", "", "### Novos editais incorporados nesta atualização", "",
    table(["Edital", "Fonte", "Abertura", "Encerramento", "Destaque"], [[item["edital"], item["fonte"], item["abertura"], item["encerramento"], item["valor"]] for item in active if item["edital"] in new_names]),
    "", "### Editais encerrados ou retirados da lista ativa", "",
    table(["Edital", "Fonte", "Motivo do encerramento"], [[item["edital"], item["fonte"], reason] for item, reason in closed]),
    "", "### Alterações de prazo e status", "",
    table(["Edital", "Alteração"], [
        ("FAPESP PIPE Jornada Tecnológica 1ª Rodada 2026 (Fase 1)", "Prazo vence hoje (28/09); permanece aberto até o encerramento do dia."),
        ("PET Saúde Informação e Saúde Digital (Edital Conjunto SEIDIGI/SGTES-MS nº 1/2026)", "Prazo vence hoje (28/09); permanece aberto até o encerramento do dia."),
        ("FAPESP nº 44/2026 – UNESCO-TWAS Pós-Doutorado", "Incluída após conferência da lista oficial FAPESP 2026; manifestação de interesse até 01/11."),
        ("FAPERJ nº 18, 19, 20 e 21/2026", "Quatro editais de obesidade e envelhecimento lançados em 24/09, com submissões até 12/10."),
    ]),
    "", "## Resumo Executivo", "",
    f"- **Abertos agora:** {count_open} editais com etapa vigente em 28/09/2026, mais {count_cont} linhas de fluxo contínuo sem prazo definido.",
    f"- **Em breve:** {count_soon} chamadas com abertura programada.",
    f"- **Alerta (encerramento em ≤ 7 dias):** {len(urgent)} editais: {deadline_alert}.",
    f"- **Não confirmado:** {len(data['nao_confirmado'])} itens sem janela de inscrição confirmada, listados ao final.",
    "", f"> **Alerta de prazo:** {deadline_alert}.", "", "## Tabela de Editais (ordenada por encerramento mais próximo)", "",
    table(["Edital", "Fonte", "Status", "Abertura", "Encerramento", "Dias restantes", "Público-alvo", "Valor/Faixa", "Contrapartida", "Principais exigências", "Link"], [[item["edital"], item["fonte"], status_label[item["status"]], item["abertura"], item["encerramento"], item["dias"], item["publico"], item["valor"], item["contrapartida"], item["exigencias"], item["link"]] for item in active]),
    "", "## Editais \"Não confirmado\" (datas não extraídas após busca)", "",
    table(["Edital", "Fonte", "Motivo"], [[item["edital"], item["fonte"], item["motivo"]] for item in data["nao_confirmado"]]),
    "", "## Aderência com os institutos SENAI/MS", "",
    table(["Edital", "Instituto(s) com maior aderência", "Grau de aderência", "Foco educacional?", "Justificativa"], [[item["edital"], item["institutos"], grade_label[item["grau"]], item["foco_educacional"], item["justificativa"]] for item in aderencia]),
    "", "## Observações de método", "",
    "> Editais com prazo em 28/09 permanecem como abertos nesta referência; devem ser reclassificados na próxima atualização caso não haja prorrogação oficial.",
    "> A FAPESP lista a chamada UNESCO-TWAS com prazo de manifestação de interesse em 01/11; detalhes não localizados foram marcados como Não encontrado.",
    "> Os editais FAPERJ nº 18 a 21 exigem execução no Rio de Janeiro; sua aderência temática não representa elegibilidade para os institutos de MS.",
    "> Valores e contrapartidas não localizados nas fontes consultadas aparecem como Não encontrado; a aderência é avaliação temática e não garante elegibilidade institucional.",
    "",
]
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"{OUT}: {count_open} abertos, {count_cont} contínuos, {count_soon} em breve, {len(urgent)} urgentes; {len(closed)} retirados")
