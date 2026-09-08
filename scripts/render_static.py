#!/usr/bin/env python3
"""
render_static.py — Gera index.html estático a partir do data/editais.json.

Útil para pré-visualizar sem servidor ou para gerar uma versão
totalmente estática (sem dependência de fetch).

Uso:
    python scripts/render_static.py [caminho_para_json] [caminho_para_html]
"""

import json
import re
import sys
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parent.parent


def newsletter_webapp_url():
    """Lê webappUrl de data/newsletter.js (para o action do form estático)."""
    cfg_path = ROOT / "data" / "newsletter.js"
    if cfg_path.exists():
        m = re.search(r'webappUrl:\s*"([^"]*)"', cfg_path.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    return ""


def newsletter_section():
    action = escape(newsletter_webapp_url())
    return f'''    <section class="doc" id="newsletter">
      <div class="sec-head"><span class="tag">Fique por dentro</span><h2>Receba as novidades por e-mail</h2><p>Assine e receba um resumo com os novos editais, prazos alterados e alertas de encerramento sempre que houver uma atualização do radar — direto na sua caixa de entrada.</p></div>
      <div class="spec-card nl-card">
        <form class="nl-form" id="nl-form" method="POST" target="nl-frame" action="{action}" novalidate>
          <input type="text" name="website" class="nl-hp" value="" tabindex="-1" autocomplete="off" aria-hidden="true">
          <div class="nl-grid">
            <label class="nl-field"><span class="glabel">Nome</span><input class="nl-input" id="nl-nome" name="nome" type="text" maxlength="80" autocomplete="name" placeholder="Seu nome"></label>
            <label class="nl-field"><span class="glabel">E-mail</span><input class="nl-input" id="nl-email" name="email" type="email" maxlength="120" autocomplete="email" placeholder="voce@empresa.com.br" inputmode="email"></label>
          </div>
          <label class="nl-check"><input type="checkbox" id="nl-consent" name="consentimento" value="sim"> <span>Concordo em receber e-mails de atualização dos editais de inovação do SENAI MS e sei que posso cancelar a qualquer momento.</span></label>
          <button class="nl-btn" type="submit">Assinar a newsletter</button>
        </form>
        <div class="nl-status" id="nl-status" hidden role="status" aria-live="polite"></div>
        <iframe id="nl-frame" name="nl-frame" style="display:none" tabindex="-1" aria-hidden="true" title="Destino do formulário"></iframe>
        <div class="nl-perks"><span class="nl-perk">Resumo semanal das novidades</span><span class="nl-perk">Alertas de prazos que encerram em breve</span><span class="nl-perk">Novos editais assim que mapeados</span><span class="nl-perk">Cancele quando quiser, com 1 clique</span></div>
      </div>
      <p class="note"><b>Seus dados:</b> usamos nome e e-mail exclusivamente para o envio destas atualizações, com consentimento e confirmação por e-mail (dupla verificação), conforme a LGPD (Lei nº 13.709/2018). O cancelamento está disponível em todas as mensagens.</p>
    </section>
'''


def status_pill(status):
    labels = {'aberto': 'Aberto', 'continuo': 'Contínuo', 'breve': 'Em breve'}
    classes = {'aberto': 'p-open', 'continuo': 'p-cont', 'breve': 'p-soon'}
    return f'<span class="pill {classes.get(status, "p-na")}">{labels.get(status, status)}</span>'


def grade_badge(grau):
    labels = {'alta': 'Alta', 'media': 'Média', 'baixa': 'Baixa', 'none': 'Sem aderência'}
    classes = {'alta': 'g-alta', 'media': 'g-media', 'baixa': 'g-baixa', 'none': 'g-none'}
    return f'<span class="g {classes.get(grau, "g-none")}">{labels.get(grau, grau)}</span>'


def dias_class(dias):
    if not dias:
        return ''
    d = dias.strip()
    import re
    if re.match(r'^\d+$', d):
        if int(d) <= 7:
            return 'urgent'
    if 'hoje' in d:
        return 'urgent'
    return ''


def render(data):
    m = data.get('meta', {})
    s = data.get('stats', {})
    # fallback for fields not in markdown
    m.setdefault('sources', 'FINEP · CNPq · FAPs · BNDES · Embrapii · Horizon Europe')
    m.setdefault('version', 'Site 2.0 — Senai Design System')

    # Build editais rows
    editais_rows = ''
    for e in data['editais']:
        cont = ' edital--cont' if e['status'] == 'continuo' else ''
        link = f'<a class="link" href="{escape(e["link"])}" target="_blank" rel="noopener">link</a>' if e.get('link') else ''
        editais_rows += f'''<tr data-s="{e['status']}"><td class="edital{cont}">{escape(e['edital'])}</td><td class="src">{escape(e['fonte'])}</td><td>{status_pill(e['status'])}</td><td>{escape(e['abertura'])}</td><td>{escape(e['encerramento'])}</td><td class="{dias_class(e['dias'])}">{escape(e['dias'])}</td><td>{escape(e['publico'])}</td><td>{escape(e['valor'])}</td><td>{escape(e['contrapartida'])}</td><td>{escape(e['exigencias'])}</td><td>{link}</td></tr>\n'''

    # Build aderência rows
    aderencia_rows = ''
    for a in data['aderencia']:
        aderencia_rows += f'''<tr data-g="{a['grau']}"><td class="edital">{escape(a['edital'])}</td><td class="src">{escape(a['institutos'])}</td><td>{grade_badge(a['grau'])}</td><td>{escape(a['foco_educacional'])}</td><td>{escape(a['justificativa'])}</td></tr>\n'''

    # Build não confirmado rows
    nao_conf_rows = ''
    for n in data['nao_confirmado']:
        nao_conf_rows += f'''<tr><td class="edital">{escape(n['edital'])}</td><td class="src">{escape(n['fonte'])}</td><td>{escape(n['motivo'])}</td></tr>\n'''

    # Build resumo
    resumo_items = ''.join(f'<div style="margin-bottom:6px">• {escape(line)}</div>' for line in data['resumo_executivo'])

    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Monitor — Editais de Inovação | SENAI MS</title>
<link rel="stylesheet" href="css/tokens.css">
<link rel="stylesheet" href="css/style.css">
</head>
<body>
<div class="geo-bg" aria-hidden="true">
  <div class="geo g1"><img src="assets/logo-senai-fiems.png" alt=""></div>
  <div class="geo g2"><img src="assets/logo-senai-fiems.png" alt=""></div>
  <div class="geo g3"><img src="assets/logo-senai-fiems.png" alt=""></div>
  <div class="geo g4"><img src="assets/logo-senai-fiems.png" alt=""></div>
  <div class="geo g5"><img src="assets/logo-senai-fiems.png" alt=""></div>
  <div class="geo g6"><img src="assets/logo-senai-fiems.png" alt=""></div>
  <div class="geo g7"><img src="assets/logo-senai-fiems.png" alt=""></div>
  <div class="geo g8"><img src="assets/logo-senai-fiems.png" alt=""></div>
</div>
<nav class="docnav" aria-label="Navegação do relatório">
  <div class="wrap">
    <a class="brandmark" href="#"><img src="assets/logo-senai-fiems.png" alt="SENAI MS — Sistema FIEMS"><span class="sys">Monitor · Editais</span></a>
    <nav id="nav-menu" aria-label="Seções"><a href="#resumo" class="active">Resumo</a><a href="#newsletter">Newsletter</a><a href="#aderencia">Aderência SENAI</a><a href="#editais">Editais</a><a href="#nao-confirmado">Não confirmado</a></nav>
    <a class="newsletter-cta" href="#newsletter" aria-label="Assinar a newsletter do Radar de Editais"><span aria-hidden="true">✉</span> Newsletter</a>
    <button class="nav-toggle" id="nav-toggle" aria-label="Abrir menu" aria-expanded="false" aria-controls="nav-menu"><span></span></button>
  </div>
</nav>
<div class="drawer-backdrop" id="drawer-backdrop" aria-hidden="true"></div>
<header class="cover">
  <div class="bars"><div style="background:var(--blue-500)"></div><div style="background:var(--sesi-green)"></div><div style="background:var(--orange-500)"></div><div style="background:var(--iel-teal)"></div></div>
  <div class="logo-badge"><img src="assets/logo-senai-fiems.png" alt="SENAI Sistema FIEMS"></div>
  <div class="wrap">
    <div class="eyebrow">Sistema FIEMS · SENAI MS — Monitoramento de Fomento</div>
    <h1>Monitoramento de<br><em>Editais de Inovação</em></h1>
    <p class="lead">Editais, chamadas públicas e programas de fomento abertos ou próximos de abrir — nacional, estadual (MS) e internacionais com elegibilidade do Brasil.</p>
    <div class="meta">
      <div><b>Data de referência</b><span>{escape(m['reference_date_formatted'])}</span></div>
      <div><b>Escopo</b><span>{escape(m['scope'])}</span></div>
      <div><b>Fontes</b><span>{escape(m['sources'])}</span></div>
      <div><b>Versão</b><span>{escape(m['version'])}</span></div>
    </div>
  </div>
</header>
<main>
  <div class="wrap">
    <div class="stats">
      <div class="stat ok"><div class="n">{s['abertos']}</div><div class="l">Editais abertos agora</div></div>
      <div class="stat cyan"><div class="n">{s['continuos']}</div><div class="l">Fluxo contínuo (sem prazo)</div></div>
      <div class="stat"><div class="n">{s['em_breve']}</div><div class="l">Em breve (abrem set/2026)</div></div>
      <div class="stat alert"><div class="n">{s['encerram_7d']}</div><div class="l">Encerram em ≤ 7 dias</div></div>
    </div>
    <section class="doc" id="resumo">
      <div class="sec-head"><span class="tag">Visão geral</span><h2>Resumo Executivo</h2><p>Panorama em {escape(m['reference_date_formatted'])} do funil de oportunidades ativas.</p></div>
      <div class="spec-card"><div class="spec-card__body">{resumo_items}</div></div>
    </section>
{newsletter_section()}  </div>
  <section class="doc doc--full" id="aderencia">
    <div class="sec-head"><span class="tag">Primeira leitura</span><h2>Aderência com os institutos SENAI/MS</h2><p>Avaliados apenas Aberto + Em breve.</p></div>
    <div class="filter-inline" id="filt-aderencia">
      <div class="filter-inline__left"><span class="flabel">Filtrar grau:</span><div class="fbtn-group" role="group"><button class="fbtn active" data-g="all" type="button">Todos</button><button class="fbtn" data-g="alta" type="button">Alta</button><button class="fbtn" data-g="media" type="button">Média</button><button class="fbtn" data-g="baixa" type="button">Baixa</button><button class="fbtn" data-g="none" type="button">Sem aderência</button></div></div>
      <div class="filter-inline__right"><input class="fsearch fsearch--grow" id="search-aderencia" type="text" placeholder="Buscar edital ou instituto…"></div>
      <span class="fcount" id="count-aderencia"></span>
    </div>
    <div class="spec-card table-full"><div class="tbl-wrap"><table id="tbl-aderencia"><thead><tr><th>Edital</th><th>Instituto(s) com maior aderência</th><th>Grau</th><th>Foco educacional?</th><th>Justificativa</th></tr></thead><tbody>{aderencia_rows}</tbody></table></div></div>
  </section>
  <section class="doc doc--full" id="editais">
    <div class="sec-head"><span class="tag">Base completa</span><h2>Editais — Aberto / Em breve</h2><p>Ordenado por encerramento mais próximo.</p></div>
    <div class="editais-toolbar"><button id="fab-filtros" class="fab-filtros" type="button">☰ Filtros <span class="fab-badge" id="fab-badge" hidden>0</span></button><span class="fcount fcount--inline" id="count-editais-top"></span></div>
    <div class="editais-layout"><aside class="sidebar" id="sidebar" aria-label="Filtros dos editais"><div class="sidebar-card" id="filt-editais"><div class="sidebar-head"><h3>Filtros</h3><button class="drawer-close" id="drawer-close" type="button" aria-label="Fechar filtros">×</button></div><div class="fgrid"><div class="fgroup"><span class="glabel">Institutos Senai</span><select class="fselect" id="f-inst"><option value="all">Todos</option><option value="alimentos">IST Alimentos e Bebidas</option><option value="eficiencia">IST Eficiência Operacional</option><option value="biomassa">ISI Biomassa</option></select></div><div class="fgroup"><span class="glabel">Status dos Editais</span><select class="fselect" id="f-status"><option value="all">Todos</option><option value="aberto">Aberto</option><option value="breve">Em breve</option><option value="continuo">Fluxo contínuo</option></select></div><div class="fgroup"><span class="glabel">Dias restantes</span><select class="fselect" id="f-dias"><option value="all">Todos</option><option value="d7">≤ 7 dias</option><option value="d30">8–30 dias</option><option value="d60">31–60 dias</option><option value="d60p">> 60 dias</option><option value="cont">Contínuo / sem prazo</option></select></div><div class="fgroup"><span class="glabel">Fonte</span><select class="fselect" id="f-fonte"><option value="all">Todos</option></select></div><div class="fgroup"><span class="glabel">Público-alvo</span><select class="fselect" id="f-publico"><option value="all">Todos</option></select></div><div class="fgroup"><span class="glabel">Contrapartida</span><select class="fselect" id="f-contra"><option value="all">Todos</option></select></div></div><div class="fgroup fgroup--search"><span class="glabel">Busca livre</span><input class="fsearch" id="search-editais" type="text" placeholder="Digite para buscar…"></div><div class="f-actions"><button class="freset" id="f-reset" type="button">↺ Limpar filtros</button><span class="fcount" id="count-editais"></span></div></div></aside></div>
    <div class="spec-card table-full"><div class="tbl-wrap"><table id="tbl-editais"><thead><tr><th>Edital</th><th>Fonte</th><th>Status</th><th>Abertura</th><th>Encerramento</th><th>Dias</th><th>Público-alvo</th><th>Valor / Faixa</th><th>Contrapartida</th><th>Principais exigências</th><th>Link</th></tr></thead><tbody>{editais_rows}</tbody></table></div></div>
    <div class="wrap"><div class="callout"><b>⚠ Alerta de prazo:</b> {escape(data['alerta_prazo'])}</div></div>
  </section>
  <section class="doc doc--full" id="nao-confirmado">
    <div class="sec-head"><span class="tag">Pendências</span><h2>Editais "Não confirmado"</h2><p>Datas não extraídas de fonte oficial após busca aprofundada.</p></div>
    <div class="spec-card table-full"><div class="tbl-wrap"><table><thead><tr><th>Edital</th><th>Fonte</th><th>Motivo</th></tr></thead><tbody>{nao_conf_rows}</tbody></table></div></div>
    <div class="wrap"><p class="note"><b>Metodologia:</b> {escape(m['methodology'])}</p></div>
  </section>
</main>
<footer class="footer"><p><b>Monitor — Editais de Inovação</b> · SENAI MS · Sistema FIEMS · 2026</p></footer>
<script src="data/newsletter.js"></script>
<script src="js/render.js"></script>
<script src="js/filters.js"></script>
<script src="js/newsletter.js"></script>
<script src="js/app.js"></script>
</body>
</html>'''
    return html


def main():
    if len(sys.argv) > 1:
        json_path = Path(sys.argv[1])
    else:
        json_path = ROOT / "data" / "editais.json"

    if len(sys.argv) > 2:
        html_path = Path(sys.argv[2])
    else:
        html_path = ROOT / "index.html"

    print(f"Lendo: {json_path}")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    html = render(data)
    html_path.write_text(html, encoding="utf-8")
    print(f"Gerado: {html_path}")
    print(f"  Editais: {len(data['editais'])}")
    print(f"  Aderência: {len(data['aderencia'])}")
    print(f"  Não confirmado: {len(data['nao_confirmado'])}")


if __name__ == "__main__":
    main()
