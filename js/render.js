/* render.js — generates DOM from JSON data */
const Render = (() => {

  /* ========== Helpers ========== */
  function el(tag, attrs = {}, children = []) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'class') e.className = v;
      else if (k === 'html') e.innerHTML = v;
      else if (k === 'text') e.textContent = v;
      else if (k.startsWith('data-')) e.setAttribute(k, v);
      else if (k === 'href') e.setAttribute('href', v);
      else if (k === 'target') e.setAttribute('target', v);
      else e.setAttribute(k, v);
    }
    const arr = Array.isArray(children) ? children : [children];
    arr.forEach(c => {
      if (c == null) return;
      e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    });
    return e;
  }

  function statusPill(status) {
    const labels = { aberto: 'Aberto', continuo: 'Contínuo', breve: 'Em breve' };
    const classes = { aberto: 'p-open', continuo: 'p-cont', breve: 'p-soon' };
    return el('span', { class: `pill ${classes[status] || 'p-na'}`, text: labels[status] || status });
  }

  function gradeBadge(grau) {
    const labels = { alta: 'Alta', media: 'Média', baixa: 'Baixa', none: 'Sem aderência' };
    const classes = { alta: 'g-alta', media: 'g-media', baixa: 'g-baixa', none: 'g-none' };
    return el('span', { class: `g ${classes[grau] || 'g-none'}`, text: labels[grau] || grau });
  }

  function diasClass(dias) {
    if (dias && /^\d+$/.test(dias.trim())) {
      const d = parseInt(dias, 10);
      if (d <= 7) return 'urgent';
    }
    if (dias && /hoje/.test(dias)) return 'urgent';
    return '';
  }

  /* ========== Hero / Meta ========== */
  function hero(data) {
    const m = data.meta;
    return el('header', { class: 'cover' }, [
      el('div', { class: 'bars' }, [
        el('div', { style: 'background:var(--blue-500)' }),
        el('div', { style: 'background:var(--sesi-green)' }),
        el('div', { style: 'background:var(--orange-500)' }),
        el('div', { style: 'background:var(--iel-teal)' }),
      ]),
      el('div', { class: 'wrap' }, [
        el('h1', {}, [el('span', { text: 'Oportunidades de' }), el('br'), el('em', { text: 'Editais de Inovação' })]),
        el('p', { class: 'lead', text: 'Editais, chamadas públicas e programas de fomento abertos ou próximos de abrir — nacional, estadual (MS) e internacionais com elegibilidade do Brasil.' }),
      ]),
    ]);
  }

  /* ========== Stats ========== */
  function stats(s) {
    const items = [
      { n: s.abertos, l: 'Editais abertos agora', cls: 'ok' },
      { n: s.continuos, l: 'Fluxo contínuo (sem prazo)', cls: 'cyan' },
      { n: s.em_breve, l: 'Em breve (abrem set/2026)', cls: '' },
      { n: s.encerram_7d, l: 'Encerram em ≤ 7 dias', cls: 'alert' },
    ];
    return el('div', { class: 'stats' }, items.map(i =>
      el('div', { class: `stat ${i.cls}` }, [
        el('div', { class: 'n', text: String(i.n) }),
        el('div', { class: 'l', text: i.l }),
      ])
    ));
  }

  /* ========== Resumo Executivo ========== */
  function resumo(data) {
    const body = el('div', { class: 'spec-card' }, [el('div', { class: 'spec-card__body' })]);
    const b = body.querySelector('.spec-card__body');
    data.resumo_executivo.forEach(line => {
      b.appendChild(el('div', { style: 'margin-bottom:6px', text: '• ' + line }));
    });
    return el('section', { class: 'doc', id: 'resumo' }, [
      el('div', { class: 'sec-head' }, [
        el('h2', { text: 'Resumo Executivo' }),
        el('p', { text: `Panorama em ${data.meta.reference_date_formatted} do funil de oportunidades ativas. A tabela de aderência está no topo para orientar a leitura pelos institutos SENAI/MS.` }),
      ]),
      body,
    ]);
  }

  /* ========== Novidades ========== */
  function novidades(data) {
    const n = data.novidades;
    if (!n || (!n.novos_editais?.length && !n.editais_encerrados?.length && !n.alteracoes_prazo?.length)) {
      return null;
    }

    // Stats row
    const statsItems = [];
    if (n.novos_editais?.length) {
      statsItems.push(el('div', { class: 'nov-stat nov-stat--open' }, [
        el('div', { class: 'nov-stat__icon', html: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>' }),
        el('div', { class: 'nov-stat__info' }, [
          el('div', { class: 'nov-stat__n', text: String(n.novos_editais.length) }),
          el('div', { class: 'nov-stat__l', text: 'Novos editais' }),
        ]),
      ]));
    }
    if (n.editais_encerrados?.length) {
      statsItems.push(el('div', { class: 'nov-stat nov-stat--closed' }, [
        el('div', { class: 'nov-stat__icon', html: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>' }),
        el('div', { class: 'nov-stat__info' }, [
          el('div', { class: 'nov-stat__n', text: String(n.editais_encerrados.length) }),
          el('div', { class: 'nov-stat__l', text: 'Encerrados' }),
        ]),
      ]));
    }
    if (n.alteracoes_prazo?.length) {
      statsItems.push(el('div', { class: 'nov-stat nov-stat--changed' }, [
        el('div', { class: 'nov-stat__icon', html: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>' }),
        el('div', { class: 'nov-stat__info' }, [
          el('div', { class: 'nov-stat__n', text: String(n.alteracoes_prazo.length) }),
          el('div', { class: 'nov-stat__l', text: 'Alterados' }),
        ]),
      ]));
    }

    // Manta todos os itens em um array único com tipo
    const allItems = [];

    if (n.novos_editais?.length) {
      n.novos_editais.forEach(e => {
        allItems.push({ type: 'novo', ...e });
      });
    }
    if (n.editais_encerrados?.length) {
      n.editais_encerrados.forEach(e => {
        allItems.push({ type: 'encerrado', ...e });
      });
    }
    if (n.alteracoes_prazo?.length) {
      n.alteracoes_prazo.forEach(e => {
        allItems.push({ type: 'alterado', ...e });
      });
    }

    // Renderiza todos como cards uniformes
    const tagMap = {
      novo: { label: 'Novo', cls: 'pill p-open' },
      encerrado: { label: 'Encerrado', cls: 'pill p-closed' },
      alterado: { label: 'Prazo alterado', cls: 'pill p-soon' },
    };

    const cards = allItems.map(item => {
      const tag = tagMap[item.type];
      const tags = [];
      const fonte = item.Fonte || item.fonte || '';
      const abertura = item.Abertura || '';
      const encerramento = item.Encerramento || item.encerramento || '';
      const motivo = item.Motivo || item.motivo || '';
      const alteracao = item.Alteração || item.alteracao || '';
      const editalName = item.Edital || item.edital || '';
      const noveltyLinks = {
        'Programa Desafios da Amazônia (Amazônia+10)': 'https://www.amazonfund.gov.br/pt/como-apresentar-projetos/chamadas-publicas/programa-desafios-da-amazonia/',
        'FAPESP PIPE Jornada Tecnológica – Transição Energética (Fase 1)': 'https://fapesp.br/18291/chamada-de-propostas-para-o-programa-pipe-jornada-tecnologica-transicao-energetica-fase-1',
        'FINEP Mais Inovação Brasil R2 – Transição Energética': 'https://www.finep.gov.br/chamadas-publicas/chamadapublica/772',
        'FAPESP – JSPS Japão 2026 (Projetos Conjuntos)': 'https://fapesp.br/index.php/18319/chamada-conjunta-de-propostas-sociedade-japonesa-para-a-promocao-da-ciencia-jsps-e-fundacao-de-amparo-a-pesquisa-do-estado-de-sao-paulo-fapesp-2026',
        'Observatório Nacional – Bolsas de Doutorado RSBR 2026': 'https://www.gov.br/observatorio/pt-br/assuntos/noticias/observatorio-nacional-lanca-edital-para-selecao-de-bolsista-em-projeto-da-rede-sismografica-brasileira',
        'FAPERJ nº 12/2026 – Centelha 3 RJ': 'https://www.faperj.br/?id=28.5.7',
      };
      const directLink = item.Link || item.link || noveltyLinks[editalName] || data.editais?.find(e => e.edital === editalName || e.edital.startsWith(editalName))?.link || '';

      if (fonte) tags.push(el('span', { class: 'nov-tag', text: fonte }));
      if (abertura) tags.push(el('span', { class: 'nov-tag nov-tag--muted', text: 'Abre: ' + abertura }));

      const destaque = item.Destaque || motivo || alteracao || '';

      return el('div', { class: 'nov-card' }, [
        el('div', { class: 'nov-card__head' }, [
          el('div', { class: 'nov-card__title', text: editalName }),
          el('span', { class: tag.cls, text: tag.label }),
        ]),
        el('div', { class: 'nov-card__tags' }, tags),
        el('div', { class: 'nov-card__body', text: destaque }),
        (encerramento || directLink) ? el('div', { class: 'nov-card__footer' }, [
          encerramento ? el('span', { class: 'nov-deadline' }, [
            ...(encerramento ? [el('b', { text: 'Encerramento: ' }), document.createTextNode(encerramento)] : []),
          ]) : null,
          directLink ? el('a', { class: 'nov-card__link', href: directLink, target: '_blank', rel: 'noopener', text: 'Acessar edital' }) : null,
        ]) : null,
      ]);
    });

    return el('section', { class: 'doc', id: 'novidades' }, [
      el('div', { class: 'wrap' }, [
        el('div', { class: 'sec-head' }, [
          el('h2', { text: 'Novidades' }),
        ]),
        el('div', { class: 'nov-stats' }, statsItems),
        el('div', { class: 'nov-cards' }, cards),
      ]),
    ]);
  }

  /* ========== Editais table ========== */
  function editaisSection(data) {
    const editais = data.editais;
    const headers = ['Edital', 'Fonte', 'Status', 'Abertura', 'Encerramento', 'Dias', 'Tipo público', 'Público-alvo', 'Valor', 'Contrapartida', 'Exigências', 'Link'];

    const thead = el('thead', {}, [el('tr', {}, headers.map(h => el('th', { text: h })))]);
    const tbody = el('tbody', {});
    editais.forEach(e => {
      const tr = el('tr', { 'data-s': e.status, 'data-tipo': e.tipo_publico || '' }, [
        el('td', { class: `edital${e.status === 'continuo' ? ' edital--cont' : ''}`, text: e.edital }),
        el('td', { class: 'src', text: e.fonte }),
        el('td', {}, [statusPill(e.status)]),
        el('td', { text: e.abertura }),
        el('td', { text: e.encerramento }),
        el('td', { class: diasClass(e.dias), text: e.dias.replace(/\*\*/g, '').replace(/\s*\(hoje\)/i, '').trim() }),
        el('td', { text: e.tipo_publico || '—' }),
        el('td', { text: e.publico }),
        el('td', { text: e.valor }),
        el('td', { text: e.contrapartida }),
        el('td', { text: e.exigencias }),
        el('td', {}, e.link ? [el('a', { class: 'link', href: e.link, target: '_blank', rel: 'noopener', text: 'link' })] : []),
      ]);
      tr._data = e;
      tbody.appendChild(tr);
    });

    const table = el('table', { id: 'tbl-editais' }, [thead, tbody]);
    const cards = el('div', { class: 'tbl-cards', id: 'cards-editais', 'aria-hidden': 'true' });
    const scrollHint = el('div', { class: 'tbl-scroll-hint', 'aria-hidden': 'true' }, [el('span', { text: '← arraste para ver mais →' })]);

    const specCard = el('div', { class: 'spec-card' }, [
      scrollHint,
      el('div', { class: 'tbl-wrap' }, [table]),
      cards,
    ]);

    // filter bar (mobile)
    const fab = el('button', { id: 'fab-filtros', class: 'fab-filtros', type: 'button', 'aria-controls': 'sidebar', 'aria-expanded': 'false' }, [
      document.createTextNode('☰ Filtros '),
      el('span', { class: 'fab-badge', id: 'fab-badge', hidden: 'true', text: '0' }),
    ]);
    const countTop = el('span', { class: 'fcount fcount--inline', id: 'count-editais-top' });
    const toolbar = el('div', { class: 'editais-toolbar' }, [fab, countTop]);

    // sidebar filters
    const selInst = el('select', { class: 'fselect', id: 'f-inst' }, [
      el('option', { value: 'all', text: 'Todos' }),
      el('option', { value: 'alimentos', text: 'IST Alimentos e Bebidas' }),
      el('option', { value: 'eficiencia', text: 'IST Eficiência Operacional' }),
      el('option', { value: 'biomassa', text: 'ISI Biomassa' }),
    ]);
    const selStatus = el('select', { class: 'fselect', id: 'f-status' }, [
      el('option', { value: 'all', text: 'Todos' }),
      el('option', { value: 'aberto', text: 'Aberto' }),
      el('option', { value: 'breve', text: 'Em breve' }),
      el('option', { value: 'continuo', text: 'Fluxo contínuo' }),
    ]);
    const selDias = el('select', { class: 'fselect', id: 'f-dias' }, [
      el('option', { value: 'all', text: 'Todos' }),
      el('option', { value: 'd7', text: '≤ 7 dias' }),
      el('option', { value: 'd30', text: '8–30 dias' }),
      el('option', { value: 'd60', text: '31–60 dias' }),
      el('option', { value: 'd60p', text: '> 60 dias' }),
      el('option', { value: 'cont', text: 'Contínuo' }),
    ]);
    const selTipo = el('select', { class: 'fselect', id: 'f-tipo' }, [
      el('option', { value: 'all', text: 'Todos' }),
      el('option', { value: 'Empresa', text: 'Empresa' }),
      el('option', { value: 'Pessoa Física', text: 'Pessoa Física' }),
    ]);
    const selFonte = el('select', { class: 'fselect', id: 'f-fonte' }, [el('option', { value: 'all', text: 'Todos' })]);
    const selPublico = el('select', { class: 'fselect', id: 'f-publico' }, [el('option', { value: 'all', text: 'Todos' })]);
    const selContra = el('select', { class: 'fselect', id: 'f-contra' }, [el('option', { value: 'all', text: 'Todos' })]);
    const search = el('input', { class: 'fsearch', id: 'search-editais', type: 'text', placeholder: 'Digite para buscar…' });
    const reset = el('button', { class: 'freset', id: 'f-reset', type: 'button', text: '↺ Limpar filtros' });
    const count = el('span', { class: 'fcount', id: 'count-editais' });

    const sidebar = el('aside', { class: 'sidebar', id: 'sidebar', 'aria-label': 'Filtros dos editais' }, [
      el('div', { class: 'sidebar-card', id: 'filt-editais' }, [
        el('div', { class: 'sidebar-head' }, [
          el('h3', { text: 'Filtros Avançados' }),
          el('button', { class: 'drawer-close', id: 'drawer-close', type: 'button', 'aria-label': 'Fechar filtros', text: '×' }),
        ]),
        el('div', { class: 'fgrid' }, [
          el('div', { class: 'fgroup' }, [el('span', { class: 'glabel', text: 'Institutos Senai' }), selInst]),
          el('div', { class: 'fgroup' }, [el('span', { class: 'glabel', text: 'Status' }), selStatus]),
          el('div', { class: 'fgroup' }, [el('span', { class: 'glabel', text: 'Tipo de público' }), selTipo]),
          el('div', { class: 'fgroup' }, [el('span', { class: 'glabel', text: 'Dias restantes' }), selDias]),
          el('div', { class: 'fgroup' }, [el('span', { class: 'glabel', text: 'Fonte' }), selFonte]),
          el('div', { class: 'fgroup' }, [el('span', { class: 'glabel', text: 'Público-alvo' }), selPublico]),
          el('div', { class: 'fgroup' }, [el('span', { class: 'glabel', text: 'Contrapartida' }), selContra]),
          el('div', { class: 'fgroup fgroup--search' }, [el('span', { class: 'glabel', text: 'Busca livre' }), search]),
        ]),
        el('div', { class: 'f-actions' }, [reset, count]),
      ]),
    ]);

    // Build wrap content
    const wrapContent = [
      el('div', { class: 'sec-head' }, [
        el('h2', { text: 'Editais — Aberto | Em breve' }),
        el('p', {}, [
          document.createTextNode('Ordenado por encerramento mais próximo. Use os filtros abaixo para refinar por instituto SENAI, status, tipo de público, fonte, contrapartida ou prazo.'),
        ]),
      ]),
      toolbar,
      sidebar,
      specCard,
    ];
    if (data.alerta_prazo) {
      wrapContent.push(el('div', { class: 'callout' }, [
        el('b', { text: '⚠ Alerta de prazo:' }),
        document.createTextNode(' ' + data.alerta_prazo),
      ]));
    }

    return el('section', { class: 'doc', id: 'editais' }, [
      el('div', { class: 'wrap' }, wrapContent),
    ]);
  }

  /* ========== Aderência ========== */
  function aderenciaSection(data) {
    const headers = ['Edital', 'Instituto(s) com maior aderência', 'Grau', 'Foco educacional?', 'Justificativa', 'Link'];
    const thead = el('thead', {}, [el('tr', {}, headers.map(h => el('th', { text: h })))]);
    const tbody = el('tbody', {});
    data.aderencia.filter(a => a.grau !== 'none' && a.institutos && a.institutos.trim() !== '—').forEach(a => {
      const link = data.editais?.find(e => e.edital === a.edital || e.edital.startsWith(a.edital))?.link || '';
      const tr = el('tr', { 'data-g': a.grau }, [
        el('td', { class: 'edital', text: a.edital }),
        el('td', { class: 'src', text: a.institutos }),
        el('td', {}, [gradeBadge(a.grau)]),
        el('td', { text: a.foco_educacional }),
        el('td', { text: a.justificativa }),
        el('td', {}, link ? [el('a', { class: 'link', href: link, target: '_blank', rel: 'noopener', text: 'Link' })] : []),
      ]);
      tbody.appendChild(tr);
    });

    const table = el('table', { id: 'tbl-aderencia' }, [thead, tbody]);
    const cards = el('div', { class: 'tbl-cards', id: 'cards-aderencia', 'aria-hidden': 'true' });
    const scrollHint = el('div', { class: 'tbl-scroll-hint', 'aria-hidden': 'true' }, [el('span', { text: '← arraste para ver mais →' })]);
    const specCard = el('div', { class: 'spec-card' }, [
      scrollHint,
      el('div', { class: 'tbl-wrap' }, [table]),
      cards,
    ]);

    const filterBar = el('div', { class: 'filter-inline', id: 'filt-aderencia' }, [
      el('div', { class: 'fgrid', style: 'grid-template-columns:repeat(3,1fr) 1fr;gap:16px;align-items:end' }, [
        el('div', { class: 'fgroup' }, [
          el('span', { class: 'glabel', text: 'Instituto Senai' }),
          el('select', { class: 'fselect', id: 'f-ader-inst' }, [
            el('option', { value: 'all', text: 'Todos' }),
            el('option', { value: 'IST Alimentos e Bebidas', text: 'IST Alimentos e Bebidas' }),
            el('option', { value: 'IST Eficiência Operacional', text: 'IST Eficiência Operacional' }),
            el('option', { value: 'ISI Biomassa', text: 'ISI Biomassa' }),
          ]),
        ]),
        el('div', { class: 'fgroup' }, [
          el('span', { class: 'glabel', text: 'Foco Educacional' }),
          el('select', { class: 'fselect', id: 'f-ader-foco' }, [
            el('option', { value: 'all', text: 'Todos' }),
            el('option', { value: 'Não', text: 'Não' }),
            el('option', { value: 'Sim', text: 'Sim' }),
          ]),
        ]),
        el('div', { class: 'fgroup' }, [
          el('span', { class: 'glabel', text: 'Aderência' }),
          el('select', { class: 'fselect', id: 'f-ader-grau' }, [
            el('option', { value: 'all', text: 'Todos' }),
            el('option', { value: 'alta', text: 'Alta' }),
            el('option', { value: 'media', text: 'Média' }),
            el('option', { value: 'baixa', text: 'Baixa' }),
          ]),
        ]),
        el('div', { class: 'fgroup' }, [
          el('span', { class: 'glabel', text: 'Buscar' }),
          el('input', { class: 'fsearch', id: 'search-aderencia', type: 'text', placeholder: 'Digite para buscar…' }),
        ]),
      ]),
      el('span', { class: 'fcount', id: 'count-aderencia' }),
    ]);

    return el('section', { class: 'doc', id: 'aderencia' }, [
      el('div', { class: 'wrap' }, [
        el('div', { class: 'sec-head' }, [
          el('h2', { text: 'Aderência com os institutos SENAI - MS' }),
          el('p', { text: 'Avaliados apenas Aberto + Em breve. Classificação por grau de aderência aos três institutos — IST Alimentos e Bebidas (Dourados), IST Eficiência Operacional (Campo Grande) e ISI Biomassa (Três Lagoas | Unidade Embrapii).' }),
        ]),
        filterBar,
        specCard,
      ]),
    ]);
  }

  /* ========== Não Confirmado ========== */
  function naoConfirmadoSection(data) {
    const headers = ['Edital', 'Fonte', 'Motivo', 'Link'];
    const thead = el('thead', {}, [el('tr', {}, headers.map(h => el('th', { text: h })))]);
    const tbody = el('tbody', {});
    const links = {
      'FAPERJ nº 07/2026 – Agro do Futuro': 'https://www.faperj.br/rp/downloads/Edital_FAPERJ_N%C2%BA07_2026_Programa_Agro_do_Futuro_%E2%80%93_Tecnologia_e_Soberania_Alimentar_%28Foodtechs_e_Agritechs%29.pdf',
      'MCTI/FINEP – Conhecimento Brasil (R$ 500 mi)': 'https://www.finep.gov.br/chamadas-publicas/chamadapublica/745',
      'FUNDECT-MS nº 01/2026 – Centelha MS (3ª edição)': 'https://www.fundect.ms.gov.br/wp-content/uploads/2026/03/Programa-Centelha-3-MS.pdf',
      'InovAtiva Brasil 2026 (2º semestre)': 'https://www.gov.br/mdic/pt-br/acesso-a-informacao/perguntas-frequentes-faq/secretaria-de-desenvolvimento-industrial-inovacao-comercio-e-servicos/quem-pode-se-inscrever-e',
    };
    data.nao_confirmado.forEach(n => {
      const link = n.link || links[n.edital] || '';
      tbody.appendChild(el('tr', {}, [
        el('td', { class: 'edital', text: n.edital }),
        el('td', { class: 'src', text: n.fonte }),
        el('td', { text: n.motivo }),
        el('td', {}, link ? [el('a', { class: 'link', href: link, target: '_blank', rel: 'noopener', text: 'Link' })] : []),
      ]));
    });
    const table = el('table', {}, [thead, tbody]);
    const specCard = el('div', { class: 'spec-card' }, [el('div', { class: 'tbl-wrap' }, [table])]);

    return el('section', { class: 'doc', id: 'nao-confirmado' }, [
      el('div', { class: 'wrap' }, [
        el('div', { class: 'sec-head' }, [
          el('h2', { text: 'Editais Não Confirmados' }),
        ]),
        specCard,
      ]),
    ]);
  }

  /* ========== Build full page ========== */
  function build(data) {
    // Nav links
    const nav = document.querySelector('.docnav nav');
    if (nav) {
      nav.innerHTML = '';
      [['#novidades', 'Novidades'], ['#resumo', 'Resumo'], ['#aderencia', 'Aderência SENAI'], ['#editais', 'Editais'], ['#nao-confirmado', 'Não confirmado']].forEach(([href, label], i) => {
        const a = el('a', { href, text: label });
        if (i === 0) a.classList.add('active');
        nav.appendChild(a);
      });
    }

    // Hero / Cover
    const header = document.querySelector('header.cover');
    if (header) header.remove();
    const navEl = document.querySelector('.docnav');
    if (navEl) navEl.insertAdjacentElement('afterend', hero(data));

    // Main content
    const main = document.querySelector('main');
    if (!main) return;
    main.innerHTML = '';

    const wrap1 = el('div', { class: 'wrap' }, [stats(data.stats)]);
    
    // Adiciona novidades antes do resumo executivo
    const novidadesEl = novidades(data);
    if (novidadesEl) {
      wrap1.appendChild(novidadesEl);
    }
    
    wrap1.appendChild(resumo(data));
    main.appendChild(wrap1);

    main.appendChild(aderenciaSection(data));
    main.appendChild(editaisSection(data));
    main.appendChild(naoConfirmadoSection(data));
  }

  return { build, statusPill, gradeBadge, diasClass, el };
})();
