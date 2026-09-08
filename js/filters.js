/* filters.js — filter logic for editais and aderencia tables */
const Filters = (() => {

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
        const instCell = tr.children[1]?.textContent || '';
        const keywords = instMap[vInst] || [vInst];
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
          const instCell = tr.children[1]?.textContent || '';
          const keywords = instMap[vInst] || [vInst];
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

    function apply() {
      let vis = 0;
      rows.forEach((tr, i) => {
        const show = matchRow(tr);
        tr.classList.toggle('hidden', !show);
        const card = cardsWrap?.children[i];
        if (card) card.style.display = show ? '' : 'none';
        if (show) vis++;
      });
      repopulateAll();
      if (count) count.textContent = vis + ' de ' + rows.length + ' editais aderentes';
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
    const selInst = document.getElementById('f-inst');
    const selStatus = document.getElementById('f-status');
    const selTipo = document.getElementById('f-tipo');
    const selFonte = document.getElementById('f-fonte');
    const selPublico = document.getElementById('f-publico');
    const selContra = document.getElementById('f-contra');
    const selDias = document.getElementById('f-dias');
    const search = document.getElementById('search-editais');
    const count = document.getElementById('count-editais');
    const countTop = document.getElementById('count-editais-top');
    const fabBadge = document.getElementById('fab-badge');
    const cardsWrap = document.getElementById('cards-editais');

    // Column index map for each select
    const colMap = { inst: -1, status: -2, tipo: -3, fonte: 1, publico: 7, contra: 8, dias: 5 };
    const allSels = [selInst, selStatus, selTipo, selFonte, selPublico, selContra, selDias];
    const selKeys = ['inst', 'status', 'tipo', 'fonte', 'publico', 'contra', 'dias'];

    function matchRow(tr, excludeKey) {
      const vInst = (selInst?.value || 'all');
      const vStatus = (selStatus?.value || 'all');
      const vTipo = (selTipo?.value || 'all');
      const vFonte = (selFonte?.value || 'all');
      const vPub = (selPublico?.value || 'all');
      const vContra = (selContra?.value || 'all');
      const vDias = (selDias?.value || 'all');
      const q = (search?.value || '').trim().toLowerCase();

      if (excludeKey !== 'inst') {
        const name = tr.querySelector('.edital')?.textContent || '';
        const inst = instOf(name);
        if (vInst !== 'all' && !inst.includes(vInst) && !inst.includes('todos')) return false;
      }
      if (excludeKey !== 'status' && vStatus !== 'all' && tr.dataset.s !== vStatus) return false;
      if (excludeKey !== 'tipo' && vTipo !== 'all' && tr.dataset.tipo !== vTipo) return false;
      if (excludeKey !== 'fonte' && vFonte !== 'all' && tr.children[1]?.textContent.trim() !== vFonte) return false;
      if (excludeKey !== 'publico' && vPub !== 'all' && tr.children[7]?.textContent.trim() !== vPub) return false;
      if (excludeKey !== 'contra' && vContra !== 'all' && tr.children[8]?.textContent.trim() !== vContra) return false;
      if (excludeKey !== 'dias' && vDias !== 'all' && diasBucket(tr.children[5]?.textContent) !== vDias) return false;
      if (q && !tr.textContent.toLowerCase().includes(q)) return false;
      return true;
    }

    function repopulateSelect(sel, key, colIdx) {
      if (!sel) return;
      const vals = new Set();
      const prev = sel.value;
      rows.forEach(tr => {
        if (!matchRow(tr, key)) return;
        let v;
        if (key === 'inst') {
          const name = tr.querySelector('.edital')?.textContent || '';
          const insts = instOf(name);
          insts.forEach(i => { if (i !== 'todos') vals.add(i); });
        } else if (key === 'status') {
          v = tr.dataset.s; if (v) vals.add(v);
        } else if (key === 'tipo') {
          v = tr.dataset.tipo; if (v) vals.add(v);
        } else if (key === 'dias') {
          v = diasBucket(tr.children[5]?.textContent); if (v) vals.add(v);
        } else {
          v = tr.children[colIdx]?.textContent.trim(); if (v) vals.add(v);
        }
      });
      // rebuild options
      const first = sel.querySelector('option');
      sel.innerHTML = '';
      sel.appendChild(first);
      const labels = { inst: { alimentos: 'IST Alimentos e Bebidas', eficiencia: 'IST Eficiência Operacional', biomassa: 'ISI Biomassa' }, status: { aberto: 'Aberto', breve: 'Em breve', continuo: 'Fluxo contínuo' }, tipo: { 'Empresa': 'Empresa', 'Pessoa Física': 'Pessoa Física' }, dias: { d7: '≤ 7 dias', d30: '8–30 dias', d60: '31–60 dias', d60p: '> 60 dias', cont: 'Contínuo' } };
      Array.from(vals).sort((a,b)=>a.localeCompare(b,'pt-BR')).forEach(v => {
        const o = document.createElement('option');
        o.value = v;
        o.textContent = (labels[key] && labels[key][v]) || (v.length > 40 ? v.slice(0,38)+'…' : v);
        o.title = v;
        sel.appendChild(o);
      });
      // restore previous value if still valid
      if (prev && [...vals].includes(prev)) sel.value = prev;
      else sel.value = 'all';
    }

    function repopulateAll() {
      repopulateSelect(selInst, 'inst', -1);
      repopulateSelect(selStatus, 'status', -2);
      repopulateSelect(selTipo, 'tipo', -3);
      repopulateSelect(selFonte, 'fonte', 1);
      repopulateSelect(selPublico, 'publico', 7);
      repopulateSelect(selContra, 'contra', 8);
      repopulateSelect(selDias, 'dias', 5);
    }

    function countActive() {
      let n = 0;
      allSels.forEach(s => { if (s && s.value !== 'all') n++; });
      if (search && search.value.trim() !== '') n++;
      return n;
    }

    function apply() {
      let vis = 0;
      rows.forEach((tr, i) => {
        const show = matchRow(tr, null);
        tr.classList.toggle('hidden', !show);
        const card = cardsWrap?.children[i];
        if (card) card.style.display = show ? '' : 'none';
        if (show) vis++;
      });
      repopulateAll();
      const label = vis + ' de ' + rows.length + ' editais';
      if (count) count.textContent = label;
      if (countTop) countTop.textContent = label;
      const active = countActive();
      if (fabBadge) {
        if (active > 0) { fabBadge.textContent = active; fabBadge.hidden = false; }
        else fabBadge.hidden = true;
      }
    }

    allSels.forEach(s => s && s.addEventListener('change', apply));
    if (search) search.addEventListener('input', apply);
    const reset = document.getElementById('f-reset');
    if (reset) reset.addEventListener('click', () => {
      allSels.forEach(s => { if (s) s.value = 'all'; });
      if (search) search.value = '';
      apply();
    });
    repopulateAll();
    apply();
  }

  return { setupAderencia, setupEditais, instOf, diasBucket };
})();
