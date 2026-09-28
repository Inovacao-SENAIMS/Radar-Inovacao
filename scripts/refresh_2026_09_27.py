#!/usr/bin/env python3
"""Gera o relatório de 27/09/2026 a partir da base anterior e da checagem oficial.

As alterações editoriais e as fontes oficiais estão registradas abaixo. O arquivo
anterior é preservado; md_to_json.py converte o novo relatório para o site.
"""

from datetime import date, datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from md_to_json import parse_markdown

TODAY = date(2026, 9, 27)
OLD = ROOT / "data/Monitoramento_Editais_Inovacao_2026-09-08.md"
OUT = ROOT / "data/Monitoramento_Editais_Inovacao_2026-09-27.md"
old = parse_markdown(OLD.read_text(encoding="utf-8"))

closed = []
active = []
for item in old["editais"]:
    # O prazo de uma etapa posterior não reabre inscrições públicas já encerradas.
    deadline = item["encerramento"].split(";")[0].replace("Pré:", "").strip()
    try:
        due = datetime.strptime(deadline, "%d/%m/%Y").date()
    except ValueError:
        due = None
    if due and due < TODAY:
        closed.append((item, f"Prazo da etapa pública encerrado em {due:%d/%m/%Y}."))
    elif item["edital"].startswith("FINEP – Desafios Tecnológicos"):
        closed.append((item, "Prazo oficial encerrado em 13/03/2026; não era fluxo contínuo."))
    elif item["edital"].startswith("Ministério da Saúde – Inovação"):
        closed.append((item, "Envio de documentação encerrado em 27/02/2026; resultado final em abril."))
    elif item["edital"].startswith("Tecnova 2026/2027"):
        closed.append((item, "Anúncio nacional sem janela única de inscrição; consultar editais estaduais."))
    else:
        active.append(item)

by_name = {item["edital"]: item for item in active}

def change(needle, **fields):
    item = next(x for x in active if needle in x["edital"])
    item.update(fields)
    return item

change("CONFAP–WBI", edital="CONFAP–WBI Bélgica 2026", fonte="CONFAP/WBI", encerramento="30/10/2026",
       publico="Pesquisadores doutores em ICTs/IES de FAPs participantes + equipe da Bélgica",
       link="https://confap.org.br/pt/editais/111/chamada-confap-wbi-belgica-2026")
next(a for a in old["aderencia"] if "CONFAP–WBI" in a["edital"])["edital"] = "CONFAP–WBI Bélgica 2026"
change("Centelha 3 RJ", status="aberto",
       exigencias="Fase 2: somente propostas selecionadas na Fase 1; constituir empresa no RJ")
change("Sustainable Blue Economy", status="aberto", abertura="14/09/2026",
       encerramento="Pré: 10/11/2026; completa: 14/06/2027",
       link="https://confap.org.br/pt/editais/118/4-chamada-transnacional-conjunta-da-parceria-de-economia-azul-sustentavel-")
change("Biodiversa+", status="aberto", abertura="09/09/2026",
       encerramento="Pré: 10/11/2026; completa: 16/04/2027",
       link="https://confap.org.br/pt/editais/117/chamada-transnacional-conjunta-biodiversa-biodivfuture-2026-2027")
change("Spain (CDTI)", link="https://confap.org.br/pt/editais/114/chamada-confap-cdti-2026-2027")
change("FAPESP PIPE Jornada Tecnológica 1ª", exigencias="Somente pré-propostas enquadradas até 29/07; proposta completa no SAGe")
change("FINEP Mais Inovação Brasil R2 – Semicondutores", valor="R$ 100 mi na chamada",
       link="https://faleconosco.finep.gov.br/web/guest/w/finep-recebe-propostas-para-inova%C3%A7%C3%A3o-em-semicondutores-at%C3%A9-30/9")
change("FINEP Mais Inovação Brasil R2 – Tecnologias Digitais",
       link="https://www.finep.gov.br/chamadas-publicas/chamadapublica/779")
change("Water4All", encerramento="Pré: 10/11/2026; completa: 06/04/2027",
       link="https://confap.org.br/pt/editais/116/chamada-transnacional-conjunta-2026-gestao-sustentavel-dos-recursos-hidricos")
old["aderencia"].append(dict(
    edital="FINEP Mais Inovação Brasil R2 – Transformação Mineral",
    institutos="IST Eficiência Operacional; ISI Biomassa", grau="alta",
    foco_educacional="Não",
    justificativa="Descarbonização e tecnologias industriais para a cadeia mineral aderem às linhas de eficiência operacional e biomassa."))

def add(name, fonte, abertura, encerramento, publico, valor, contrapartida,
        exigencias, link, institutos, grau, justificativa, foco="Não"):
    active.append(dict(edital=name, fonte=fonte, status="aberto", abertura=abertura,
                       encerramento=encerramento, publico=publico, valor=valor,
                       contrapartida=contrapartida, exigencias=exigencias, link=link))
    old["aderencia"].append(dict(edital=name, institutos=institutos, grau=grau,
                                  foco_educacional=foco, justificativa=justificativa))

add("FAPESP nº 42/2026 – Auxílio à Inovação Regular / Iniciação Tecnológica", "FAPESP",
    "Não encontrado", "05/10/2026", "Docentes/pesquisadores vinculados às FATECs SP",
    "Até R$ 50 mil de custeio + até 2 bolsas IT", "Não encontrado",
    "Projeto de inovação tecnológica no SAGe; estudantes regularmente matriculados nas FATECs",
    "https://fapesp.br/18364/chamada-de-propostas-422026-auxilio-a-inovacao-regular-iniciacao-tecnologica",
    "IST Eficiência Operacional; ISI Biomassa; IST Alimentos", "media",
    "Temas abertos permitem P&D aplicado, mas proponente deve estar vinculado às FATECs de SP.", "Sim, com P&D")
add("FAPESP PIPE Jornada Tecnológica – Indústria do Futuro (Fase 1)", "FAPESP",
    "08/09/2026", "Pré: 08/10/2026; completa: 09/12/2026", "Pequenas empresas sediadas ou com P&D em SP",
    "Até R$ 500 mil/projeto; R$ 25 mi na chamada", "Não encontrado",
    "SAGe; pesquisador responsável sócio da empresa e residente em SP; até 250 empregados",
    "https://fapesp.br/18349", "IST Eficiência Operacional", "alta",
    "Pesquisa industrial e tecnologias da indústria do futuro são alinhadas à eficiência operacional; restrição territorial a SP.")
add("FAPESP–ANR Generic Call for Proposals 2027", "FAPESP/ANR",
    "15/09/2026", "Pré-cadastro: 13/10/2026", "Pesquisadores de ICTs/IES em SP + parceiros franceses",
    "Não encontrado", "Cofinanciamento pelas agências; percentual não encontrado",
    "Pré-cadastro conjunto no SAGe e ANR; seis blocos temáticos; proposta completa em 2027",
    "https://fapesp.br/18378", "IST Eficiência Operacional; ISI Biomassa; IST Alimentos", "media",
    "Engenharia, materiais, recursos biológicos e saúde podem comportar P&D dos institutos, mediante parceria elegível em SP.")
add("FAPESP SPRINT 2026 (1ª edição)", "FAPESP",
    "Não encontrado", "26/10/2026", "Pesquisadores responsáveis por auxílios FAPESP vigentes e parceiros internacionais",
    "Não encontrado", "Não encontrado",
    "Mobilidade de pesquisadores; elegibilidade vinculada a auxílio FAPESP vigente; submissão SAGe",
    "https://fapesp.br/18408/fapesp-anuncia-chamada-sprint-em-2026",
    "IST Eficiência Operacional; ISI Biomassa; IST Alimentos", "baixa",
    "Mobilidade pode apoiar cooperação em P&D, mas depende de auxílio FAPESP vigente.")
add("Finep PRONINC 2026 – Tecnologias para Economia Solidária", "MCTI/FINEP/FNDCT",
    "09/09/2026", "14/01/2027", "ICTs públicas ou privadas sem fins lucrativos com ITCP e NIT",
    "R$ 2–5 mi/projeto; R$ 100 mi totais", "Isenta para ICT federal/privada sem fins lucrativos; estadual/municipal conforme LDO",
    "Cadastro SISGON até 09/10/2026; rede solidária e carta de anuência; agroecologia, resíduos, energia e sistemas digitais",
    "https://www.finep.gov.br/en/e/chamada-publica/222684/1057230",
    "IST Alimentos; ISI Biomassa; IST Eficiência Operacional", "alta",
    "Soluções tecnológicas em alimentos, resíduos e energia aderem aos institutos; exige atuação conjunta de ITCP e NIT.")
add("Finep COOPERAMAIS Tecnologia – ICT", "MCTI/FINEP/FNDCT",
    "22/09/2026", "01/12/2026", "ICTs públicas ou privadas sem fins lucrativos + cooperativa da agricultura familiar",
    "R$ 3–15 mi/projeto; R$ 100 mi na chamada", "Financeira; percentual não encontrado",
    "TRL inicial ≥ 3; cooperativa com CAF e 70% de cooperados com CAF PF; parceria prévia de 1 ano",
    "https://www.finep.gov.br/en/e/chamada-publica/222684/1060260",
    "IST Alimentos; ISI Biomassa; IST Eficiência Operacional", "alta",
    "Processamento agroindustrial, resíduos e eficiência energética se alinham às capacidades dos institutos.")
add("Finep COOPERAMAIS Brasil Tecnologias – Empresas", "MCTI/FINEP/FNDCT",
    "22/09/2026", "30/04/2027", "Empresas de qualquer porte + cooperativas da agricultura familiar",
    "R$ 5–20 mi/projeto; R$ 120 mi na chamada", "Financeira conforme porte; percentual não encontrado",
    "Fluxo contínuo até 30/04/2027; cooperativa CAF com ≥70% de agricultores familiares; máquinas e processamento",
    "https://www.finep.gov.br/en/e/chamada-publica/222684/1060720",
    "IST Alimentos; IST Eficiência Operacional; ISI Biomassa", "alta",
    "Máquinas e processamento para agricultura familiar podem envolver desenvolvimento industrial dos institutos.")
add("FOREST 2026 – Chamada Transnacional Conjunta", "Horizon Europe/CONFAP",
    "15/09/2026", "Pré: 02/12/2026; completa: 02/06/2027",
    "Consórcio de ≥3 países, com ≥2 da UE/associados; ICTs de FAPs participantes",
    ">€40 mi no programa; valor por projeto não encontrado", "FAPs financiam equipes BR; percentual não encontrado",
    "Pesquisa florestal, madeira e produtos de base florestal; elegibilidade conforme FAP estadual",
    "https://confap.org.br/pt/editais/119/chamada-transnacional-conjunta-forest-2026",
    "ISI Biomassa; IST Eficiência Operacional", "alta",
    "Produtos florestais e materiais de base biológica se alinham a biomassa e processos industriais.")
add("FUNDECT-MS nº 09/2026 – PAE-MS (eventos C,T&I)", "FUNDECT/SEMADESC-MS",
    "31/07/2026", "08/10/2026", "Proponentes de eventos científicos, tecnológicos e de inovação em MS",
    "Não encontrado", "Não encontrado",
    "SIGFUNDECT até 17h de Brasília; eventos regionais, nacionais ou internacionais em MS",
    "https://www.fundect.ms.gov.br/wp-content/uploads/2026/09/Prorrogacao_prazo_submissao_Chamada_PAE_26-1.pdf",
    "Sem aderência direta aos institutos", "none",
    "A chamada financia a realização de eventos; não há componente de P&D institucional identificado.",
    "Sim, divulgação científica; fora do escopo de P&D")

old["nao_confirmado"] = [
    item for item in old["nao_confirmado"]
    if not item["edital"].startswith(("FAPEG nº 02/2026", "MCTI/FINEP – Conhecimento Brasil"))
]

def deadline(item):
    import re
    match = re.search(r"\d{2}/\d{2}/\d{4}", item["encerramento"])
    return datetime.strptime(match.group(), "%d/%m/%Y").date() if match else date.max

for item in active:
    if item["status"] == "continuo":
        item["dias"] = "—"
    else:
        due = deadline(item)
        item["dias"] = str((due - TODAY).days) if due != date.max else "—"
active.sort(key=lambda e: (e["status"] == "continuo", deadline(e), e["edital"]))
names = {e["edital"] for e in active}
aderencia = [a for a in old["aderencia"] if a["edital"] in names]
aderencia.sort(key=lambda a: a["edital"])
urgent = [e for e in active if e["status"] == "aberto" and e["dias"].isdigit() and int(e["dias"]) <= 7]
count_open = sum(e["status"] == "aberto" for e in active)
count_cont = sum(e["status"] == "continuo" for e in active)
count_soon = sum(e["status"] == "breve" for e in active)

def table(headers, rows):
    def cell(value):
        return str(value or "—").replace("|", "/").replace("\n", " ")
    return "\n".join(["| " + " | ".join(headers) + " |",
                      "|" + "---|" * len(headers)] +
                     ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows])

new_names = ({e["edital"] for e in active} - {e["edital"] for e in old["editais"]}) - {"CONFAP–WBI Bélgica 2026"}
new = [e for e in active if e["edital"] in new_names]
changed = [
    ("CONFAP–WBI Bélgica 2026", "Prazo prorrogado de 30/09 para 30/10/2026 pela 3ª retificação; chamada nacional via FAPs aderentes."),
    ("FAPERJ nº 12/2026 – Centelha 3 RJ (Fase 2)", "Fase 2 aberta em 23/09; acesso restrito às selecionadas na Fase 1."),
    ("Sustainable Blue Economy Partnership – 4ª Call", "Chamada aberta; pré-propostas até 10/11/2026."),
    ("Biodiversa+ – BiodivFuture 2026–2027", "Chamada aberta; pré-propostas até 10/11/2026."),
    ("Finep COOPERAMAIS Tecnologia – ICT", "Página do edital informa 01/12/2026; notícia de 22/09 menciona 08/12. Confirmar retificação antes de submeter."),
    ("FUNDECT-MS nº 09/2026 – PAE-MS", "Retificação oficial de 08/09 prorrogou o prazo até 08/10/2026, 17h."),
    ("FAPEG nº 02/2026 – Eventos C&T&I", "Removido de não confirmado: fonte oficial o classifica como encerrado e publicou resultados."),
    ("MCTI/FINEP – Conhecimento Brasil", "Removido de não confirmado: prazo prorrogado pela Finep encerrou em 11/09/2026."),
]
lines = [
    "# Monitoramento de Editais de Inovação",
    "**Data de referência:** 2026-09-27 · domingo — America/Cuiaba; base para classificação de status/prazos.",
    "**Escopo:** Nacional (BR), estadual (prioridade MS/Centro-Oeste) e internacional com elegibilidade do Brasil.",
    "**Metodologia:** Revisão em fontes oficiais em 27/09/2026; prazos comparados com a data local. O monitor não é inventário exaustivo; inscrições condicionadas à elegibilidade e à etapa aplicável.",
    "",
    "## Novidades desde a última atualização (14/09/2026)",
    "",
    "### Novos editais incorporados nesta atualização",
    "",
    table(["Edital", "Fonte", "Abertura", "Encerramento", "Destaque"],
          [[e["edital"], e["fonte"], e["abertura"], e["encerramento"], e["valor"]] for e in new]),
    "", "### Editais encerrados ou retirados da lista ativa", "",
    table(["Edital", "Fonte", "Motivo do encerramento"],
          [[e["edital"], e["fonte"], reason] for e, reason in closed]),
    "", "### Alterações de prazo e status", "",
    table(["Edital", "Alteração"], changed),
    "", "## Resumo Executivo", "",
    f"- **Abertos agora:** {count_open} editais com etapa vigente em 27/09/2026, mais {count_cont} linhas de fluxo contínuo sem prazo definido.",
    f"- **Em breve:** {count_soon} chamadas com abertura programada.",
    f"- **Alerta (encerramento em ≤ 7 dias):** {len(urgent)} editais: " + "; ".join(f"{e['edital']} ({e['encerramento']})" for e in urgent) + ".",
    f"- **Não confirmado:** {len(old['nao_confirmado'])} itens sem janela de inscrição confirmada, listados ao final.",
    "", "> **Alerta de prazo:** " + "; ".join(f"{e['edital']} ({e['encerramento']})" for e in urgent) + ".",
    "", "## Tabela de Editais (ordenada por encerramento mais próximo)", "",
    table(["Edital", "Fonte", "Status", "Abertura", "Encerramento", "Dias restantes", "Público-alvo", "Valor/Faixa", "Contrapartida", "Principais exigências", "Link"],
          [[e["edital"], e["fonte"], {"aberto": "Aberto", "continuo": "Fluxo contínuo", "breve": "Em breve"}[e["status"]],
            e["abertura"], e["encerramento"], e["dias"], e["publico"], e["valor"], e["contrapartida"], e["exigencias"], e["link"]] for e in active]),
    "", "## Editais \"Não confirmado\" (datas não extraídas após busca)", "",
    table(["Edital", "Fonte", "Motivo"], [[e["edital"], e["fonte"], e["motivo"]] for e in old["nao_confirmado"]]),
    "", "## Aderência com os institutos SENAI/MS", "",
    table(["Edital", "Instituto(s) com maior aderência", "Grau de aderência", "Foco educacional?", "Justificativa"],
          [[a["edital"], a["institutos"], {"alta": "Alta", "media": "Média", "baixa": "Baixa", "none": "Sem aderência identificada"}[a["grau"]],
            a["foco_educacional"], a["justificativa"]] for a in aderencia]),
    "", "## Observações de método", "",
    "> A página oficial da Finep para COOPERAMAIS ICT indica 01/12/2026, mas notícia institucional cita 08/12/2026. Foi adotada a data mais conservadora do edital. Verificar retificações antes da submissão.",
    "> Para PRONINC, a página da chamada informa cadastro até 09/10/2026, enquanto a notícia institucional menciona 16/10/2026. Foi adotada a data mais conservadora da chamada.",
    "> Chamadas PIPE com prazo de proposta completa e Centelha Fase 2 permanecem visíveis somente para participantes aprovados na etapa anterior.",
    "> Tecnova 2026/2027 é programa guarda-chuva, sem janela nacional de inscrição. O Chamamento InovaSUS Digital e o desafio Finep Agricultura Familiar já encerraram as etapas de submissão.",
    "> Valores e contrapartidas não localizados nas fontes consultadas aparecem como Não encontrado; a aderência é avaliação temática e não garante elegibilidade institucional.",
    ""
]
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"{OUT}: {count_open} abertos, {count_cont} contínuos, {count_soon} em breve, {len(urgent)} urgentes; {len(closed)} retirados")
