# PRD — Newsletter do Radar de Editais

## Objetivo

Permitir que visitantes assinem atualizações do Radar de Editais de Inovação do SENAI MS e recebam um digest profissional quando houver novidades, alterações de prazo ou editais próximos do encerramento. A solução usa somente serviços gratuitos: GitHub Pages, Google Sheets, Google Apps Script e Gmail SMTP.

## Experiência do assinante

1. O visitante encontra o botão laranja **Newsletter** na barra superior ou acessa a seção de assinatura.
2. Informa nome, e-mail e concorda com o recebimento das atualizações.
3. Recebe uma mensagem de confirmação e ativa a assinatura pelo link recebido.
4. Recebe somente os digests posteriores à confirmação.
5. Pode cancelar a assinatura em um clique no rodapé de cada e-mail.

## Arquitetura

```text
index.html + js/newsletter.js
        │ POST em iframe oculto
        ▼
Google Apps Script + Google Sheets
        │ double opt-in / cancelamento / lista de assinantes ativos
        ▼
scripts/send_newsletter.py + Gmail SMTP
        │
        ▼
Digest HTML e texto gerado de data/editais.json
```

`data/editais.json` permanece a única fonte de dados do radar. O e-mail é montado a partir de suas novidades, alertas de prazo e resumo executivo.

## Checklist de entrega

- [x] Criar seção de assinatura com nome, e-mail e consentimento LGPD.
- [x] Adicionar botão CTA **Newsletter** destacado na barra superior.
- [x] Incluir link de newsletter na navegação e no scroll spy.
- [x] Criar comportamento responsivo para desktop e celular.
- [x] Adicionar respeito a `prefers-reduced-motion` para a animação do CTA.
- [x] Criar backend Google Apps Script com double opt-in, cancelamento e proteção da lista por chave.
- [x] Criar template de e-mail HTML e versão em texto simples com identidade SENAI.
- [x] Criar script de prévia, teste individual, envio em lote e log anti-duplicata.
- [x] Manter segredos fora do Git com variáveis de ambiente e arquivo local ignorado.
- [x] Atualizar o gerador de HTML estático com o formulário e CTA.
- [x] Validar a sintaxe de JavaScript e Python e gerar a prévia local do e-mail.
- [ ] Criar a planilha Google e colar `scripts/google/appsscript_subscribers.gs` no Apps Script.
- [ ] Definir `NEWSLETTER_API_KEY` nas Propriedades do Script e autorizar acesso à planilha e ao Gmail.
- [ ] Publicar o Apps Script como Aplicativo da Web acessível a qualquer pessoa.
- [ ] Preencher a URL `/exec` em `data/newsletter.js` e `scripts/newsletter_config.json`.
- [ ] Configurar `GMAIL_USER`, `GMAIL_APP_PASSWORD` e `NEWSLETTER_API_KEY` no ambiente local.
- [ ] Executar teste completo de assinatura, confirmação e cancelamento.
- [ ] Enviar um e-mail de teste com `python3 scripts/send_newsletter.py --test-to seu@email.com`.
- [ ] Configurar os secrets do GitHub Actions (`GMAIL_USER`, `GMAIL_APP_PASSWORD`, `NEWSLETTER_API_KEY`) para envio automático após mudança em `data/editais.json`.
- [ ] Publicar a versão configurada no GitHub Pages.

## Configuração inicial do Google

1. Crie uma planilha Google e renomeie a primeira aba para `Assinantes`.
2. Abra **Extensões → Apps Script**, substitua o conteúdo pelo arquivo `scripts/google/appsscript_subscribers.gs` e defina `NEWSLETTER_API_KEY` em **Configurações do projeto → Propriedades do script**.
3. Em **Implantar → Nova implantação**, escolha **Aplicativo da Web**, execute como sua conta e permita acesso a qualquer pessoa. Autorize as permissões solicitadas.
4. Copie a URL terminada em `/exec` para os dois locais abaixo:

```js
// data/newsletter.js
webappUrl: "https://script.google.com/macros/s/SEU_ID/exec"
```

```json
// scripts/newsletter_config.json
"webapp_url": "https://script.google.com/macros/s/SEU_ID/exec"
```

5. Defina os segredos no terminal antes de enviar. Nunca os registre no repositório.

```zsh
export GMAIL_USER="seu-email@gmail.com"
export GMAIL_APP_PASSWORD="senha-de-app-do-gmail"
export NEWSLETTER_API_KEY="a-mesma-chave-do-apps-script"
```

No Gmail, a senha de app exige autenticação em duas etapas. Como alternativa local, crie `scripts/newsletter_secrets.json`; esse caminho já está no `.gitignore`.

## Operação semanal

```zsh
python3 scripts/md_to_json.py data/Monitoramento_Editais_Inovacao_2026-09-01.md data/editais.json
python3 scripts/send_newsletter.py --preview
python3 scripts/send_newsletter.py --test-to seu@email.com
git push
```

Após o `git push`, o workflow `.github/workflows/send-newsletter.yml` envia
automaticamente o digest somente quando `data/editais.json` foi alterado.

Revise o arquivo em `newsletter/preview_YYYY-MM-DD.html` antes do envio. O script evita envio duplicado da mesma edição e respeita o limite de lote configurado.

## Melhorias futuras

- [ ] Disponibilizar uma página pública de preferências para escolher frequência e temas.
- [ ] Registrar métricas agregadas de assinaturas, confirmações e cancelamentos em planilha separada.
- [ ] Criar um resumo mensal com tendências de fontes, áreas e valores dos editais.
- [ ] Incluir teste automatizado do formulário em navegador antes de cada publicação.
- [ ] Adicionar um fluxo editorial de aprovação do digest antes do disparo.
- [ ] Criar uma política de privacidade pública, com contato do encarregado de dados e prazo de retenção.
