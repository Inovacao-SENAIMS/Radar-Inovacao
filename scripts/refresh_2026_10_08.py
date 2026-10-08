#!/usr/bin/env python3
"""Gera o relatório de 08/10/2026 a partir da base de 06/10 e de fontes oficiais.

Passo 0 (PROMPT.md): data de referência = 2026-10-08 (America/Cuiaba).

Fontes conferidas em 08/10/2026 (novas/atualizadas nesta rodada):
- Portal da Indústria — Plataforma Inovação para a Indústria
  https://www.portaldaindustria.com.br/canais/plataforma-inovacao-para-industria/
  (fonte que faltava na metodologia das rodadas anteriores)
- FAPESP — https://fapesp.br/chamadas/
- CNPq — https://www.gov.br/cnpq/pt-br/chamadas/abertas-para-submissao
- CONFAP — https://confap.org.br/pt/editais
- FAPERJ — https://www.faperj.br/?id=28.5.7
- FINEP/MCTI, BNDES, EMBRAPII, FUNDECT-MS
- Internacionais: Horizon Europe (MSCA), Eureka/Eurostars, BID Lab
"""

from datetime import date, datetime
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from md_to_json import parse_markdown  # noqa: E402

TODAY = date(2026, 10, 8)
OLD = ROOT / "data/Monitoramento_Editais_Inovacao_2026-10-06.md"
OUT = ROOT / "data/Monitoramento_Editais_Inovacao_2026-10-08.md"
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
    "FAPERJ nº 20/2026 – Envelhecimento com Qualidade de Vida (CNE/CNPq A-B)": {
        "encerramento": "19/10/2026",
    },
    "FAPERJ nº 21/2026 – Envelhecimento com Qualidade de Vida (JCNE/CNPq C-D)": {
        "encerramento": "19/10/2026",
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


# ===== Novos editais incorporados nesta atualização (08/10/2026) =====

# --- Portal da Indústria / Plataforma Inovação para a Indústria (fonte antes ausente) ---
add(
    "Chamada Smart Factory – Brasil Mais Produtivo (SENAI/FINEP, 11ª edição)",
    "SENAI/FINEP (Plataforma Inovação)", "1ª janela: 16/10/2026 (até 4 janelas até mar/2027)",
    "MPMEs industriais + fornecedores de tecnologia, com Instituto SENAI coordenador",
    "R$ 47,5 mi não reembolsáveis; até 70% por projeto",
    "Submissão na Plataforma; cliente-piloto MPME; ISI/IST coordenador; TRL e mérito",
    "https://www.portaldaindustria.com.br/canais/plataforma-inovacao-para-industria/categoria/smart-factory-finep-senai/",
    "IST Eficiência Operacional; ISI Biomassa", "alta",
    "Indústria 4.0, automação e digitalização de processos alinham-se ao IST Eficiência; bioprocessos digitais ao ISI Biomassa.",
    abertura="30/09/2026",
)
add(
    "Aliança Industrial (SENAI)",
    "SENAI (Plataforma Inovação)", "Contínuo",
    "Grupos de empresas industriais de todos os portes + startups",
    "R$ 2 mi por fase complementar",
    "Empresa proponente + Instituto SENAI de Inovação/Tecnologia coordenador; submissão em qualquer período",
    "https://www.portaldaindustria.com.br/canais/plataforma-inovacao-para-industria/categoria/alianca-industrial/",
    "IST Eficiência Operacional; ISI Biomassa; IST Alimentos", "media",
    "PD&I industrial em aliança adere aos institutos conforme o tema; avaliação depende do objeto proposto.",
    status="continuo", abertura="Permanente", contrapartida="Contrapartida ≥ valor da Plataforma; financeira ≥ 60%",
)
add(
    "Habitats de Inovação (SENAI)",
    "SENAI (Plataforma Inovação)", "Contínuo",
    "Indústrias + Institutos SENAI de Inovação/Tecnologia",
    "Conforme chamada regional",
    "Uso de infraestrutura e corpo técnico dos Institutos; contato com interlocutor regional (MS: SENAI MS)",
    "https://www.portaldaindustria.com.br/canais/plataforma-inovacao-para-industria/categoria/habitats-de-inovacao/",
    "IST Eficiência Operacional; ISI Biomassa; IST Alimentos", "media",
    "Acesso à infraestrutura dos Institutos para PD&I; aderência depende do habitat/tema.",
    status="continuo", abertura="Permanente", contrapartida="Definida por chamada regional",
)
add(
    "Chamada Regional (SENAI) – SENAI/RJ Inovação em Eficiência Energética (Chamada 3)",
    "SENAI/RJ (Plataforma Inovação)", "Não encontrado",
    "Empresas industriais; arranjo coordenado pelo Departamento Regional",
    "Não encontrado",
    "Proposta via Plataforma; seleção pelo SENAI DN; cronograma no site do Lab Procel",
    "https://www.portaldaindustria.com.br/canais/plataforma-inovacao-para-industria/categoria/chamada-regional-senai/",
    "IST Eficiência Operacional", "alta",
    "Eficiência energética industrial é o núcleo do IST Eficiência Operacional; restrição territorial ao RJ.",
    abertura="11/02/2026",
)

# --- FAPESP (confirmado em fapesp.br/chamadas) ---
add(
    "FAPESP PIPE Jornada Tecnológica – 7ª Chamada (Educação)",
    "FAPESP", "Não encontrado",
    "Pequenas empresas de SP (perfil PIPE)",
    "Não encontrado",
    "SAGe; programa PIPE Jornada Tecnológica (tema Educação)",
    "https://fapesp.br/chamadas/",
    "—", "none",
    "Chamada PIPE com foco educacional; aderência institucional de P&D não identificada.",
    foco="Sim (foco educacional)", abertura="13/10/2026", status="breve",
)
add(
    "FAPESP PIPE Jornada Tecnológica – 8ª Chamada (Geral)",
    "FAPESP", "Não encontrado",
    "Pequenas empresas de SP (perfil PIPE)",
    "Não encontrado",
    "SAGe; programa PIPE Jornada Tecnológica (tema geral)",
    "https://fapesp.br/chamadas/",
    "IST Eficiência Operacional; ISI Biomassa", "media",
    "Tema geral do PIPE pode comportar P&D industrial/bioenergia, com restrição territorial a SP.",
    abertura="16/11/2026", status="breve",
)
add(
    "FAPESP – Aperfeiçoamento de especialistas em museus e acervos (PAIP)",
    "FAPESP", "06/11/2026",
    "Especialistas e ICTs de SP (infraestrutura de pesquisa)",
    "Não encontrado",
    "Chamada PAIP; vinculada a instituições de SP",
    "https://fapesp.br/18387",
    "—", "none",
    "Foco em infraestrutura de pesquisa e acervos; sem aderência industrial direta.",
)
add(
    "FAPESP – BEPE Mestrado (Estágio de Pesquisa no Exterior)",
    "FAPESP", "11/12/2026",
    "Mestrandos com auxílio FAPESP vigente",
    "Bolsa BEPE",
    "Vínculo a projeto FAPESP; estágio no exterior",
    "https://fapesp.br/18417",
    "—", "baixa",
    "Mobilidade/formação; interface indireta com P&D dos institutos.",
    foco="Sim (bolsa de formação)",
)
add(
    "FAPESP – BEPE Iniciação Científica (Estágio de Pesquisa no Exterior)",
    "FAPESP", "11/12/2026",
    "Bolsistas de IC com auxílio FAPESP vigente",
    "Bolsa BEPE",
    "Vínculo a projeto FAPESP; estágio no exterior",
    "https://fapesp.br/18416",
    "—", "baixa",
    "Mobilidade/formação; interface indireta com P&D dos institutos.",
    foco="Sim (bolsa de formação)",
)
add(
    "FAPESP-BBSRC Pump-Priming Award (FAPPA)",
    "FAPESP/UKRI", "Contínuo",
    "Pesquisadores de SP + parceiros do Reino Unido",
    "Não encontrado",
    "Fluxo contínuo; prioridade a segurança alimentar, bioenergia e biotecnologia industrial",
    "http://www.fapesp.br/11999",
    "ISI Biomassa; IST Alimentos", "alta",
    "Segurança alimentar, bioenergia e biotecnologia industrial são linhas diretas do ISI Biomassa e do IST Alimentos.",
    status="continuo", abertura="Permanente", contrapartida="Cofinanciamento pelas agências",
)
add(
    "Chamada FAPESP/CONFAP/Horizon Europe",
    "FAPESP/CONFAP", "Contínuo",
    "Pesquisadores de SP em projetos com parceiros europeus",
    "Não encontrado",
    "Fluxo contínuo; auxílios Regular, Temático ou Jovem Pesquisador",
    "https://fapesp.br/16466",
    "IST Eficiência Operacional; ISI Biomassa", "media",
    "Porta de entrada contínua para P&D com parceiros europeus em temas alinhados aos institutos.",
    status="continuo", abertura="Permanente", contrapartida="Cofinanciamento pelas agências",
)

# --- CNPq / CAPES ---
add(
    "CNPq nº 33/2026 – Bolsas de Produtividade (PQ/DT/PQSr)",
    "CNPq", "07/01/2027",
    "Pesquisadores doutores",
    "Bolsa de produtividade",
    "Plataforma Carlos Chagas; produção científica/tecnológica (inclui DT – Desenvolvimento Tecnológico)",
    "https://www.gov.br/cnpq/pt-br/chamadas/todas-as-chamadas/chamadas-2026/chamada-no-33-2026/chamada-publica-cnpq-N-33-2026",
    "IST Eficiência Operacional; IST Alimentos; ISI Biomassa", "media",
    "A modalidade DT valoriza inovação e pode credenciar pesquisadores vinculados aos institutos.",
    abertura="07/10/2026",
)
add(
    "CAPES nº 23/2026 – Programa de Apoio à Pós-Graduação Indígena (PDAI)",
    "CAPES", "26/10/2026",
    "Candidatos indígenas à pós-graduação",
    "Bolsas CAPES",
    "Inscrição no sistema CAPES; cronograma prorrogado",
    "https://www.gov.br/capes/pt-br",
    "—", "none",
    "Formação acadêmica, sem componente de inovação industrial.",
    foco="Sim (foco educacional)", abertura="02/10/2026",
)

# --- Internacionais ---
add(
    "MSCA Staff Exchanges 2027 (Horizon Europe)",
    "Horizon Europe/CONFAP", "Abril/2027 (a confirmar)",
    "Consórcios internacionais (universidades, ICTs, empresas/PMEs)",
    "~€97,9 mi (orçamento UE)",
    "Consórcio ≥3 entidades de 3 países (≥2 UE); cofinanciamento via FAP estadual",
    "https://marie-sklodowska-curie-actions.ec.europa.eu/funding/msca-staff-exchanges",
    "ISI Biomassa", "alta",
    "Intercâmbio de pessoal de PD&I pode fortalecer linhas de bioprocessos/biomassa, com aporte da FAP estadual.",
    abertura="15/12/2026", status="breve", contrapartida="Aporte via FAP estadual",
)
add(
    "Eureka Eurostars – Call 12 for projects",
    "Eureka/Horizon Europe", "04/03/2027",
    "PMEs inovadoras líderes de consórcio + parceiros",
    "Conforme regra nacional de cada parceiro",
    "Consórcio liderado por PME; ≥2 entidades de 2 países; elegibilidade do Brasil a confirmar",
    "https://www.eurekanetwork.org/programmes-and-calls/eurostars/eurostars-call-12-for-projects-deadline-march-2027",
    "IST Eficiência Operacional; ISI Biomassa", "media",
    "PD&I colaborativa orientada ao mercado; aderência depende de confirmar a elegibilidade brasileira no Eurostars.",
    abertura="17/12/2026", status="breve", contrapartida="Cofinanciamento por agência nacional",
)
add(
    "BID Lab – Convocatória para Fundos de Capital Empreendedor",
    "BID Lab", "31/10/2026",
    "Gestoras de fundos de capital empreendedor (ALC)",
    "Não encontrado",
    "Formulário online; alinhamento à tese de investimento do BID Lab",
    "https://www.iadb.org/es/inicio/convocatorias/fondos-de-capital-emprendedor",
    "—", "none",
    "Instrumento voltado a gestores de fundos de venture capital, sem execução de P&D pelos institutos.",
    status="continuo", abertura="Contínua",
)


# ===== Recomputa prazos e ordena =====
for item in active:
    due = deadline(item)
    if item["status"] == "continuo" or due == date.max:
        item["dias"] = "—"
    else:
        item["dias"] = str((due - TODAY).days)
active.sort(key=lambda item: (item["status"] != "aberto", item["status"] == "continuo", deadline(item), item["edital"]))

names = {item["edital"] for item in active}
aderencia = sorted((item for item in data["aderencia"] if item["edital"] in names), key=lambda item: item["edital"])
urgent = [item for item in active if item["status"] == "aberto" and item["dias"].isdigit() and int(item["dias"]) <= 7]
count_open = sum(item["status"] == "aberto" for item in active)
count_cont = sum(item["status"] == "continuo" for item in active)
count_soon = sum(item["status"] == "breve" for item in active)

new_names = {
    "Chamada Smart Factory – Brasil Mais Produtivo (SENAI/FINEP, 11ª edição)",
    "Aliança Industrial (SENAI)",
    "Habitats de Inovação (SENAI)",
    "Chamada Regional (SENAI) – SENAI/RJ Inovação em Eficiência Energética (Chamada 3)",
    "FAPESP PIPE Jornada Tecnológica – 7ª Chamada (Educação)",
    "FAPESP PIPE Jornada Tecnológica – 8ª Chamada (Geral)",
    "FAPESP – Aperfeiçoamento de especialistas em museus e acervos (PAIP)",
    "FAPESP – BEPE Mestrado (Estágio de Pesquisa no Exterior)",
    "FAPESP – BEPE Iniciação Científica (Estágio de Pesquisa no Exterior)",
    "FAPESP-BBSRC Pump-Priming Award (FAPPA)",
    "Chamada FAPESP/CONFAP/Horizon Europe",
    "CNPq nº 33/2026 – Bolsas de Produtividade (PQ/DT/PQSr)",
    "CAPES nº 23/2026 – Programa de Apoio à Pós-Graduação Indígena (PDAI)",
    "MSCA Staff Exchanges 2027 (Horizon Europe)",
    "Eureka Eurostars – Call 12 for projects",
    "BID Lab – Convocatória para Fundos de Capital Empreendedor",
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
    "**Data de referência:** 2026-10-08 · quinta-feira — America/Cuiaba; base para classificação de status/prazos.",
    "**Escopo:** Nacional (BR), estadual (prioridade MS/Centro-Oeste) e internacional com elegibilidade do Brasil.",
    "**Metodologia:** Revisão em fontes oficiais em 08/10/2026 (FAPESP, CNPq, CONFAP, FAPERJ, FINEP/MCTI, FUNDECT-MS e Portal da Indústria — Plataforma Inovação para a Indústria/CNI/SENAI-SESI); prazos comparados com a data local. O monitor não é inventário exaustivo; inscrições condicionadas à elegibilidade e à etapa aplicável.",
    "", "## Novidades desde a última atualização (06/10/2026)", "", "### Novos editais incorporados nesta atualização", "",
    table(["Edital", "Fonte", "Abertura", "Encerramento", "Destaque"],
          [[item["edital"], item["fonte"], item["abertura"], item["encerramento"], item["valor"]] for item in active if item["edital"] in new_names]),
    "", "### Editais encerrados ou retirados da lista ativa", "",
    table(["Edital", "Fonte", "Motivo do encerramento"],
          [[item["edital"], item["fonte"], reason] for item, reason in closed]),
    "", "### Alterações de prazo e status", "",
    table(["Edital", "Alteração"], [
        ("FAPERJ nº 20 e 21/2026 – Envelhecimento com Qualidade de Vida",
         "Prazo prorrogado de 12/10/2026 para 19/10/2026 (lista oficial FAPERJ)."),
        ("FAPESP SPRINT 2026",
         "Confirmadas 2 edições: Edição 1 em 26/10/2026 e Edição 2 em 22/02/2027."),
        ("Finep PRONINC 2026 – Tecnologias para Economia Solidária",
         "Cadastro de instituições na plataforma FINEP até 09/10/2026; propostas até 14/01/2027."),
        ("Portal da Indústria – Plataforma Inovação para a Indústria",
         "Fonte incorporada à metodologia desta rodada (antes ausente). Chamadas Smart Factory (FINEP/SENAI), Aliança Industrial, Habitats de Inovação e Chamada Regional (SENAI/RJ) incluídas."),
    ]),
    "", "## Resumo Executivo", "",
    f"- **Abertos agora:** {count_open} editais com etapa vigente em 08/10/2026, mais {count_cont} linhas de fluxo contínuo sem prazo definido.",
    f"- **Em breve:** {count_soon} chamadas com abertura programada.",
    f"- **Alerta (encerramento em ≤ 7 dias):** {len(urgent)} editais: {deadline_alert}.",
    f"- **Não confirmado:** {len(data['nao_confirmado'])} itens sem janela de inscrição confirmada, listados ao final.",
    f"- **Novidade de fonte:** o Portal da Indústria (Plataforma Inovação para a Indústria) passou a ser fonte ativa desta rodada.",
    "", f"> **Alerta de prazo:** {deadline_alert}.", "", "## Tabela de Editais (ordenada por encerramento mais próximo)", "",
    table(["Edital", "Fonte", "Status", "Abertura", "Encerramento", "Dias restantes", "Público-alvo", "Valor/Faixa", "Contrapartida", "Principais exigências", "Link"],
          [[item["edital"], item["fonte"], status_label[item["status"]], item["abertura"], item["encerramento"], item["dias"], item["publico"], item["valor"], item["contrapartida"], item["exigencias"], item["link"]] for item in active]),
    "", "## Editais \"Não confirmado\" (datas não extraídas após busca)", "",
    table(["Edital", "Fonte", "Motivo"], [[item["edital"], item["fonte"], item["motivo"]] for item in data["nao_confirmado"]]),
    "", "## Aderência com os institutos SENAI/MS", "",
    table(["Edital", "Instituto(s) com maior aderência", "Grau de aderência", "Foco educacional?", "Justificativa"],
          [[item["edital"], item["institutos"], grade_label[item["grau"]], item["foco_educacional"], item["justificativa"]] for item in aderencia]),
    "", "## Observações de método", "",
    "> O Portal da Indústria (Plataforma Inovação para a Indústria) passou a integrar as fontes desta rodada; as chamadas da cadeia automotiva (MOVER, Rota 2030, Smart Factory BNDES) foram avaliadas e a maioria já encerrou o ciclo 2026.",
    "> A linha Smart Factory FINEP/SENAI está com a 1ª janela em 16/10/2026; a página de cronograma da categoria não carregou em 08/10 — data confirmada por comunicado oficial do SENAI/CNI de 01/10/2026.",
    "> Os editais FAPESP (PIPE, PRONEX, M-ERA.NET, Jovens Pesquisadores, Desafios da Amazônia, RAMP) exigem vínculo com ICT/IES de São Paulo; a aderência temática não representa elegibilidade para os institutos de MS.",
    "> A elegibilidade do Brasil no Eurostars Call 12 deve ser confirmada antes do uso; o BID Lab financia gestoras de fundos, sem execução de P&D pelos institutos.",
    "> Valores e contrapartidas não localizados nas fontes consultadas aparecem como Não encontrado; a aderência é avaliação temática e não garante elegibilidade institucional.",
    "",
]
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"{OUT}: {count_open} abertos, {count_cont} contínuos, {count_soon} em breve, {len(urgent)} urgentes; {len(closed)} encerrados")
