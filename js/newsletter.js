/* newsletter.js — seção "Assine a newsletter": formulário (nome, e-mail, consentimento LGPD)
   + integração opcional com Web App do Apps Script (arquitetura 100% Google — ver PRD.md).
   Sem backend configurado → fallback mailto: para NEWSLETTER_CONFIG.contactEmail. */
const Newsletter = (() => {

  const CFG = window.NEWSLETTER_CONFIG || {};

  /* ========== Helpers ========== */
  function show(root, kind, msg) {
    const status = root.querySelector('#nl-status');
    if (!status) return;
    status.className = 'nl-status nl-status--' + kind;
    status.textContent = msg;
    status.hidden = false;
  }

  function validEmail(v) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
  }

  /* ========== Form logic ========== */
  function wire(root) {
    if (!root) return;
    const form = root.querySelector('#nl-form');
    if (!form || form.dataset.wired === '1') return;
    form.dataset.wired = '1';

    let timer = null;

    /* Resposta do Apps Script (postMessage vindo do iframe oculto) */
    window.addEventListener('message', e => {
      if (!e.data || e.data.type !== 'nl-result') return;
      clearTimeout(timer);
      if (e.data.ok) {
        show(root, 'ok', e.data.msg || 'Parabéns, agora você receberá as nossas atualizações frequentes, fique de olho no e-mail.');
        form.reset();
      } else {
        show(root, 'err', e.data.msg || 'Não foi possível concluir a assinatura. Tente novamente.');
      }
      const btn = form.querySelector('.nl-btn');
      if (btn) btn.disabled = false;
    });

    form.addEventListener('submit', ev => {
      const nome = (form.querySelector('#nl-nome')?.value || '').trim();
      const email = (form.querySelector('#nl-email')?.value || '').trim();
      const consent = form.querySelector('#nl-consent')?.checked;

      if (!nome) { ev.preventDefault(); show(root, 'err', 'Informe seu nome.'); return; }
      if (!validEmail(email)) { ev.preventDefault(); show(root, 'err', 'Informe um e-mail válido.'); return; }
      if (!consent) { ev.preventDefault(); show(root, 'err', 'É necessário consentir com o envio dos e-mails.'); return; }

      /* Sem backend configurado → fallback mailto */
      if (!CFG.webappUrl) {
        ev.preventDefault();
        if (CFG.contactEmail) {
          const subject = encodeURIComponent('Assinatura — Newsletter Radar de Editais SENAI MS');
          const body = encodeURIComponent(
            'Olá!\n\nGostaria de assinar a newsletter de atualizações dos editais de inovação.\n\n' +
            'Nome: ' + nome + '\nE-mail: ' + email + '\n\n(Envie este e-mail para concluir a assinatura.)'
          );
          show(root, 'ok', 'Seu cliente de e-mail foi aberto — basta enviar a mensagem para concluir a assinatura.');
          window.location.href = 'mailto:' + CFG.contactEmail + '?subject=' + subject + '&body=' + body;
        } else {
          show(root, 'err', 'Assinaturas temporariamente indisponíveis. Tente novamente mais tarde.');
        }
        return;
      }

      /* POST nativo → iframe oculto (sem CORS; funciona em file:// e GitHub Pages) */
      form.action = CFG.webappUrl;
      const btn = form.querySelector('.nl-btn');
      if (btn) btn.disabled = true;
      show(root, 'pending', 'Enviando…');
      clearTimeout(timer);
      timer = setTimeout(() => {
        show(root, 'ok',
          'Recebemos sua solicitação. Se os dados estiverem corretos, você receberá um e-mail de confirmação em instantes — verifique também a caixa de spam.');
        const b = form.querySelector('.nl-btn');
        if (b) b.disabled = false;
      }, 12000);
    });
  }

  /* ========== Section builder ========== */
  function build() {
    const form = Render.el('form', { class: 'nl-form', id: 'nl-form', method: 'POST', target: 'nl-frame', novalidate: 'true' }, [
      Render.el('input', { type: 'text', name: 'website', class: 'nl-hp', value: '', tabindex: '-1', autocomplete: 'off', 'aria-hidden': 'true' }),
      Render.el('div', { class: 'nl-grid' }, [
        Render.el('label', { class: 'nl-field' }, [
          Render.el('span', { class: 'glabel', text: 'Nome' }),
          Render.el('input', { class: 'nl-input', id: 'nl-nome', name: 'nome', type: 'text', maxlength: '80', autocomplete: 'name', placeholder: 'Seu nome' }),
        ]),
        Render.el('label', { class: 'nl-field' }, [
          Render.el('span', { class: 'glabel', text: 'E-mail' }),
          Render.el('input', { class: 'nl-input', id: 'nl-email', name: 'email', type: 'email', maxlength: '120', autocomplete: 'email', placeholder: 'voce@empresa.com.br', inputmode: 'email' }),
        ]),
      ]),
      Render.el('label', { class: 'nl-check' }, [
        Render.el('input', { type: 'checkbox', id: 'nl-consent', name: 'consentimento', value: 'sim' }),
        Render.el('span', {}, [
          document.createTextNode('Concordo em receber e-mails de atualização dos editais de inovação do SENAI MS e sei que posso cancelar a qualquer momento.'),
        ]),
      ]),
      Render.el('button', { class: 'nl-btn', type: 'submit', text: 'Assinar a newsletter' }),
    ]);

    const card = Render.el('div', { class: 'spec-card nl-card' }, [
      form,
      Render.el('div', { class: 'nl-status', id: 'nl-status', hidden: 'true', role: 'status', 'aria-live': 'polite' }),
      Render.el('iframe', { id: 'nl-frame', name: 'nl-frame', style: 'display:none', tabindex: '-1', 'aria-hidden': 'true', title: 'Destino do formulário' }),
    ]);

    return Render.el('section', { class: 'doc', id: 'newsletter' }, [
      Render.el('div', { class: 'wrap' }, [
        Render.el('div', { class: 'sec-head' }, [
          Render.el('h2', { id: 'nl-modal-title', text: 'Receba as novidades por e-mail' }),
          Render.el('p', { text: 'Assine e receba um resumo com os novos editais, prazos alterados e alertas de encerramento sempre que houver uma atualização do radar — direto na sua caixa de entrada.' }),
        ]),
        card,
        Render.el('p', { class: 'note nl-consent-note' }, [
          Render.el('b', { text: 'Seus dados:' }),
          document.createTextNode(' usamos nome e e-mail exclusivamente para o envio destas atualizações, com consentimento e confirmação por e-mail (dupla verificação), conforme a LGPD (Lei nº 13.709/2018). O cancelamento está disponível em todas as mensagens.'),
        ]),
      ]),
    ]);
  }

  /* ========== Mount (páginas dinâmicas — chamado por app.js após Render.build) ========== */
  function mount() {
    const existing = document.getElementById('newsletter');
    if (existing) { wire(existing); setupModal(existing); return; }
    const main = document.querySelector('main');
    if (!main) return;
    const wrap = main.querySelector('.wrap');
    const sec = build();
    if (wrap) wrap.appendChild(sec);
    else main.appendChild(sec);
    wire(sec);
    setupModal(sec);
  }

  function setupModal(section) {
    if (!section || section.dataset.modalReady === '1') return;
    section.dataset.modalReady = '1';
    const cta = document.querySelector('.newsletter-cta');
    if (!cta) return;

    const modal = document.createElement('div');
    modal.className = 'nl-modal';
    modal.id = 'nl-modal';
    modal.hidden = true;
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'nl-modal-title');

    const panel = document.createElement('div');
    panel.className = 'nl-modal__panel';
    const close = document.createElement('button');
    close.className = 'nl-modal__close';
    close.type = 'button';
    close.setAttribute('aria-label', 'Fechar newsletter');
    close.textContent = '×';
    panel.append(close, section);
    modal.appendChild(panel);
    document.body.appendChild(modal);

    const open = ev => {
      ev.preventDefault();
      modal.hidden = false;
      document.body.classList.add('nl-modal-open');
      close.focus();
    };
    const dismiss = () => {
      modal.hidden = true;
      document.body.classList.remove('nl-modal-open');
      cta.focus();
    };
    cta.addEventListener('click', open);
    close.addEventListener('click', dismiss);
    modal.addEventListener('click', ev => { if (ev.target === modal) dismiss(); });
    document.addEventListener('keydown', ev => {
      if (ev.key === 'Escape' && !modal.hidden) dismiss();
    });
  }

  /* ========== Self-init (HTML estático gerado por render_static.py) ========== */
  document.addEventListener('DOMContentLoaded', () => {
    const existing = document.getElementById('newsletter');
    if (existing) { wire(existing); setupModal(existing); }
  });

  return { mount, build, wire };
})();

// app.js acessa o módulo pelo objeto global após o carregamento dos scripts.
window.Newsletter = Newsletter;
