# Guia de ativação da newsletter

Este guia coloca a newsletter em funcionamento sem alterar o código. Execute os passos na ordem apresentada e marque cada item quando terminar.

## Antes de começar

Você precisará de:

- Uma conta Google que será dona da planilha e do Apps Script.
- Uma conta Gmail que enviará os e-mails. Pode ser a mesma conta Google.
- Acesso de edição a este projeto e ao repositório GitHub Pages.
- Um endereço de e-mail seu para os testes.

Não registre senhas, chaves ou URLs privadas no Git.

## 1. Criar a planilha de assinantes

- [X] Acesse [Google Sheets](https://sheets.google.com) e crie uma planilha em branco.
- [X] Renomeie a primeira aba para **Assinantes**.
- [X] Dê à planilha um nome identificável, como `Radar de Editais — Assinantes`.
- [X] Mantenha a planilha privada; ela armazenará nome, e-mail, status e tokens de confirmação.

Não crie as colunas manualmente. O Apps Script as cria na primeira assinatura.

## 2. Configurar o Apps Script

- [X] Na planilha, acesse **Extensões → Apps Script**.
- [X] Remova o código inicial do editor.
- [X] Abra localmente [appsscript_subscribers.gs](</Users/danillosantanadearaujo/Documents/Python%20Scripts/monitor-editais/scripts/google/appsscript_subscribers.gs>), copie todo o conteúdo e cole no editor.
- [X] Em **Configurações do projeto → Propriedades do script**, crie a propriedade `NEWSLETTER_API_KEY`.
- [X] Use uma chave longa e exclusiva e guarde-a em local seguro, pois será usada novamente no passo 5.
- [X] Clique em **Salvar**.

Exemplo de formato da chave:

```text
Nome: NEWSLETTER_API_KEY
Valor: troque-por-uma-chave-longa-e-aleatoria
```

## 3. Publicar o Apps Script como Web App

- [X] No Apps Script, clique em **Implantar → Nova implantação**.
- [X] Em “Selecionar tipo”, escolha **Aplicativo da Web**.
- [X] Em “Executar como”, escolha **Eu**.
- [X] Em “Quem tem acesso”, escolha a opção que permite acesso a qualquer pessoa.
- [X] Clique em **Implantar** e aceite as permissões solicitadas para Planilhas e Gmail.
- [X] Copie a URL final da implantação. Ela deve terminar em `/exec`.

Guarde esta URL. Ela será usada pelo formulário público e pelo script de envio.

> **Ao atualizar o código do Apps Script:** em **Implantar → Gerenciar implantações**, edite a implantação Web App, selecione **Nova versão** e implante novamente. A URL `/exec` permanece a mesma. Esta versão cria a aba privada **Envios newsletter** e só ativa o cadastro após a confirmação por e-mail.

## 4. Conectar o formulário do site

Abra [data/newsletter.js](</Users/danillosantanadearaujo/Documents/Python%20Scripts/monitor-editais/data/newsletter.js>) e preencha `webappUrl` com a URL copiada.

```js
webappUrl: "https://script.google.com/macros/s/SEU_ID/exec",
```

Abra [newsletter_config.json](</Users/danillosantanadearaujo/Documents/Python%20Scripts/monitor-editais/scripts/newsletter_config.json>) e preencha `webapp_url` com a mesma URL.

```json
"webapp_url": "https://script.google.com/macros/s/SEU_ID/exec",
```

- [X] As duas URLs são iguais e terminam em `/exec`.
- [X] Nenhuma chave secreta foi colocada nesses dois arquivos.

## 5. Configurar a conta remetente no Gmail

- [X] Entre na conta Gmail que enviará os digests.
- [X] Ative a verificação em duas etapas da conta Google.
- [X] Em **Segurança → Senhas de app**, gere uma senha de app para “E-mail”.
- [X] Copie a senha de app; ela será mostrada uma única vez.

No terminal, dentro da pasta do projeto, defina as variáveis apenas para a sessão atual:

```zsh
export GMAIL_USER="seu-email@gmail.com"
export GMAIL_APP_PASSWORD="sua-senha-de-app"
export NEWSLETTER_API_KEY="a-mesma-chave-configurada-no-script"
```

Para não repetir esse comando a cada uso, crie o arquivo local `scripts/newsletter_secrets.json`. Ele já é ignorado pelo Git.

```json
{
  "gmail_user": "danillo.araujo.senai@gmail.com",
  "gmail_app_password": "sua-senha-de-app",
  "newsletter_api_key": "a-mesma-chave-configurada-no-apps-script"
}
```

- [X] O arquivo contém apenas valores reais, sem aspas extras ou comentários.
- [ ] `git status` não mostra `scripts/newsletter_secrets.json`.

## 6. Testar a assinatura completa

- [ ] Abra `index.html` no navegador ou publique uma versão de teste no GitHub Pages.
- [ ] Clique no botão laranja **Newsletter**.
- [ ] Preencha nome, e-mail de teste e consentimento.
- [ ] Envie o formulário e confirme que a mensagem informa o envio da confirmação.
- [ ] Abra o e-mail recebido e clique em **Confirmar assinatura**.
- [ ] Na planilha, confirme que o registro aparece com status `ativo`.
- [ ] Use o link de cancelamento recebido e confirme que o status muda para `cancelado`.
- [ ] Assine novamente e confirme a ativação para continuar o teste de envio.

Se o formulário não responder, confira se `webappUrl` contém a URL `/exec` e se a implantação está configurada para acesso público.

## 7. Revisar e enviar o primeiro digest

Gere uma prévia local. Este comando não envia e-mail:

```zsh
python3 scripts/send_newsletter.py --preview
```

- [ ] Abra o arquivo indicado dentro da pasta `newsletter/` e revise o conteúdo, os links e o rodapé.

Envie uma edição apenas para você:

```zsh
python3 scripts/send_newsletter.py --test-to seu-email@exemplo.com
```

- [ ] Confira caixa de entrada, spam, layout, links e botão de cancelamento.

Quando tudo estiver correto, envie aos assinantes ativos:

```zsh
python3 scripts/send_newsletter.py --send
```

O script registra quem recebeu cada edição na aba privada **Envios newsletter** da mesma planilha, evitando duplicidade mesmo entre execuções locais e do GitHub Actions.

## 8. Publicar o site configurado

Depois de validar o formulário e o e-mail:

```zsh
git add data/newsletter.js scripts/newsletter_config.json
git commit -m "configura newsletter"
git push
```

- [ ] Abra o GitHub Pages e teste novamente o botão **Newsletter** na página pública.

## Rotina semanal

```zsh
python3 scripts/md_to_json.py data/Monitoramento_Editais_Inovacao_YYYY-MM-DD.md data/editais.json
python3 scripts/send_newsletter.py --preview
python3 scripts/send_newsletter.py --send
git push
```

Envie somente após revisar a prévia. Caso o lote seja maior que o limite configurado, o script informa quantos assinantes restam; reexecute no próximo dia para continuar sem duplicar os já enviados.

## Solução rápida de problemas

| Situação                                                 | Verificação e ação                                                                                    |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| O formulário mostra que assinaturas estão indisponíveis | Preencha`webappUrl` em `data/newsletter.js` e publique o site novamente.                              |
| Nenhum e-mail de confirmação chega                       | Verifique Spam; depois abra o histórico de execuções do Apps Script e confira as permissões do Gmail. |
| O script acusa`webapp_url vazio`                         | Preencha`scripts/newsletter_config.json` com a mesma URL `/exec`.                                     |
| O script acusa chave recusada                              | Confirme que`NEWSLETTER_API_KEY` é idêntica a `API_KEY` do Apps Script.                             |
| O script não autentica no Gmail                           | Gere uma nova senha de app e confirme que a autenticação em duas etapas está ativa.                    |
| O e-mail foi enviado duas vezes                            | Confira a aba privada **Envios newsletter** e interrompa novos disparos; ela é a proteção contra duplicidade. |
