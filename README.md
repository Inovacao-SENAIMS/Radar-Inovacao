# Monitor de Editais de Inovação — SENAI MS

Painel web estático que monitora editais, chamadas públicas e programas de fomento à inovação abertos ou próximos de abrir — nacional, estadual (MS) e internacionais com elegibilidade do Brasil.

## Funcionalidades

- **Tabela de Aderência** — classifica editais por grau de aderência aos 3 institutos SENAI/MS (IST Alimentos, IST Eficiência Operacional, ISI Biomassa)
- **Tabela de Editais** — 38+ editais com filtros dependentes (instituto, status, tipo de público, fonte, dias restantes)
- **Filtros dependentes** — ao selecionar um filtro, os demais se adequam automaticamente
- **Cards mobile** — em telas pequenas, tabelas são substituídas por cards legíveis
- **Dados embutidos** — funciona com `file://` (duplo-clique) sem servidor
- **Newsletter gratuita** — assinatura no site (nome, e-mail, consentimento LGPD) com double opt-in e digest semanal por e-mail — arquitetura 100% gratuita (Google Apps Script + Gmail SMTP), ver `PRD.md`

Para colocar a newsletter em produção, siga o [Guia de ativação](GUIA_ATIVACAO_NEWSLETTER.md).

## Estrutura

```
├── index.html                 Shell vazio — renderizado via JS
├── css/
│   ├── tokens.css             Design tokens SENAI (cores, fontes, sombras)
│   └── style.css              Layout, tabelas, filtros, responsivo
├── js/
│   ├── render.js              Gera DOM a partir do JSON
│   ├── filters.js             Lógica de filtros com dependência
│   └── app.js                 Entry point: scroll spy, nav, drawer
├── data/
│   ├── editais.json           Fonte única de verdade (JSON)
│   ├── editais.js             Wrapper JS: window.EDITAIS_DATA
│   └── newsletter.js          Config da newsletter (webappUrl, contactEmail, siteUrl)
├── js/
│   ├── render.js              Gera DOM a partir do JSON
│   ├── filters.js             Lógica de filtros com dependência
│   ├── newsletter.js          Seção/formulário de assinatura (consentimento LGPD)
│   └── app.js                 Entry point: scroll spy, nav, drawer
├── scripts/
│   ├── md_to_json.py          Parser: Markdown → JSON + JS
│   ├── render_static.py       Gerador HTML estático (opcional)
│   ├── email_template.py      Design do e-mail digest (HTML + texto)
│   ├── send_newsletter.py     Envio via Gmail SMTP (lotes, registro anti-duplicata no Sheets)
│   ├── newsletter_config.json Config não-secreta da newsletter
│   └── google/appsscript_subscribers.gs  Backend Google (colar no Apps Script)
├── assets/
│   ├── logo-senai-fiems.png   Logo SENAI MS
│   └── palette.json           Paleta de cores
├── PROMPT.md                  Metodologia de 8 passos para cada execução semanal
├── AGENTS.md                  Instruções para agentes OpenCode
└── .gitignore
```

## Fluxo semanal

```
Monitoramento_Editais_Inovacao_YYYY-MM-DD.md  (edição manual)
        │
        ▼  python scripts/md_to_json.py
data/editais.json + data/editais.js           (atualizados)
        │
        ▼  git push (publica no GitHub Pages)
        ▼  GitHub Actions envia o digest quando data/editais.json mudar
index.html → render.js → DOM                  (tabelas, filtros, cards)
newsletter → Gmail SMTP                       (digest para assinantes)
```

### Atualizar dados

1. Editar o `.md` com novos editais
2. Executar:
   ```powershell
   python scripts/md_to_json.py data/Monitoramento_Editais_Inovacao_2026-08-24.md data/editais.json
   ```
3. Abrir `index.html` no navegador

### Enviar a newsletter (após configurar — ver PRD.md)

```powershell
python scripts/send_newsletter.py --preview      # revisa o design no navegador
python scripts/send_newsletter.py --test-to eu@exemplo.com   # teste individual
python scripts/send_newsletter.py --send         # envia aos assinantes ativos
```

O envio usa apenas conta Google gratuita (Gmail SMTP + Apps Script); segredos
ficam em variáveis de ambiente (`GMAIL_USER`, `GMAIL_APP_PASSWORD`,
`NEWSLETTER_API_KEY`) — nunca no repositório. Para o envio automático, salve
essas mesmas três variáveis em **Settings → Secrets and variables → Actions**
do repositório GitHub. O workflow só é disparado por alterações em
`data/editais.json`; ajustes visuais, textos e código não enviam e-mails.

### Gerar HTML estático (opcional)

```powershell
python scripts/render_static.py data/editais.json index.html
```

## Executar

Sem instalação. Funciona com `file://` ou HTTP:

```powershell
# Opção 1: duplo-clique no index.html
# Opção 2: servidor local
python -m http.server 8000
# abrir http://localhost:8000
```

## Tecnologias

- **HTML/CSS/JS** vanilla (sem frameworks, sem build)
- **Python 3** para scripts de conversão
- Design tokens do SENAI MS (paleta azul `#003876` + laranja `#E84910`)

## Licença

Uso interno — SENAI/MS Sistema FIEMS.
