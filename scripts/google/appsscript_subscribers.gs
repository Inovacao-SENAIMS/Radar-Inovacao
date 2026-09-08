/**
 * appsscript_subscribers.gs — Backend 100% gratuito da newsletter (Google Apps Script)
 * Radar de Editais de Inovação — SENAI MS / Sistema FIEMS
 *
 * O QUE É
 *   Web App ligado a uma Planilha Google que:
 *     1. doPost  → recebe o formulário do site (nome, e-mail, consentimento),
 *                  grava o assinante como "pendente" e envia e-mail de confirmação
 *                  (double opt-in — LGPD);
 *     2. doGet ?confirm=TOKEN   → ativa a assinatura (página "Confirmado");
 *     3. doGet ?cancel=TOKEN    → cancela a assinatura em 1 clique (unsubscribe);
 *     4. doGet ?action=list&key=CHAVE → devolve JSON dos assinantes ativos
 *                  (usado por scripts/send_newsletter.py; protegido por chave).
 *
 * INSTALAÇÃO (passo a passo completo no PRD.md § Configuração)
 *   1. Crie uma Planilha Google. Renomeie a primeira aba para "Assinantes".
 *   2. Extensões → Apps Script → apague o conteúdo e cole ESTE arquivo.
 *   3. Em Configurações do projeto → Propriedades do script, crie
 *      NEWSLETTER_API_KEY com uma chave longa e aleatória.
 *   4. Implantação → "Nova implantação" → tipo "Aplicativo da Web":
 *        Executar como: Eu (sua conta)
 *        Quem tem acesso: "Qualquer pessoa"
 *      Copie a URL /exec e cole em data/newsletter.js → webappUrl
 *      e em scripts/newsletter_config.json → webapp_url.
 *   5. Autorize as permissões (Planilha + Gmail) quando solicitado.
 *
 * COTAS GRATUITAS (conta Gmail comum)
 *   MailApp: ~100 e-mails/dia (confirmations + resends).
 *   Se tiver conta Google Workspace (ex.: institucional), a cota sobe para ~1.500/dia.
 */

/* ============================ CONFIGURAÇÃO ============================ */
var API_KEY  = PropertiesService.getScriptProperties().getProperty('NEWSLETTER_API_KEY') || '';
var SITE_URL = 'https://ldanill01.github.io/monitor-editais/';
var SENDER_NAME = 'Radar de Editais — SENAI MS';
var SHEET_NAME = 'Assinantes';
var DELIVERIES_SHEET_NAME = 'Envios newsletter';

/* Colunas: 0 Timestamp | 1 Nome | 2 Email | 3 Status | 4 Token | 5 Consentimento | 6 Origem | 7 ConfirmadoEm | 8 CanceladoEm | 9 Observações */
var COL = { TS: 0, NOME: 1, EMAIL: 2, STATUS: 3, TOKEN: 4, CONSENT: 5, ORIGEM: 6, OK_EM: 7, OFF_EM: 8, OBS: 9 };

function sheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
  if (sh.getLastRow() === 0 || String(sh.getRange(1, 1).getValue()).indexOf('Timestamp') !== 0) {
    sh.clear();
    sh.getRange(1, COL.TS + 1, 1, 10).setValues([[
      'Timestamp', 'Nome', 'Email', 'Status', 'Token', 'Consentimento', 'Origem', 'ConfirmadoEm', 'CanceladoEm', 'Observações'
    ]]);
    sh.getRange(1, 1, 1, 10).setFontWeight('bold').setBackground('#003876').setFontColor('#FFFFFF');
    sh.setFrozenRows(1);
  }
  return sh;
}

function rows_() {
  var sh = sheet_();
  var values = sh.getDataRange().getValues();
  values.shift(); // remove header
  return { sheet: sh, data: values };
}

function deliveriesSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(DELIVERIES_SHEET_NAME) || ss.insertSheet(DELIVERIES_SHEET_NAME);
  if (sh.getLastRow() === 0 || String(sh.getRange(1, 1).getValue()) !== 'Edicao') {
    sh.clear();
    sh.getRange(1, 1, 1, 3).setValues([['Edicao', 'Email', 'EnviadoEm']]);
    sh.getRange(1, 1, 1, 3).setFontWeight('bold').setBackground('#003876').setFontColor('#FFFFFF');
    sh.setFrozenRows(1);
  }
  return sh;
}

function sentEmails_(edition) {
  var sh = deliveriesSheet_();
  var values = sh.getDataRange().getValues();
  var seen = {};
  for (var i = 1; i < values.length; i++) {
    if (String(values[i][0]) === edition) seen[String(values[i][1]).trim().toLowerCase()] = true;
  }
  return Object.keys(seen);
}

function apiReply_(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload)).setMimeType(ContentService.MimeType.JSON);
}

/* ============================ doPost — assinatura ============================ */
function doPost(e) {
  try {
    var p = (e && e.parameter) || {};

    /* Honeypot: campo oculto "website" — só bots preenchem */
    if (String(p.website || '') !== '') {
      return reply_({ ok: true, msg: 'Assinatura registrada. Verifique seu e-mail para confirmar.' });
    }

    var nome = String(p.nome || '').trim().substring(0, 80);
    var email = String(p.email || '').trim().toLowerCase().substring(0, 120);
    var consent = String(p.consentimento || '') !== '';

    if (!consent) return reply_({ ok: false, msg: 'É necessário consentir com o recebimento dos e-mails.' });
    if (!nome) return reply_({ ok: false, msg: 'Informe seu nome.' });
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return reply_({ ok: false, msg: 'Informe um e-mail válido.' });

    var now = new Date();
    var r = rows_();
    var rowIdx = -1;   // índice na planilha (1-based + header)
    var existing = null;

    for (var i = 0; i < r.data.length; i++) {
      if (String(r.data[i][COL.EMAIL]).toLowerCase() === email) {
        existing = r.data[i];
        rowIdx = i + 2; // +1 header, +1 base 1
        break;
      }
    }

    if (existing) {
      var status = String(existing[COL.STATUS]).toLowerCase();
      if (status === 'ativo') {
        return reply_({ ok: true, msg: 'Parabéns, agora você receberá as nossas atualizações frequentes, fique de olho no e-mail.' });
      }
    }

    var token = Utilities.getUuid();
    var linha = [now, nome, email, 'pendente', token, 'sim', p.origem || 'site', '', '', existing ? 'reinscrição' : ''];
    if (rowIdx > 0) {
      r.sheet.getRange(rowIdx, 1, 1, 10).setValues([linha]);
    } else {
      r.sheet.appendRow(linha);
    }

    sendConfirmation_(nome, email, token);
    return reply_({ ok: true, msg: 'Recebemos sua solicitação. Confira seu e-mail e confirme a assinatura para começar a receber as atualizações.' });

  } catch (err) {
    return reply_({ ok: false, msg: 'Erro interno ao processar a assinatura. Tente novamente mais tarde.' });
  }
}

/* ============================ doGet — confirmar / cancelar / listar ============================ */
function doGet(e) {
  var p = (e && e.parameter) || {};

  /* Ativar assinatura (double opt-in) */
  if (p.confirm) {
    return byToken_(String(p.confirm), 'ativo', 'confirmado',
      'Assinatura confirmada!',
      'Você passará a receber as atualizações do Radar de Editais de Inovação sempre que houver uma nova rodada de monitoramento.');
  }

  /* Cancelar (unsubscribe em 1 clique — LGPD) */
  if (p.cancel) {
    return byToken_(String(p.cancel), 'cancelado', 'cancelado',
      'Inscrição cancelada',
      'Você não receberá mais os e-mails do Radar de Editais. Se quiser voltar, é só assinar novamente pelo painel.');
  }

  /* API protegida usada pelo envio: lista, consulta e registra entregas. */
  if (p.action === 'list' || p.action === 'sent' || p.action === 'record_sent') {
    if (!API_KEY || !p.key || p.key !== API_KEY) {
      return apiReply_({ error: 'nao_autorizado' });
    }
    if (p.action === 'sent') return apiReply_({ emails: sentEmails_(String(p.edition || '')) });
    if (p.action === 'record_sent') {
      var edition = String(p.edition || '').trim();
      var deliveryEmail = String(p.email || '').trim().toLowerCase();
      if (!edition || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(deliveryEmail)) return apiReply_({ error: 'dados_invalidos' });
      var lock = LockService.getScriptLock();
      lock.waitLock(30000);
      try {
        var alreadySent = sentEmails_(edition);
        if (alreadySent.indexOf(deliveryEmail) === -1) deliveriesSheet_().appendRow([edition, deliveryEmail, new Date()]);
      } finally {
        lock.releaseLock();
      }
      return apiReply_({ ok: true });
    }
    var r = rows_();
    var out = [];
    for (var i = 0; i < r.data.length; i++) {
      if (String(r.data[i][COL.STATUS]).toLowerCase() === 'ativo') {
        out.push({
          nome: String(r.data[i][COL.NOME]),
          email: String(r.data[i][COL.EMAIL]),
          token: String(r.data[i][COL.TOKEN])
        });
      }
    }
    return apiReply_({ assinantes: out });
  }

  return page_('Newsletter — Radar de Editais', 'Serviço de assinatura ativo. Use o painel do Radar de Editais para assinar.');
}

function byToken_(token, newStatus, obsText, title, msg) {
  var r = rows_();
  for (var i = 0; i < r.data.length; i++) {
    if (String(r.data[i][COL.TOKEN]) === token) {
      var email = String(r.data[i][COL.EMAIL]);
      var already = String(r.data[i][COL.STATUS]).toLowerCase() === newStatus;
      if (!already) {
        var rowIdx = i + 2;
        if (newStatus === 'ativo') {
          r.sheet.getRange(rowIdx, COL.STATUS + 1).setValue('ativo');
          r.sheet.getRange(rowIdx, COL.OK_EM + 1).setValue(new Date());
          r.sheet.getRange(rowIdx, COL.OBS + 1).setValue(obsText);
        } else {
          r.sheet.getRange(rowIdx, COL.STATUS + 1).setValue('cancelado');
          r.sheet.getRange(rowIdx, COL.OFF_EM + 1).setValue(new Date());
          r.sheet.getRange(rowIdx, COL.OBS + 1).setValue(obsText);
        }
      }
      return page_(title, msg + (already ? ' (Este link já havia sido utilizado.)' : ''));
    }
  }
  return page_('Link inválido', 'Não encontramos essa assinatura. Assine novamente pelo painel do Radar de Editais.');
}

/* ============================ E-mail de confirmação (double opt-in) ============================ */
function sendConfirmation_(nome, email, token) {
  var url = ScriptApp.getService().getUrl();
  var confirmUrl = url + '?confirm=' + encodeURIComponent(token);
  var cancelUrl = url + '?cancel=' + encodeURIComponent(token);

  var html =
    '<div style="margin:0;padding:24px;background:#F2F7FD;font-family:Arial,Helvetica,sans-serif">' +
      '<table role="presentation" width="600" align="center" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;background:#FFFFFF;border-radius:12px;overflow:hidden">' +
        '<tr><td style="padding:24px 28px;background:#FFFFFF;border-bottom:2px solid #E84910">' +
          '<span style="font-size:15px;font-weight:bold;color:#003876;font-family:Arial,Helvetica,sans-serif">SENAI MS · Sistema FIEMS</span>' +
          '<div style="font-size:11px;color:#5A667D;letter-spacing:.08em;text-transform:uppercase;margin-top:4px">Radar de Editais de Inovação</div>' +
        '</td></tr>' +
        '<tr><td style="padding:28px">' +
          '<p style="margin:0 0 12px;font-size:16px;color:#0E2C63;font-weight:bold">Olá, ' + escapeHtml_(nome) + '!</p>' +
          '<p style="margin:0 0 16px;font-size:14px;line-height:1.6;color:#232E45">Recebemos sua solicitação de assinatura das atualizações do Radar de Editais de Inovação. Para confirmar e começar a receber os e-mails, clique no botão abaixo:</p>' +
          '<p style="margin:0 0 24px;text-align:center">' +
            '<a href="' + confirmUrl + '" style="display:inline-block;background:#E84910;color:#FFFFFF;text-decoration:none;font-weight:bold;font-size:14px;padding:14px 32px;border-radius:6px">Confirmar assinatura</a>' +
          '</p>' +
          '<p style="margin:0 0 8px;font-size:12px;line-height:1.6;color:#5A667D">Se o botão não funcionar, copie e cole este link no navegador:<br>' +
            '<a href="' + confirmUrl + '" style="color:#164194;word-break:break-all">' + confirmUrl + '</a></p>' +
          '<p style="margin:16px 0 0;font-size:12px;line-height:1.6;color:#5A667D;border-top:1px solid #E3E7ED;padding-top:16px">Se não foi você quem solicitou, apenas ignore este e-mail — ou <a href="' + cancelUrl + '" style="color:#164194">cancele a solicitação</a>. Nada será enviado sem a confirmação.</p>' +
        '</td></tr>' +
        '<tr><td style="padding:18px 28px;background:#0E2C63;color:#FFFFFF;font-size:11px;line-height:1.6">' +
          'SENAI MS · Sistema FIEMS — Radar de Editais de Inovação<br>' +
          'Tratamos seus dados (nome e e-mail) exclusivamente para este envio, conforme a LGPD (Lei nº 13.709/2018).' +
        '</td></tr>' +
      '</table>' +
    '</div>';

  MailApp.sendEmail({
    to: email,
    subject: 'Confirme sua assinatura — Radar de Editais SENAI MS',
    htmlBody: html,
    name: SENDER_NAME
  });
}

/* ============================ Saídas HTML ============================ */

/* Resposta para o iframe do site: postMessage → js/newsletter.js */
function reply_(payload) {
  var json = JSON.stringify(payload).replace(/</g, '\\u003c');
  return HtmlService.createHtmlOutput(
    '<!DOCTYPE html><html><body style="margin:0">' +
    '<script>window.parent.postMessage(' + json + ', "*");<\/script>' +
    '</body></html>'
  ).setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/* Página autônoma (confirmar/cancelar) */
function page_(title, msg) {
  return HtmlService.createHtmlOutput(
    '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">' +
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">' +
    '<title>' + escapeHtml_(title) + ' — Radar de Editais</title></head>' +
    '<body style="margin:0;padding:40px 16px;background:#F2F7FD;font-family:Arial,Helvetica,sans-serif">' +
      '<table role="presentation" width="600" align="center" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;background:#FFFFFF;border-radius:12px;overflow:hidden">' +
        '<tr><td style="padding:24px 28px;border-bottom:2px solid #E84910">' +
          '<span style="font-size:15px;font-weight:bold;color:#003876">SENAI MS · Sistema FIEMS</span>' +
          '<div style="font-size:11px;color:#5A667D;letter-spacing:.08em;text-transform:uppercase;margin-top:4px">Radar de Editais de Inovação</div>' +
        '</td></tr>' +
        '<tr><td style="padding:28px">' +
          '<h1 style="margin:0 0 12px;font-size:22px;color:#0E2C63">' + escapeHtml_(title) + '</h1>' +
          '<p style="margin:0;font-size:14px;line-height:1.6;color:#232E45">' + escapeHtml_(msg) + '</p>' +
          '<p style="margin:24px 0 0"><a href="' + SITE_URL + '" style="display:inline-block;background:#E84910;color:#FFFFFF;text-decoration:none;font-weight:bold;font-size:14px;padding:12px 24px;border-radius:6px">Voltar ao painel de editais</a></p>' +
        '</td></tr>' +
      '</table>' +
    '</body></html>'
  );
}

function escapeHtml_(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
