/* data/newsletter.js — Configuração da newsletter (editar aqui)
   Ver PRD.md § "Configuração do backend Google" para o passo a passo. */
window.NEWSLETTER_CONFIG = {
  /* URL do Web App do Apps Script (ex.: https://script.google.com/macros/s/AKfyc.../exec).
     Vazio = modo fallback: o formulário compõe um e-mail (mailto) para `contactEmail`. */
  webappUrl: "https://script.google.com/macros/s/AKfycbxK6_Kr9BYTvneTa7mK4gT6PR9ju-Eg3K5jJd9o26_QiXd6evF_sr_8kw1ybFNXoEU/exec",

  /* E-mail de contato usado no fallback (mailto) quando o backend não está configurado. */
  contactEmail: "",

  /* URL pública do site (GitHub Pages). Usada no e-mail para logo e botão "Ver painel". */
  siteUrl: "https://ldanill01.github.io/monitor-editais/"
};
