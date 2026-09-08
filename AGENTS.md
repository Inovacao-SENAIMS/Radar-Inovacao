# AGENTS.md — monitor-editais

## What this is
Vanilla static site (no build, no package manager, no git). Shell `index.html` + `js/` modules render the deliverable from `data/editais.js`. Report data is **structured in JSON** — the HTML tables, stats, filters, and aderência section are all generated client-side from that single data source. Works with both `file://` (double-click) and `http://` (served).

## Architecture (data flow)
```
Monitoramento_Editais_Inovacao_YYYY-MM-DD.md   (weekly editor input, human-readable)
        │
        ▼  python scripts/md_to_json.py
data/editais.json                               (single source of truth — machine-readable)
data/editais.js                                 (embedded JS: window.EDITAIS_DATA = {...})
        │
        ▼  <script src="data/editais.js">  →  js/render.js  →  DOM
index.html                                      (thin shell — no hardcoded data)
```

### Weekly update workflow
1. **Edit the `.md`** with new editais/data (or edit `data/editais.json` directly).
2. **Regenerate JSON + JS from markdown** (if you edited the .md):
   ```powershell
   python scripts/md_to_json.py Monitoramento_Editais_Inovacao_2026-08-24.md data/editais.json
   ```
   This generates both `data/editais.json` and `data/editais.js`.
3. **Publish + send the newsletter digest** (optional — requires one-time setup, see `PRD.md`):
   ```powershell
   git push                                            # publishes via GitHub Pages
   python scripts/send_newsletter.py --preview         # review email design
   python scripts/send_newsletter.py --send            # send to active subscribers
   ```
   Secrets live in env vars (`GMAIL_USER`, `GMAIL_APP_PASSWORD`, `NEWSLETTER_API_KEY`) — never in the repo.
4. **Done.** Open `index.html` — all tables, stats, filters update automatically.

### Optional: generate a fully static HTML (no JS dependency)
```powershell
python scripts/render_static.py data/editais.json index.html
```
Use this for a self-contained file (e.g., email attachment, offline archive).

## Run / Preview
No install or build. Works with both `file://` (double-click) and `http://` (served):
```powershell
# Option 1: just open index.html in browser (file://) — works out of the box
# Option 2: serve locally:
python -m http.server 8000
# then open http://localhost:8000
```
No lint/test/typecheck config exists.

## Structure
```
index.html                  — thin shell: loads css + js, empty <main> rendered at runtime
css/tokens.css              — SENAI design tokens (colors, fonts, radii, shadows)
css/style.css               — layout, tables, filters, responsive, cards, newsletter form
js/render.js                — pure DOM generation from JSON (Render.build, statusPill, gradeBadge)
js/filters.js               — filter logic for editais + aderência (Filters.setupAderencia, Filters.setupEditais)
js/newsletter.js            — newsletter signup section: form (nome, e-mail, consent), Apps Script POST via hidden iframe, mailto fallback (Newsletter.mount/build/wire)
js/app.js                   — entry point: scroll spy, nav toggle, drawer, embedded data → render → wire filters → mount newsletter
data/editais.json           — SINGLE SOURCE OF TRUTH: meta, stats, resumo, editais[], aderencia[], nao_confirmado[]
data/editais.js             — embedded JS wrapper: window.EDITAIS_DATA = {...} (works with file://)
data/newsletter.js          — newsletter config: window.NEWSLETTER_CONFIG = { webappUrl, contactEmail, siteUrl }
scripts/md_to_json.py       — parses Monitoramento_*.md → data/editais.json + data/editais.js
scripts/render_static.py    — generates standalone index.html from JSON (optional; includes newsletter section)
scripts/email_template.py   — builds the weekly digest email (SENAI-branded, email-safe HTML + plain text) from editais.json
scripts/send_newsletter.py  — sends the digest via Gmail SMTP (subscribers from Apps Script Web App; batch + sent-log)
scripts/newsletter_config.json — non-secret newsletter config (webapp_url, site_url, sender_name, smtp, batch_size)
scripts/google/appsscript_subscribers.gs — 100% free Google backend (paste into the "Assinantes" sheet's Apps Script): subscribe w/ double opt-in, confirm, cancel, list?key=
newsletter/                 — gitignored local output: preview_*.html + sent_log.json
assets/logo-senai-fiems.png — brand asset
assets/palette.json         — brand palette
.design/Senai/              — source of truth for visual identity (read before CSS changes)
PRD.md                      — product requirements: newsletter feature, setup guide, tasks, roadmap
PROMPT.md                   — 7-step methodology for every monitoring run
Monitoramento_Editais_Inovacao_YYYY-MM-DD.md — dated markdown export / editor input
```

## data/editais.json schema
```jsonc
{
  "meta": {
    "reference_date": "2026-08-24",
    "reference_date_formatted": "2026-08-24 · segunda-feira",
    "scope": "Nacional · MS/Centro-Oeste · Internacional",
    "sources": "FINEP · CNPq · ...",
    "version": "Site 2.0 — Senai Design System",
    "methodology": "..."
  },
  "stats": { "abertos": 30, "continuos": 6, "em_breve": 3, "encerram_7d": 11, "nao_confirmado": 9 },
  "resumo_executivo": ["line 1", "line 2", "line 3"],
  "alerta_prazo": "FAPESP PIPE Soberania Digital...",
  "editais": [
    {
      "edital": "name", "fonte": "FAPESP", "status": "aberto|continuo|breve",
      "abertura": "25/05/2026", "encerramento": "24/08/2026", "dias": "0 (hoje)",
      "publico": "Pequenas empresas SP", "valor": "Até R$ 500 mil",
      "contrapartida": "Não exige", "exigencias": "SAGe; empresa paulista",
      "link": "https://...", "grupo": null
    }
  ],
  "aderencia": [
    { "edital": "name", "institutos": "IST Alimentos", "grau": "alta|media|baixa|none",
      "foco_educacional": "Não", "justificativa": "..." }
  ],
  "nao_confirmado": [
    { "edital": "name", "fonte": "CNPq", "motivo": "..." }
  ]
}
```

### Key conventions
- `editais[].status`: drives sidebar filter — `aberto` | `continuo` | `breve`
- `aderencia[].grau`: drives aderência filter — `alta` | `media` | `baixa` | `none`
- `editais[].dias`: string; if numeric and ≤ 7 → red `.urgent` class; "hoje" also triggers urgent
- `editais[].grupo`: set to `"contínuo"` for continuous-flow editais (visual grouping)
- Missing fields: use `"Não encontrado"` or `"—"`, never invent data.

### Institute filter mapping (js/filters.js `mapInst`)
Add new keywords when adding editais, otherwise the institute filter won't match:
```js
const mapInst = {
  'Tecnologias Digitais': ['eficiencia'],
  'Biotecnologia': ['biomassa', 'alimentos'],
  // add: 'substring-in-edital-name': ['institute-key']
};
```
Institute keys: `alimentos` | `eficiencia` | `biomassa` | `todos`.

## Methodology (PROMPT.md — do not skip)
1. **Date first** (`Passo 0`): system date is the only valid reference for status classification.
2. **Broad scope**: include every innovation edital (any area, nationality, audience). Institute filtering happens only in the adhesion table.
3. **12 fields per edital** — mark missing as "Não encontrado", never invent.
4. **Deep search order** for missing dates: PDF oficial → cronograma → retificações → FAQ → news → contact.
5. **Adhesion**: evaluate only Aberto+Em breve against IST Alimentos (Dourados), IST Eficiência Operacional (Campo Grande), ISI Biomassa (Três Lagoas/Embrapii).
6. **Source over aggregators.** Don't invent data. Update status of editais from previous runs.

## Design constraints
- Brand: SENAI blue `#003876`/`#00529B` + orange `#E84910`; Neo Sans Pro → Montserrat/Mulish fallback. Never add generic palettes when `.design/` has content.
- Layout: `.wrap` (1440px), centered card for tables (`max-width:1440px`), `geo-bg` parallax background.
- JS hooks: `#filt-aderencia`, `#tbl-aderencia`, `#tbl-editais`, `#sidebar`, `#drawer-backdrop`, `#nav-toggle`, `#fab-filtros`, `#nav-menu`.
- Encoding: `UTF-8` with pt-BR text.

## Gotchas
- IS a git repo (remote `github.com/lDanill01/monitor-editais`) — publish via `git push` → GitHub Pages.
- No CI, no lint. Newsletter secrets live ONLY in env vars (`GMAIL_USER`, `GMAIL_APP_PASSWORD`, `NEWSLETTER_API_KEY`) or gitignored `scripts/newsletter_secrets.json` — never commit them.
- OneDrive sync path contains spaces — quote paths in PowerShell.
- `render_static.py` overwrites `index.html` — the dynamic shell version is the default.
- `js/newsletter.js` POSTs to the Apps Script Web App via a hidden iframe (`postMessage` reply); without `webappUrl` configured it falls back to `mailto:`/unavailable message.
