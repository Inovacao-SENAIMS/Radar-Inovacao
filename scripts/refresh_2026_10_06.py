#!/usr/bin/env python3
"""Gera o relatório de 06/10/2026 a partir da base de 28/09 e fontes oficiais.

Fontes conferidas em 06/10/2026:
- FAPESP — https://fapesp.br/chamadas/
- CNPq — https://www.gov.br/cnpq/pt-br/chamadas/abertas-para-submissao
- CONFAP — https://confap.org.br/pt/editais
- FAPERJ — https://www.faperj.br/?id=28.5.7
- FINEP/MCTI — notícias de chamadas (PRONINC, Transformação Mineral, Cooperamais)
- FUNDECT-MS — https://www.fundect.ms.gov.br/informativos/consultas/
"""

from datetime import date, datetime
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from md_to_json import parse_markdown

TODAY = date(2026, 10, 6)
OLD = ROOT / "data/Monitoramento_Editais_Inovacao_2026-09-28.md"
OUT = ROOT / "data/Monitoramento_Editais_Inovacao_2026-10-06.md"
data = parse_markdown(OLD.read_text(encoding="utf-8"))


def deadline(item):
    match = re.search(r"\d{2}/\d{2}/\d{4}", item["encerramento"])
    return datetime.strptime(match.group(), "%d/%m/%Y").date() if match else date.max


# Mantém oportunidades cujo prazo é hoje ou futuro; encerra as vencidas.
active, closed = [], []
for item in data["editais"]:
    due = deadline(item)
    if due < TODAY:
        closed.append((item, f"Prazo da etapa pública encerrado em {due:%d/%m/%Y}."))
    else:
        active.append(item)

# --- Atualizações de prazo/status em itens já existentes ---
UPDATES = {
    "Sustainable Blue Economy Partnership – 4ª Call": {
        "encerramento": "Pré: 16/11/2026; completa: 14/06/2027",
    },
}
for item in active:
    if item["edital"] in UPDATES:
        item.update(UPDATES[item["edital"]])


def add(name, fonte, encerramento, publico, valor, exigencias, link,
        institutos, grau, justificativa, foco="Não", contrapartida="Não encontrado",
        abertura="Não encontrado", status="aberto"):
    active.append({
        "edital": name, "fonte": fonte, "status": status, "abertura": abertura,
        "encerramento": encerramento, "publico": publico, "valor": valor,
        "contrapartida": contrapartida, "exigencias": exigencias, "link": link,
    })
    data["aderencia"].append({
        "edital": name, "institutos": institutos, "grau": grau,
        "foco_educacional": foco, "justificativa": justificativa,
    })


# ===== Novos editais incorporados nesta atualização (06/10/2026) =====
add(
    "FAPESP PIPE Jornada Tecnológica Transição Energética – Fase 1",
    "FAPESP", "03/11/2026",
    "Pequenas empresas sediadas ou com P&D em SP",
    "Até R$ 500 mil/projeto; R$ 25 mi na chamada",
    "SAGe; pesquisador responsável sócio da empresa e residente em SP; até 250 empregados",
    "https://fapesp.br/18291",
    "IST Eficiência Operacional; ISI Biomassa", "alta",
    "Transição energética e inovação em energia alinham-se à eficiência operacional e às linhas de bioenergia do ISI Biomassa; restrição territorial a SP.",
)
add(
    "FAPESP / CONFAP / RAMP – Raw Materials for the Green and Digital Transition",
    "FAPESP/CONFAP", "15/02/2027",
    "Consórcios de pesquisa (SP + parceiros europeus da parceria RAMP)",
    "Não encontrado",
    "Proposta completa (após etapa anterior); consórcio transnacional; matérias-primas para transição verde e digital",
    "https://fapesp.br/18256",
    "IST Eficiência Operacional; ISI Biomassa", "alta",
    "Materiais e matérias-primas para transição verde e digital dialogam com descarbonização e novos materiais do ISI Biomassa e com processos industriais do IST Eficiência.",
)
add(
    "FAPESP / M-ERA.NET 2026",
    "FAPESP + M-ERA.NET", "18/11/2026",
    "Pesquisadores de ICTs/IES de SP + parceiros europeus (Ciência de Materiais e Engenharia)",
    "Não encontrado",
    "Propostas finais mediante convite; consórcio transnacional M-ERA.NET",
    "https://fapesp.br/18101",
    "IST Eficiência Operacional; ISI Biomassa", "media",
    "Ciência de materiais e engenharia podem sustentar P&D em processos industriais e biomateriais, mediante parceria elegível em SP.",
)
add(
    "Auxílio à Pesquisa Jovens Pesquisadores para Pesquisadores Internacionais",
    "FAPESP", "19/11/2026",
    "Pesquisadores internacionais (modalidade Jovem Pesquisador) vinculados a ICTs/IES de SP",
    "Não encontrado",
    "Submissão via SAGe; modalidade Jovem Pesquisador; áreas conforme chamada",
    "https://fapesp.br/18389",
    "IST Eficiência Operacional; ISI Biomassa; IST Alimentos", "media",
    "Chamada aberta a todas as áreas; pode viabilizar a fixação de pesquisadores em linhas dos institutos, com execução em SP.",
)
add(
    "FAPESP – Programa Desafios da Amazônia",
    "FAPESP", "08/12/2026",
    "Pesquisadores de ICTs/IES de SP (Sociobioeconomia)",
    "Não encontrado",
    "Propostas finais (pré-propostas enquadradas em 01/09/2026); submissão via SAGe",
    "https://fapesp.br/18249",
    "ISI Biomassa", "alta",
    "Sociobioeconomia e uso sustentável de recursos biológicos aproximam-se diretamente das linhas de bioprocessos e biomassa.",
)
add(
    "Chamada Trans-Atlantic Platform (T-AP) Preparing for Tomorrow – FAPESP 23/2026",
    "FAPESP/T-AP", "28/10/2026",
    "Pesquisadores de ICTs/IES de SP + parceiros de oito países (Ciências Humanas e Sociais)",
    "Não encontrado",
    "Proposta completa apenas para pré-propostas enquadradas (LOI até 08/07/2026); submissão SAGe e portal T-AP",
    "https://fapesp.br/18135",
    "—", "none",
    "Chamada internacional em Ciências Humanas e Sociais; não foi identificada aderência temática direta aos institutos.",
)
add(
    "FAPESP – IIDTAC (Tecnologias Disruptivas para Desafios Globais)",
    "FAPESP", "03/11/2026",
    "Pesquisadores de ICTs/IES de SP em consórcio internacional (interdisciplinar)",
    "Não encontrado",
    "Proposta completa; uso de tecnologias disruptivas para enfrentamento de desafios globais",
    "https://fapesp.br/17952",
    "IST Eficiência Operacional; ISI Biomassa", "media",
    "Tecnologias disruptivas e interdisciplinares podem dialogar com automação, digitalização e bioprocessos, mediante parceria elegível em SP.",
)
add(
    "Edital do Programa FICA-SP (Ciclo 2)",
    "FAPESP/CNPq/CAPES", "26/02/2027",
    "Pesquisadores doutores vinculados a ICTs/IES de São Paulo",
    "Até R$ 1,5 mi/proposta",
    "Submissão via SAGe; execução em SP; modalidade Projeto Geração",
    "https://fapesp.br/18238",
    "IST Alimentos; IST Eficiência Operacional; ISI Biomassa", "media",
    "Abrange linhas estratégicas de alimentos, biotecnologia, energia e transição digital, mas é restrito a ICTs/IES de São Paulo.",
)
add(
    "FAPERJ nº 27/2026 – Bolsa de Iniciação Tecnológica (IT) 2026",
    "FAPERJ/SECTI-RJ", "26/11/2026",
    "Orientadores e estudantes vinculados a instituições sediadas no RJ",
    "Bolsa IT (valor conforme tabela FAPERJ)",
    "SisFAPERJ; indicação do bolsista no ato da submissão; etapa única",
    "https://www.faperj.br/rp/downloads/Edital_FAPERJ_N%C2%BA_27_2026_%E2%80%93_Bolsa_de_Inicia%C3%A7%C3%A3o_Tecnol%C3%B3gica_(IT).pdf",
    "IST Eficiência Operacional", "baixa",
    "Bolsa de iniciação tecnológica vinculada a projeto no RJ; interface indireta com P&D aplicado dos institutos.",
    foco="Sim (bolsa de iniciação tecnológica)", abertura="26/10/2026", status="breve",
)
add(
    "FAPERJ nº 26/2026 – Bolsa de Inovação Tecnológica (INT) 2026",
    "FAPERJ/SECTI-RJ", "26/11/2026",
    "Orientadores e bolsistas vinculados a instituições sediadas no RJ",
    "Bolsa INT (valor conforme tabela FAPERJ)",
    "SisFAPERJ; indicação do bolsista no ato da submissão; foco em empreendedorismo e inovação",
    "https://www.faperj.br/rp/downloads/Edital_FAPPERJ_N%C2%BA_26_2026_%E2%80%93_Bolsa_de_Inova%C3%A7%C3%A3o_Tecnol%C3%B3gica_(INT).pdf",
    "IST Eficiência Operacional", "baixa",
    "Bolsa de inovação tecnológica restrita ao RJ; pode apoiar projetos de inovação com interface indireta aos institutos.",
    foco="Sim (bolsa de inovação tecnológica)", abertura="26/10/2026", status="breve",
)


# ===== Recomputa prazos e ordena =====
for item in active:
    item["dias"] = "—" if item["status"] == "continuo" else str((deadline(item) - TODAY).days)
active.sort(key=lambda item: (item["status"] != "aberto", item["status"] == "continuo", deadline(item), item["edital"]))

names = {item["edital"] for item in active}
aderencia = sorted((item for item in data["aderencia"] if item["edital"] in names), key=lambda item: item["edital"])
urgent = [item for item in active if item["status"] == "aberto" and item["dias"].isdigit() and int(item["dias"]) <= 7]
count_open = sum(item["status"] == "aberto" for item in active)
count_cont = sum(item["status"] == "continuo" for item in active)
count_soon = sum(item["status"] == "breve" for item in active)

new_names = {
    "FAPESP PIPE Jornada Tecnológica Transição Energética – Fase 1",
    "FAPESP / CONFAP / RAMP – Raw Materials for the Green and Digital Transition",
    "FAPESP / M-ERA.NET 2026",
    "Auxílio à Pesquisa Jovens Pesquisadores para Pesquisadores Internacionais",
    "FAPESP – Programa Desafios da Amazônia",
    "Chamada Trans-Atlantic Platform (T-AP) Preparing for Tomorrow – FAPESP 23/2026",
    "FAPESP – IIDTAC (Tecnologias Disruptivas para Desafios Globais)",
    "Edital do Programa FICA-SP (Ciclo 2)",
    "FAPERJ nº 27/2026 – Bolsa de Iniciação Tecnológica (IT) 2026",
    "FAPERJ nº 26/2026 – Bolsa de Inovação Tecnológica (INT) 2026",
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
    "**Data de referência:** 2026-10-06 · terça-feira — America/Cuiaba; base para classificação de status/prazos.",
    "**Escopo:** Nacional (BR), estadual (prioridade MS/Centro-Oeste) e internacional com elegibilidade do Brasil.",
    "**Metodologia:** Revisão em fontes oficiais em 06/10/2026 (FAPESP, CNPq, CONFAP, FAPERJ, FINEP/MCTI, FUNDECT-MS); prazos comparados com a data local. O monitor não é inventário exaustivo; inscrições condicionadas à elegibilidade e à etapa aplicável.",
    "", "## Novidades desde a última atualização (28/09/2026)", "", "### Novos editais incorporados nesta atualização", "",
    table(["Edital", "Fonte", "Abertura", "Encerramento", "Destaque"],
          [[item["edital"], item["fonte"], item["abertura"], item["encerramento"], item["valor"]] for item in active if item["edital"] in new_names]),
    "", "### Editais encerrados ou retirados da lista ativa", "",
    table(["Edital", "Fonte", "Motivo do encerramento"],
          [[item["edital"], item["fonte"], reason] for item, reason in closed]),
    "", "### Alterações de prazo e status", "",
    table(["Edital", "Alteração"], [
        ("Sustainable Blue Economy Partnership – 4ª Call",
         "Pré-proposta atualizada para 16/11/2026 conforme a página oficial de chamadas da FAPESP (antes 10/11)."),
        ("FAPERJ nº 26 e 27/2026 – Bolsas INT e IT",
         "Lançadas em 24/09/2026; submissões abrem em 26/10/2026 e seguem até 26/11/2026 — registradas como Em breve."),
        ("Finep Mais Inovação Brasil R2 – Transformação Mineral",
         "Prazo prorrogado e confirmado em 30/11/2026 pela FINEP/MCTI."),
        ("FINEP PRONINC 2026 – Tecnologias para Economia Solidária",
         "Cadastro de instituições na plataforma FINEP até 09/10/2026; propostas até 14/01/2027."),
    ]),
    "", "## Resumo Executivo", "",
    f"- **Abertos agora:** {count_open} editais com etapa vigente em 06/10/2026, mais {count_cont} linhas de fluxo contínuo sem prazo definido.",
    f"- **Em breve:** {count_soon} chamadas com abertura programada (bolsas FAPERJ INT e IT, a partir de 26/10).",
    f"- **Alerta (encerramento em ≤ 7 dias):** {len(urgent)} editais: {deadline_alert}.",
    f"- **Não confirmado:** {len(data['nao_confirmado'])} itens sem janela de inscrição confirmada, listados ao final.",
    "", f"> **Alerta de prazo:** {deadline_alert}.", "", "## Tabela de Editais (ordenada por encerramento mais próximo)", "",
    table(["Edital", "Fonte", "Status", "Abertura", "Encerramento", "Dias restantes", "Público-alvo", "Valor/Faixa", "Contrapartida", "Principais exigências", "Link"],
          [[item["edital"], item["fonte"], status_label[item["status"]], item["abertura"], item["encerramento"], item["dias"], item["publico"], item["valor"], item["contrapartida"], item["exigencias"], item["link"]] for item in active]),
    "", "## Editais \"Não confirmado\" (datas não extraídas após busca)", "",
    table(["Edital", "Fonte", "Motivo"], [[item["edital"], item["fonte"], item["motivo"]] for item in data["nao_confirmado"]]),
    "", "## Aderência com os institutos SENAI/MS", "",
    table(["Edital", "Instituto(s) com maior aderência", "Grau de aderência", "Foco educacional?", "Justificativa"],
          [[item["edital"], item["institutos"], grade_label[item["grau"]], item["foco_educacional"], item["justificativa"]] for item in aderencia]),
    "", "## Observações de método", "",
    "> Editais com prazo vencido entre 28/09 e 05/10 foram reclassificados como encerrados; devem retornar apenas se houver prorrogação oficial.",
    "> As bolsas FAPERJ nº 26 (INT) e nº 27 (IT) de 2026 têm submissão de 26/10 a 26/11/2026 e são registradas como Em breve até a abertura da janela.",
    "> Os editais FAPESP (PIPE Transição Energética, IIDTAC, M-ERA.NET, Jovens Pesquisadores, Desafios da Amazônia, RAMP) exigem vínculo com ICT/IES de São Paulo; a aderência temática não representa elegibilidade para os institutos de MS.",
    "> Valores e contrapartidas não localizados nas fontes consultadas aparecem como Não encontrado; a aderência é avaliação temática e não garante elegibilidade institucional.",
    "",
]
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"{OUT}: {count_open} abertos, {count_cont} contínuos, {count_soon} em breve, {len(urgent)} urgentes; {len(closed)} encerrados")
