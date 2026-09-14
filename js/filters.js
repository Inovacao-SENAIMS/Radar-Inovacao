/* filters.js — filter logic for editais and aderencia tables */
const Filters = (() => {

  const PAGE_SIZE = 7;

  function paginate(total, page, pageSize = PAGE_SIZE) {
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    const safePage = Math.min(Math.max(1, page), totalPages);
    return {
      start: Math.min((safePage - 1) * pageSize, total),
      end: Math.min(safePage * pageSize, total),
      totalPages,
    };
  }

  function updatePagination(id, total, page, onPageChange, pageSize = PAGE_SIZE) {
    const container = document.getElementById(id);
    if (!container) return;
    const range = paginate(total, page, pageSize);
    container.innerHTML = '';
    container.hidden = total <= pageSize;
    if (container.hidden) return;

    const previous = document.createElement('button');
    previous.type = 'button';
    previous.className = 'pagination__button';
    previous.textContent = 'Anterior';
    previous.disabled = page <= 1;
    previous.addEventListener('click', () => onPageChange(page - 1));

    const status = document.createElement('span');
    status.className = 'pagination__status';
    status.textContent = 'Página ' + page + ' de ' + range.totalPages;
    status.setAttribute('aria-live', 'polite');

    const next = document.createElement('button');
    next.type = 'button';
    next.className = 'pagination__button';
    next.textContent = 'Próxima';
    next.disabled = page >= range.totalPages;
    next.addEventListener('click', () => onPageChange(page + 1));

    container.append(previous, status, next);
  }

  function setupNovidades() {
    const cards = Array.from(document.querySelectorAll('#novidades .nov-card'));
    if (!cards.length) return;
    const pageSize = 9;
    let currentPage = 1;

    function apply() {
      const page = paginate(cards.length, currentPage, pageSize);
      currentPage = Math.min(currentPage, page.totalPages);
      cards.forEach((card, index) => {
        card.hidden = index < page.start || index >= page.end;
      });
      updatePagination('pagination-novidades', cards.length, currentPage, pageNumber => {
        currentPage = pageNumber;
        apply();
      }, pageSize);
    }

    apply();
  }

  function normalizeText(value) {
    return String(value || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/\s+/g, ' ')
      .trim();
  }

  /* ========== Institute mapping (matches by substring in edital name) ========== */
  const mapInst = {
    'Agroindustriais Sustentáveis': ['alimentos', 'biomassa'],
    'Tecnologias Digitais': ['eficiencia'],
    'Transição Energética': ['biomassa', 'eficiencia'],
    'Saúde': [],
    'Economia Circular': ['biomassa', 'eficiencia'],
    'Mobilidade Sustentável': ['eficiencia'],
    'Transformação Mineral': ['eficiencia'],
    'Base Industrial de Defesa': ['eficiencia'],
    'Semicondutores': ['eficiencia'],
    'Biotecnologia': ['biomassa', 'alimentos'],
    'Atlânticas': [],
    'Eventos de Empreendedorismo': [],
    'PAE-MS': [],
    'Centelha 3 RJ': [],
    'Eurostars': ['eficiencia', 'bmassa'],
    'FAPESP PIPE': ['eficiencia', 'biomassa'],
    'SC Inovadora': [],
    'British Council': [],
    'RAMP': ['eficiencia', 'biomassa'],
    'Ohio State': ['eficiencia', 'biomassa'],
    'PICTEC': [],
    'Agroindustriais': ['alimentos', 'biomassa'],
    'Spain-CDTI': ['eficiencia', 'biomassa'],
    'PRONEX': ['eficiencia', 'biomassa'],
    'Desafios da Amazônia': ['biomassa'],
    'ProÁfrica': [],
    'Tecnova': ['todos'],
    'BNDES Mais Inovação': ['todos'],
    'EMBRAPII': ['todos'],
    'Agricultura Familiar': ['todos'],
    'Saúde Digital': [],
    'Water4All': ['biomassa'],
    'Biodiversa+': ['biomassa'],
    'Sustainable Blue Economy': [],
    'Induz': ['eficiencia', 'biomassa'],
    'Carbon Pricing': ['eficiencia', 'biomassa'],
    'FACEPE': ['eficiencia', 'biomassa']
  };

  function instOf(name) {
    for (const k in mapInst) {
      if (name.indexOf(k) >= 0) return mapInst[k];
    }
    return [];
  }

  function diasBucket(txt) {
    if (!txt) return 'cont';
    const t = txt.trim().toLowerCase();
    if (t.includes('—') || t.includes('contínuo')) return 'cont';
    const m = t.match(/\d+/);
    if (!m) return 'cont';
    const d = parseInt(m[0], 10);
    if (d <= 7) return 'd7';
    if (d <= 30) return 'd30';
    if (d <= 60) return 'd60';
    return 'd60p';
  }

  function populate(sel, idx, rows) {
    if (!sel) return;
    const vals = new Set();
    rows.forEach(tr => {
      const v = tr.children[idx]?.textContent.trim();
      if (v) vals.add(v);
    });
    Array.from(vals).sort((a, b) => a.localeCompare(b, 'pt-BR')).forEach(v => {
      const o = document.createElement('option');
      o.value = v;
      o.textContent = v.length > 34 ? v.slice(0, 32) + '…' : v;
      o.title = v;
      sel.appendChild(o);
    });
  }

  /* ========== Aderência filter (dropdown selects) ========== */
  function setupAderencia() {
    const tbl = document.getElementById('tbl-aderencia');
    if (!tbl) return;
    const selInst = document.getElementById('f-ader-inst');
    const selFoco = document.getElementById('f-ader-foco');
    const selGrau = document.getElementById('f-ader-grau');
    const search = document.getElementById('search-aderencia');
    const count = document.getElementById('count-aderencia');
    const cardsWrap = document.getElementById('cards-aderencia');
    let currentPage = 1;
    const rows = tbl ? Array.from(tbl.querySelectorAll('tbody tr')) : [];

    // Keywords to match each institute (partial matching)
    const instMap = {
      'IST Alimentos e Bebidas': ['IST Alimentos', 'Alimentos e Bebidas'],
      'IST Eficiência Operacional': ['IST Eficiência', 'Eficiência Operacional'],
      'ISI Biomassa': ['ISI Biomassa']
    };

    function matchRow(tr) {
      const vInst = selInst?.value || 'all';
      const vFoco = selFoco?.value || 'all';
      const vGrau = selGrau?.value || 'all';
      const q = (search?.value || '').trim().toLowerCase();

      if (vInst !== 'all') {
        const instCell = normalizeText(tr.children[1]?.textContent);
        const keywords = (instMap[vInst] || [vInst]).map(normalizeText);
        if (!keywords.some(kw => instCell.includes(kw))) return false;
      }
      if (vFoco !== 'all') {
        const focoCell = tr.children[3]?.textContent.trim() || '';
        if (vFoco === 'Sim' && !focoCell.startsWith('Sim')) return false;
        if (vFoco === 'Não' && focoCell !== 'Não') return false;
      }
      if (vGrau !== 'all' && tr.dataset.g !== vGrau) return false;
      if (q && !tr.textContent.toLowerCase().includes(q)) return false;
      return true;
    }

    function matchRowExcluding(tr, excludeKey) {
      const q = (search?.value || '').trim().toLowerCase();
      if (excludeKey !== 'inst') {
        const vInst = selInst?.value || 'all';
        if (vInst !== 'all') {
          const instCell = normalizeText(tr.children[1]?.textContent);
          const keywords = (instMap[vInst] || [vInst]).map(normalizeText);
          if (!keywords.some(kw => instCell.includes(kw))) return false;
        }
      }
      if (excludeKey !== 'foco') {
        const vFoco = selFoco?.value || 'all';
        if (vFoco !== 'all') {
          const focoCell = tr.children[3]?.textContent.trim() || '';
          if (vFoco === 'Sim' && !focoCell.startsWith('Sim')) return false;
          if (vFoco === 'Não' && focoCell !== 'Não') return false;
        }
      }
      if (excludeKey !== 'grau') {
        const vGrau = selGrau?.value || 'all';
        if (vGrau !== 'all' && tr.dataset.g !== vGrau) return false;
      }
      if (q && !tr.textContent.toLowerCase().includes(q)) return false;
      return true;
    }

    // Only repopulate Foco and Grau (Inst stays fixed with 3 options)
    function repopulateFoco() {
      if (!selFoco) return;
      const prev = selFoco.value;
      const vals = new Set();
      rows.forEach(tr => {
        if (!matchRowExcluding(tr, 'foco')) return;
        const v = tr.children[3]?.textContent.trim();
        if (v) vals.add(v);
      });
      selFoco.innerHTML = '';
      const first = document.createElement('option'); first.value = 'all'; first.textContent = 'Todos';
      selFoco.appendChild(first);
      Array.from(vals).sort((a,b)=>a.localeCompare(b,'pt-BR')).forEach(v => {
        const o = document.createElement('option'); o.value = v; o.textContent = v.length > 40 ? v.slice(0,38)+'…' : v; o.title = v;
        selFoco.appendChild(o);
      });
      if (prev && [...vals].includes(prev)) selFoco.value = prev; else selFoco.value = 'all';
    }

    function repopulateGrau() {
      if (!selGrau) return;
      const prev = selGrau.value;
      const vals = new Set();
      const labels = { alta: 'Alta', media: 'Média', baixa: 'Baixa' };
      rows.forEach(tr => {
        if (!matchRowExcluding(tr, 'grau')) return;
        const g = tr.dataset.g;
        if (labels[g]) vals.add(g);
      });
      selGrau.innerHTML = '';
      const first = document.createElement('option'); first.value = 'all'; first.textContent = 'Todos';
      selGrau.appendChild(first);
      Array.from(vals).sort().forEach(v => {
        const o = document.createElement('option'); o.value = v; o.textContent = labels[v] || v;
        selGrau.appendChild(o);
      });
      if (prev && [...vals].includes(prev)) selGrau.value = prev; else selGrau.value = 'all';
    }

    function repopulateAll() { repopulateFoco(); repopulateGrau(); }

    function apply(resetPage = true) {
      if (resetPage) currentPage = 1;
      const matchingRows = rows.filter(matchRow);
      const page = paginate(matchingRows.length, currentPage);
      currentPage = Math.min(currentPage, page.totalPages);
      const pageRows = new Set(matchingRows.slice(page.start, page.end));
      rows.forEach((tr, i) => {
        const show = pageRows.has(tr);
        tr.classList.toggle('hidden', !show);
        const card = cardsWrap?.children[i];
        if (card) card.style.display = matchingRows.includes(tr) && show ? '' : 'none';
      });
      repopulateAll();
      if (count) count.textContent = matchingRows.length + ' de ' + rows.length + ' editais aderentes';
      updatePagination('pagination-aderencia', matchingRows.length, currentPage, pageNumber => {
        currentPage = pageNumber;
        apply(false);
      });
    }

    [selInst, selFoco, selGrau].forEach(s => s && s.addEventListener('change', apply));
    if (search) search.addEventListener('input', apply);
    repopulateAll();
    apply();
  }

  /* ========== Editais filter (com dependência entre filtros) ========== */
  function setupEditais() {
    const tbl = document.getElementById('tbl-editais');
    if (!tbl) return;
    const rows = Array.from(tbl.querySelectorAll('tbody tr'));
    const search = document.getElementById('search-editais');
    const count = document.getElementById('count-editais');
    const cardsWrap = document.getElementById('cards-editais');
    let currentPage = 1;

    function matchRow(tr) {
      const q = (search?.value || '').trim().toLowerCase();
      if (q && !tr.textContent.toLowerCase().includes(q)) return false;
      return true;
    }

    function apply(resetPage = true) {
      if (resetPage) currentPage = 1;
      const matchingRows = rows.filter(matchRow);
      const page = paginate(matchingRows.length, currentPage);
      currentPage = Math.min(currentPage, page.totalPages);
      const pageRows = new Set(matchingRows.slice(page.start, page.end));
      rows.forEach((tr, i) => {
        const show = pageRows.has(tr);
        tr.classList.toggle('hidden', !show);
        const card = cardsWrap?.children[i];
        if (card) card.style.display = matchingRows.includes(tr) && show ? '' : 'none';
      });
      const label = matchingRows.length + ' de ' + rows.length + ' editais';
      if (count) count.textContent = label;
      updatePagination('pagination-editais', matchingRows.length, currentPage, pageNumber => {
        currentPage = pageNumber;
        apply(false);
      });
    }

    if (search) search.addEventListener('input', apply);
    apply();
  }

  return { setupNovidades, setupAderencia, setupEditais, instOf, diasBucket, paginate };
})();
