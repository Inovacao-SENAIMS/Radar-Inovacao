#!/usr/bin/env python3
"""Gera o relatório de 14/10/2026 a partir da base de 08/10 e de fontes oficiais.

Passo 0 (PROMPT.md): data de referência = 2026-10-14 (America/Cuiaba).

Fontes conferidas em 14/10/2026 (novas/atualizadas nesta rodada):
- FINEP/MCTI — https://www.finep.gov.br/chamadas-publicas
- CNPq — https://www.gov.br/cnpq/pt-br/chamadas/abertas-para-submissao
- CAPES — https://www.gov.br/capes/pt-br/assuntos/editais-e-resultados-capes
- FAPESP — https://fapesp.br/2185/chamadas-de-propostas-2026
- CONFAP / Horizon Europe — https://confap.org.br/pt/editais
- FAPERJ — https://www.faperj.br/?id=28.5.7
- FAPESC — https://fapesc.sc.gov.br/chamadas-abertas/
- FACEPE — https://www.facepe.br/editais/todos/?c=aberto
- FUNDECT-MS — https://www.fundect.ms.gov.br/informativos/consultas/
- Portal da Indústria / BNDES / EMBRAPII / Eureka / BID Lab
"""

from datetime import date, datetime
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from md_to_json import parse_markdown  # noqa: E402

TODAY = date(2026, 10, 14)
OLD = ROOT / "data/Monitoramento_Editais_Inovacao_2026-10-08.md"
OUT = ROOT / "data/Monitoramento_Editais_Inovacao_2026-10-14.md"
data = parse_markdown(OLD.read_text(encoding="utf-8"))


def deadline(item):
    match = re.search(r"\d{2}/\d{2}/\d{4}", item["encerramento"])
    return datetime.strptime(match.group(), "%d/%m/%Y").date() if match else date.max


# --- Atualizações de prazo/status em itens já existentes (aplicar ANTES do corte) ---
UPDATES = {
    "FAPESP PIPE Jornada Tecnológica – Indústria do Futuro (Fase 1)": {
        "encerramento": "09/12/2026",
    },
    "FAPESP PIPE Jornada Tecnológica – 7ª Chamada (Educação)": {
        "status": "aberto", "abertura": "13/10/2026", "encerramento": "12/11/2026",
    },
    "Finep COOPERAMAIS Tecnologia – ICT": {"encerramento": "08/12/2026"},
    "Finep PRONINC 2026 – Tecnologias para Economia Solidária": {
        "exigencias": "Cadastro SISGON até 17/11/2026; rede solidária e carta de anuência; agroecologia, resíduos, energia e sistemas digitais",
    },
}
for item in data["editais"]:
    if item["edital"] in UPDATES:
        item.update(UPDATES[item["edital"]])

# Mantém oportunidades cujo prazo é hoje ou futuro; encerra as vencidas.
CLOSE_REASONS = {
    "FUNDECT-MS nº 09/2026 – PAE-MS (eventos C,T&I)":
        "Submissão encerrada em 08/10/2026 (17h, hora de Brasília).",
    "Spain (CDTI) – Brazil (CONFAP) 2026–2027 Call":
        "Submissão encerrada em 08/10/2026.",
    "CNPq nº 29/2026 – RHAE IA (Pesquisadores em Empresas de IA)":
        "Prazo final venceu em 09/10/2026; item retirado da lista de chamadas abertas do CNPq.",
    "FAPERJ nº 18/2026 – Pesquisa em Obesidade (CNE/CNPq A-B)":
        "Submissão encerrada em 12/10/2026.",
    "FAPERJ nº 19/2026 – Pesquisa em Obesidade (JCNE/CNPq C-D)":
        "Submissão encerrada em 12/10/2026.",
    "FAPESP–ANR Generic Call for Proposals 2027":
        "Pré-cadastro conjunto encerrado em 13/10/2026; proposta completa segue pelo lado da ANR (2027).",
}

active, closed = [], []
for item in data["editais"]:
    due = deadline(item)
    if due < TODAY:
        reason = CLOSE_REASONS.get(item["edital"], f"Prazo da etapa pública encerrado em {due:%d/%m/%Y}.")
        closed.append((item, reason))
    else:
        active.append(item)


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


# ===== Novos editais incorporados nesta atualização (14/10/2026) =====

# --- FINEP / MCTI ---
add(
    "Finep Rede EUREKA – Resiliência a Desastres (fase nacional)",
    "FINEP/MCTI", "06/11/2026",
    "Empresas brasileiras que participaram da etapa internacional da Rede EUREKA",
    "R$ 1 mi a R$ 5 mi por projeto; R$ 7 mi na chamada",
    "Consórcio transnacional (Áustria, Bélgica/Flandres, Chile, Lituânia, Espanha, Turquia, Ucrânia); nenhum parceiro >70%; TRL 4 a 8; duração até 36 meses",
    "https://www.finep.gov.br/w/finep-abre-chamada-de-r-7-milh%C3%B5es-da-rede-eureka-para-financiar-projetos-de-resili%C3%AAncia-a-desastres",
    "IST Eficiência Operacional; ISI Biomassa", "alta",
    "Resiliência a desastres e manufatura avançada dialoga com automação/processos industriais (IST Eficiência) e novos materiais (ISI Biomassa).",
    abertura="07/10/2026", contrapartida="Contrapartida financeira proporcional ao porte",
)
add(
    "5ª Chamada Finep/RCN – Brasil-Noruega (Rede EUREKA)",
    "FINEP + Research Council of Norway", "16/12/2026",
    "ICTs e empresas brasileiras em consórcio quadripartite com a Noruega",
    "Até R$ 3 mi por projeto (Finep); até NOK 10 mi (RCN)",
    "Consórcio ICT+empresa (BR) e ICT+empresa (NO); Selo EUREKA; Consortium Agreement; temas de energia limpa e transporte marítimo verde",
    "https://www.finep.gov.br/e/chamada-publica/222684/1019381",
    "ISI Biomassa; IST Eficiência Operacional", "alta",
    "Energia limpa, petróleo offshore e transporte marítimo verde alinham-se à bioenergia (ISI Biomassa) e à eficiência de processos (IST Eficiência).",
    abertura="09/11/2026", status="breve", contrapartida="ICT até 100%; empresas cofinanciam (mín. 20%)",
)
add(
    "Finep Mais Inovação Brasil R2 – Semicondutores",
    "MCTI/FINEP/FNDCT", "25/11/2026",
    "Empresas brasileiras de todos os portes",
    "Subvenção econômica (Rodada 2 do programa Mais Inovação Brasil)",
    "Prorrogado de 30/09/2026 para 25/11/2026; risco tecnológico em semicondutores e microeletrônica",
    "https://finep.gov.br/chamadas-publicas/chamadapublica/780",
    "IST Eficiência Operacional", "media",
    "Semicondutores e microeletrônica são insumo de automação/indústria 4.0, com aderência temática ao IST Eficiência Operacional.",
)

# --- FAPESC (Santa Catarina) ---
add(
    "FAPESC/CNPq/CAPES nº 55/2026 – PROFIX-CB (Fixação de Doutores)",
    "FAPESC", "06/11/2026",
    "PPGs stricto sensu de IES/SC credenciadas",
    "Não encontrado",
    "Programa de fixação de doutores no Brasil; linhas temáticas prioritárias; processo SEI CNPq 01300.001930/2026-14",
    "https://fapesc.sc.gov.br/edital-de-chamada-publica-fapesc-cnpq-capes-n-o-55-2026-programa-de-apoio-a-fixacao-de-doutores-no-brasil-profix-cb/",
    "—", "none",
    "Fixação de doutores e fortalecimento de pós-graduação; foco de formação de RH, fora do escopo de P&D dos institutos.",
    foco="Sim (fixação de doutores)", abertura="23/09/2026",
)
add(
    "FAPESC/SED nº 54/2026 – Pesquisa e Inovação na Educação Catarinense",
    "FAPESC", "20/10/2026",
    "PPGs stricto sensu e licenciaturas de IES/SC",
    "Não encontrado",
    "Termo de Colaboração 005/2025; linhas temáticas prioritárias; retificações I, II e III",
    "https://fapesc.sc.gov.br/edital-de-chamada-publica-fapesc-sed-n-o-054-2026-programa-de-fomento-a-pesquisa-e-inovacao-para-o-desenvolvimento-da-educacao-catarinense/",
    "—", "none",
    "Fomento à pesquisa e inovação em educação; foco educacional, sem componente industrial direto.",
    foco="Sim (foco educacional)", abertura="10/09/2026",
)
add(
    "FAPESC/SSP nº 41/2026 – INOVASEG/SC (Segurança Pública)",
    "FAPESC", "15/10/2026",
    "Bolsistas qualificados para instituições de segurança pública de SC",
    "Não encontrado",
    "Pesquisa aplicada em segurança pública; retificações I e II",
    "https://fapesc.sc.gov.br/edital-de-chamada-publica-fapesc-ssp-n-o-041-2026-programa-de-inovacao-ciencia-e-tecnologia-em-seguranca-publica-de-santa-catarina-inovaseg-sc/",
    "IST Eficiência Operacional", "baixa",
    "Pesquisa aplicada e inovação em segurança pública; interface indireta com tecnologias digitais/sensores do IST Eficiência.",
    abertura="06/07/2026",
)

# --- Internacionais / Horizon Europe ---
add(
    "MSCA Doctoral Networks 2026 (Horizon Europe)",
    "Comissão Europeia / MSCA", "24/11/2026",
    "Consórcios internacionais de universidades, institutos e empresas",
    "€593 mi (orçamento global)",
    "Consórcio ≥3 entidades de 3 países (≥2 na UE/associados); Brasil participa como parceiro de país terceiro (sem financiamento UE)",
    "https://marie-sklodowska-curie-actions.ec.europa.eu/funding/msca-doctoral-networks-2026",
    "ISI Biomassa", "baixa",
    "Formação doutoral em rede internacional; pode envolver linhas dos institutos, mas é essencialmente educacional.",
    foco="Sim (formação doutoral)", abertura="28/05/2026",
)
add(
    "FutureFoodS – 3ª Chamada Transnacional (GETS)",
    "FutureFoodS (Horizon Europe)", "Pré-proposta: 11/01/2027",
    "Universidades, institutos, empresas e órgãos públicos (consórcios transnacionais)",
    "Definido por agência nacional",
    "Consórcio mínimo de 3 parceiros de 3 países; temas de cadeias alimentares confiáveis, comportamento do consumidor e processamento inovador (pós-colheita); participação brasileira a confirmar",
    "https://futurefoodspartnership.eu/funding-opportunities",
    "IST Alimentos e Bebidas", "alta",
    "Cadeias de valor alimentares, pós-colheita e processamento inovador são o núcleo do IST Alimentos e Bebidas (Dourados).",
    abertura="Novembro/2026", status="breve",
)

# --- FAPESP (acordos contínuos) ---
add(
    "FAPESP–NSF (National Science Foundation, EUA)",
    "FAPESP/NSF", "Contínuo",
    "Pesquisadores de SP em Geociências com parceiros nos EUA",
    "Auxílio à Pesquisa Regular e Temático",
    "Fluxo contínuo; projeto conjunto com pesquisador financiado pela NSF (Geociências)",
    "https://fapesp.br/17293",
    "IST Eficiência Operacional; ISI Biomassa", "media",
    "Cooperação contínua em Geociências; pode dialogar com análise de materiais e recursos naturais, mediante parceria elegível em SP.",
    status="continuo", abertura="Permanente", contrapartida="Não exige (co-financiamento pelas agências)",
)
add(
    "FAPESP–DFG (Alemanha)",
    "FAPESP/DFG", "Contínuo",
    "Pesquisadores de SP com parceiros alemães financiados pela DFG",
    "Auxílio à Pesquisa Regular e Projeto Temático",
    "Fluxo contínuo; projeto conjunto com pesquisador com auxílio DFG vigente",
    "https://fapesp.br/acordos-dfg",
    "IST Eficiência Operacional; ISI Biomassa", "media",
    "Cooperação contínua Brasil-Alemanha em todas as áreas, com potencial de P&D em processos e biomateriais.",
    status="continuo", abertura="Permanente", contrapartida="Não exige (co-financiamento pelas agências)",
)
add(
    "FAPESP–UKRI (Reino Unido)",
    "FAPESP/UKRI", "Contínuo",
    "Pesquisadores de SP com parceiros do Reino Unido",
    "Auxílio à Pesquisa Regular, Jovem Pesquisador ou Temático",
    "Fluxo contínuo; modalidade conforme o conselho de pesquisa do Reino Unido parceiro",
    "http://www.fapesp.br/10273",
    "IST Eficiência Operacional; ISI Biomassa", "media",
    "Cooperação contínua Brasil-Reino Unido; aderência depende do tema e de parceria elegível em SP.",
    status="continuo", abertura="Permanente", contrapartida="Não exige (co-financiamento pelas agências)",
)

# --- Não confirmados ---
data["nao_confirmado"] = [
    {"edital": "InovAtiva Brasil 2026 (2º semestre)", "fonte": "MCTI/Sebrae",
     "motivo": "Ciclo 2026 encerrado; site oficial suspenso (04/07 a 25/10/2026) por período eleitoral; novas janelas não confirmadas."},
    {"edital": "FACEPE nº 31/2026 – Ciência no Governo (Cientista Arretado)", "fonte": "FACEPE",
     "motivo": "Chamada publicada em 01/10/2026; prazo de submissão não localizado nas fontes consultadas."},
    {"edital": "FACEPE nº 32/2026 – Desafios.Gov", "fonte": "FACEPE",
     "motivo": "Chamada publicada em 30/09/2026; prazo de submissão não localizado nas fontes consultadas."},
    {"edital": "FACEPE nº 33/2026 – Pró-Startups Operação", "fonte": "FACEPE",
     "motivo": "Chamada publicada em 30/09/2026; prazo de submissão não localizado nas fontes consultadas."},
    {"edital": "MCTI/FINEP – Conhecimento Brasil (R$ 500 mi)", "fonte": "FINEP/MCTI",
     "motivo": "Fontes divergentes: página oficial sem informação disponível e registro de prazo encerrado em 11/09/2026."},
]


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
    "Finep Rede EUREKA – Resiliência a Desastres (fase nacional)",
    "5ª Chamada Finep/RCN – Brasil-Noruega (Rede EUREKA)",
    "Finep Mais Inovação Brasil R2 – Semicondutores",
    "FAPESC/CNPq/CAPES nº 55/2026 – PROFIX-CB (Fixação de Doutores)",
    "FAPESC/SED nº 54/2026 – Pesquisa e Inovação na Educação Catarinense",
    "FAPESC/SSP nº 41/2026 – INOVASEG/SC (Segurança Pública)",
    "MSCA Doctoral Networks 2026 (Horizon Europe)",
    "FutureFoodS – 3ª Chamada Transnacional (GETS)",
    "FAPESP–NSF (National Science Foundation, EUA)",
    "FAPESP–DFG (Alemanha)",
    "FAPESP–UKRI (Reino Unido)",
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
    "**Data de referência:** 2026-10-14 · quarta-feira — America/Cuiaba; base para classificação de status/prazos.",
    "**Escopo:** Nacional (BR), estadual (prioridade MS/Centro-Oeste) e internacional com elegibilidade do Brasil.",
    "**Metodologia:** Revisão em fontes oficiais em 14/10/2026 (FINEP/MCTI, CNPq, CAPES, FAPESP, CONFAP/Horizon Europe, FAPERJ, FAPESC, FACEPE, FUNDECT-MS e Portal da Indústria — Plataforma Inovação para a Indústria/CNI/SENAI-SESI); prazos comparados com a data local. O monitor não é inventário exaustivo; inscrições condicionadas à elegibilidade e à etapa aplicável.",
    "", "## Novidades desde a última atualização (08/10/2026)", "", "### Novos editais incorporados nesta atualização", "",
    table(["Edital", "Fonte", "Abertura", "Encerramento", "Destaque"],
          [[item["edital"], item["fonte"], item["abertura"], item["encerramento"], item["valor"]] for item in active if item["edital"] in new_names]),
    "", "### Editais encerrados ou retirados da lista ativa", "",
    table(["Edital", "Fonte", "Motivo do encerramento"],
          [[item["edital"], item["fonte"], reason] for item, reason in closed]),
    "", "### Alterações de prazo e status", "",
    table(["Edital", "Alteração"], [
        ("Finep PRONINC 2026 – Tecnologias para Economia Solidária",
         "Cadastro SISGON prorrogado de 16/10/2026 para 17/11/2026; propostas até 14/01/2027."),
        ("Finep COOPERAMAIS Tecnologia – ICT",
         "Submissão de propostas confirmada para 08/12/2026 (cadastro 01/12/2026)."),
        ("Finep Mais Inovação Brasil R2 – Semicondutores",
         "Prazo prorrogado de 30/09/2026 para 25/11/2026 e incorporado à base."),
        ("FAPESP PIPE Jornada Tecnológica – Indústria do Futuro (Fase 1)",
         "Pré-proposta encerrada em 08/10/2026; etapa vigente é a proposta completa, até 09/12/2026."),
        ("FAPESP PIPE Jornada Tecnológica – 7ª Chamada (Educação)",
         "Chamada aberta em 13/10/2026 para pré-propostas (tema Tecnologias Educacionais); prazo em 12/11/2026."),
        ("CNPq nº 33/2026 – Bolsas de Produtividade (PQ/DT/PQSr)",
         "Errata nº 1 (13/10/2026) alterou critério de julgamento do CA-DT; prazo inalterado (07/01/2027)."),
    ]),
    "", "## Resumo Executivo", "",
    f"- **Abertos agora:** {count_open} editais com etapa vigente em 14/10/2026, mais {count_cont} linhas de fluxo contínuo sem prazo definido.",
    f"- **Em breve:** {count_soon} chamadas com abertura programada.",
    f"- **Alerta (encerramento em ≤ 7 dias):** {len(urgent)} editais: {deadline_alert}.",
    f"- **Não confirmado:** {len(data['nao_confirmado'])} itens sem janela de inscrição confirmada, listados ao final.",
    "- **Novidade da rodada:** entrada da FINEP/Rede EUREKA (Resiliência a Desastres e cooperação Brasil-Noruega), da FAPESC (SC) e novos acordos contínuos FAPESP (NSF, DFG, UKRI); saída de 6 editais com prazo vencido.",
    "", f"> **Alerta de prazo:** {deadline_alert}.", "", "## Tabela de Editais (ordenada por encerramento mais próximo)", "",
    table(["Edital", "Fonte", "Status", "Abertura", "Encerramento", "Dias restantes", "Público-alvo", "Valor/Faixa", "Contrapartida", "Principais exigências", "Link"],
          [[item["edital"], item["fonte"], status_label[item["status"]], item["abertura"], item["encerramento"], item["dias"], item["publico"], item["valor"], item["contrapartida"], item["exigencias"], item["link"]] for item in active]),
    "", "## Editais \"Não confirmado\" (datas não extraídas após busca)", "",
    table(["Edital", "Fonte", "Motivo"], [[item["edital"], item["fonte"], item["motivo"]] for item in data["nao_confirmado"]]),
    "", "## Aderência com os institutos SENAI/MS", "",
    table(["Edital", "Instituto(s) com maior aderência", "Grau de aderência", "Foco educacional?", "Justificativa"],
          [[item["edital"], item["institutos"], grade_label[item["grau"]], item["foco_educacional"], item["justificativa"]] for item in aderencia]),
    "", "## Observações de método", "",
    "> Corte de 14/10/2026: saíram FUNDECT-MS PAE-MS, Spain (CDTI)–Brazil (CONFAP), CNPq RHAE IA, FAPERJ 18 e 19/2026 e FAPESP–ANR (pré-cadastro), todos com prazo vencido entre 08 e 13/10/2026.",
    "> FINEP: a chamada MCTI/FINEP Conhecimento Brasil (R$ 500 mi) consta como encerrada (prazo 11/09/2026) em parte das fontes e sem informação na página oficial — mantida como Não confirmado até verificação.",
    "> FUNDECT-MS não possui chamada com submissão aberta em 14/10/2026: o ciclo 2026 está em avaliação/execução; o PAE-MS nº 09/2026 encerrou em 08/10/2026 e o Centelha MS 3ª edição teve a Fase 2 encerrada em 31/08/2026.",
    "> Os editais FAPESP exigem vínculo com ICT/IES de São Paulo e os FAPESC/FACEPE são restritos a SC/PE; a aderência temática não representa elegibilidade para os institutos de MS.",
    "> Elegibilidade do Brasil no Eureka Eurostars Call 12 e no FutureFoodS ainda não confirmada; o BID Lab financia gestoras de fundos, sem execução de P&D pelos institutos.",
    "> Valores e contrapartidas não localizados nas fontes consultadas aparecem como Não encontrado; a aderência é avaliação temática e não garante elegibilidade institucional.",
    "",
]
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"{OUT}: {count_open} abertos, {count_cont} contínuos, {count_soon} em breve, {len(urgent)} urgentes; {len(closed)} encerrados; {len(active)} ativos")
