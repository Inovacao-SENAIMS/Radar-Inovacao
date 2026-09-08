/* app.js — entry point: loads data, builds UI, wires interactions */
document.addEventListener('DOMContentLoaded', () => {

  /* ========== Scroll spy ========== */
  const navLinks = document.querySelectorAll('.docnav nav a');
  const sectionIds = ['novidades', 'resumo', 'newsletter', 'aderencia', 'editais', 'nao-confirmado'];
  function spy() {
    const y = window.scrollY + 90;
    let active = sectionIds[0];
    sectionIds.forEach(id => {
      const el = document.getElementById(id);
      if (el && el.offsetTop <= y) active = id;
    });
    document.querySelectorAll('.docnav nav a').forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + active));
  }
  window.addEventListener('scroll', spy, { passive: true });

  /* ========== Nav toggle (mobile) ========== */
  const navToggle = document.getElementById('nav-toggle');
  const navMenu = document.getElementById('nav-menu');
  function closeNav() {
    if (navMenu) navMenu.classList.remove('open');
    if (navToggle) { navToggle.classList.remove('open'); navToggle.setAttribute('aria-expanded', 'false'); }
  }
  function toggleNav() {
    if (!navMenu || !navToggle) return;
    if (navMenu.classList.contains('open')) closeNav();
    else { navMenu.classList.add('open'); navToggle.classList.add('open'); navToggle.setAttribute('aria-expanded', 'true'); }
  }
  if (navToggle) navToggle.addEventListener('click', e => { e.stopPropagation(); toggleNav(); });
  document.addEventListener('click', e => {
    if (navMenu?.classList.contains('open') && !navMenu.contains(e.target) && !navToggle.contains(e.target)) closeNav();
  });

  /* ========== Drawer (filtros editais) ========== */
  const backdrop = document.getElementById('drawer-backdrop');
  const sidebar = document.getElementById('sidebar');
  const fab = document.getElementById('fab-filtros');
  const drawerClose = document.getElementById('drawer-close');

  function isMobileDrawer() { return window.innerWidth <= 1100; }

  function openDrawer() {
    if (!sidebar) return;
    sidebar.classList.add('open');
    if (backdrop) backdrop.classList.add('open');
    if (fab) fab.setAttribute('aria-expanded', 'true');
    if (isMobileDrawer()) document.body.style.overflow = 'hidden';
  }
  function closeDrawer() {
    if (!sidebar) return;
    sidebar.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
    if (fab) fab.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }

  if (fab) fab.addEventListener('click', () => sidebar?.classList.contains('open') ? closeDrawer() : openDrawer());
  if (drawerClose) drawerClose.addEventListener('click', closeDrawer);
  if (backdrop) backdrop.addEventListener('click', () => { closeDrawer(); closeNav(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') { closeDrawer(); closeNav(); } });
  window.addEventListener('resize', () => {
    if (window.innerWidth > 1100) { if (backdrop) backdrop.classList.remove('open'); document.body.style.overflow = ''; }
    if (window.innerWidth > 760) closeNav();
  });

  /* ========== Build cards for mobile (from rendered table rows) ========== */
  function buildCards(tblId, cardsId, headers) {
    const tbl = document.getElementById(tblId);
    const wrap = document.getElementById(cardsId);
    if (!tbl || !wrap) return;
    wrap.innerHTML = '';
    const rows = tbl.querySelectorAll('tbody tr');
    rows.forEach((tr, idx) => {
      const tds = Array.from(tr.children);
      const card = document.createElement('div');
      card.className = 'tbl-card';
      card.dataset.idx = idx;
      if (tr.dataset.s) card.dataset.s = tr.dataset.s;
      if (tr.dataset.g) card.dataset.g = tr.dataset.g;

      const head = document.createElement('div');
      head.className = 'tbl-card__head';
      const title = document.createElement('div');
      title.className = 'tbl-card__title';
      title.textContent = tds[0]?.textContent.trim() || '';
      head.appendChild(title);
      const badgeSlot = document.createElement('div');
      const pill = tds[2]?.querySelector('.pill');
      const grade = tds[2]?.querySelector('.g');
      if (pill) badgeSlot.appendChild(pill.cloneNode(true));
      else if (grade) badgeSlot.appendChild(grade.cloneNode(true));
      head.appendChild(badgeSlot);
      card.appendChild(head);

      const grid = document.createElement('div');
      grid.className = 'tbl-card__grid';
      for (let i = 1; i < tds.length; i++) {
        if (i === 2) continue;
        const isLink = (i === tds.length - 1 && tds[i]?.querySelector('a'));
        const field = document.createElement('div');
        field.className = 'tbl-card__field' + (isLink ? ' tbl-card__full tbl-card__link' : (i >= tds.length - 3 ? ' tbl-card__full' : ''));
        if (isLink) {
          const a = tds[i].querySelector('a');
          if (a) {
            const clone = a.cloneNode(true);
            clone.textContent = 'Abrir edital ↗';
            field.appendChild(clone);
          }
        } else {
          const label = document.createElement('span');
          label.className = 'tbl-card__label';
          label.textContent = headers[i] || '';
          const value = document.createElement('span');
          value.className = 'tbl-card__value';
          value.textContent = tds[i]?.textContent.trim() || '—';
          field.appendChild(label);
          field.appendChild(value);
        }
        grid.appendChild(field);
      }
      card.appendChild(grid);
      wrap.appendChild(card);
    });
  }

  /* ========== Init: render from embedded data ========== */
  function init(data) {
    Render.build(data);

    // re-bind nav links (DOM was replaced)
    document.querySelectorAll('.docnav nav a').forEach(a => a.addEventListener('click', closeNav));

    // build mobile cards
    const editaisHeaders = ['Edital', 'Fonte', 'Status', 'Abertura', 'Encerramento', 'Dias', 'Público-alvo', 'Valor / Faixa', 'Contrapartida', 'Principais exigências', 'Link'];
    const aderenciaHeaders = ['Edital', 'Instituto(s) com maior aderência', 'Grau', 'Foco educacional?', 'Justificativa'];
    buildCards('tbl-editais', 'cards-editais', editaisHeaders);
    buildCards('tbl-aderencia', 'cards-aderencia', aderenciaHeaders);

    // setup filters
    Filters.setupAderencia();
    Filters.setupEditais();

    // newsletter section (formulário de assinatura)
    if (window.Newsletter) Newsletter.mount();

    // scroll spy
    spy();
  }

  /* ========== Load data: embedded (file://) or fetch (http://) ========== */
  if (window.EDITAIS_DATA) {
    // Dados embutidos via <script src="data/editais.js">
    init(window.EDITAIS_DATA);
  } else {
    // Fallback: fetch via HTTP
    fetch('data/editais.json')
      .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(data => init(data))
      .catch(err => {
        console.error('Falha ao carregar dados:', err);
        const main = document.querySelector('main');
        if (main) main.innerHTML = '<div class="wrap"><div class="callout">Erro ao carregar dados. Verifique se data/editais.js existe ou sirva via HTTP.<br><small>' + err.message + '</small></div></div>';
      });
  }
});
