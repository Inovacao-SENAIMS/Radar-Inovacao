# Monitoramento de Editais de Inovação

## Objetivo
Pesquisar editais, chamadas públicas e programas de fomento à inovação que estejam abertos ou próximos de abrir neste momento, e organizar as informações em uma tabela clara, indicando fonte, exigências, contrapartidas e público-alvo.

## Fluxo de trabalho (arquitetura)
```
Monitoramento_Editais_Inovacao_YYYY-MM-DD.md   (edição semanal, human-readable)
        │
        ▼  python scripts/md_to_json.py
data/editais.json                               (fonte única de verdade — machine-readable)
        │
        ▼  fetch() no carregamento  →  js/render.js  →  DOM
index.html                                      (shell — sem dados hardcoded)
```

### Comandos
```powershell
# 1. Editar o .md com novos editais
# 2. Regerar JSON a partir do markdown:
python scripts/md_to_json.py Monitoramento_Editais_Inovacao_2026-08-24.md data/editais.json

# 3. (opcional) Gerar HTML estático autocontido:
python scripts/render_static.py data/editais.json index.html

# 4. Servir localmente para visualizar:
python -m http.server 8000
# abrir http://localhost:8000
```

---

## REGRA CRÍTICA DE ESCOPO (NÃO IGNORE)
A busca é ampla e **NÃO** deve ser filtrada pelos institutos-alvo previamente. Inclua editais de qualquer área de inovação (saúde, indústria 4.0, agro, tecnologia digital, energia, biotecnologia, mobilidade, etc.), de qualquer nacionalidade (nacionais e internacionais) e voltados a qualquer público (empresas de qualquer porte, startups, ICTs, pessoas físicas). Não descarte um edital por parecer fora do escopo dos institutos listados abaixo. A comparação com o escopo dos institutos só acontece no Passo 5, como uma camada extra de sinalização no final do relatório, e nunca como critério para excluir um edital da tabela principal.

---

## Institutos-Alvo (Contexto para avaliação de aderência)
Este monitoramento serve a três institutos do SENAI/MS. Use o escopo abaixo como referência para avaliar, ao final do relatório (Passo 5), se cada edital tem aderência com algum deles. Se encontrar informação mais recente sobre o escopo de algum instituto (novas linhas, credenciamentos), atualize seu julgamento.

1. **IST Alimentos e Bebidas — Dourados/MS**
   - **Atuação:** Análises microbiológicas e físico-químicas (alimentos, bebidas, água); laboratório de qualidade de sementes; consultoria e desenvolvimento de produtos para a cadeia de alimentos, bebidas e cosméticos; foco em agroindústria (carnes, lácteos, grãos, pescados, mel, panificação, etc.).
   - **Aderência provável:** Editais sobre segurança de alimentos, bioinsumos agrícolas, desenvolvimento de novos produtos alimentícios/bebidas/cosméticos, certificação e metrologia de alimentos, agroindústria em geral.

2. **IST Eficiência Operacional — Campo Grande/MS ("Senai Empresa")**
   - **Atuação:** Consultoria e transferência de tecnologia industrial em múltiplas áreas: eficiência energética, automação, metalmecânica, gestão da produção, meio ambiente, logística, construção civil, têxtil/vestuário, energia renovável. Foco multissetorial em ganho de produtividade.
   - **Aderência provável:** Editais sobre eficiência energética, automação industrial, indústria 4.0, produtividade, transferência de tecnologia, descarbonização de processos industriais.

3. **ISI Biomassa — Três Lagoas/MS**
   - **Atuação:** Unidade Embrapii de Transformação da Biomassa. Linhas: Bioprocessos e Biotecnologia Integrada; Energia e Sustentabilidade; Tecnologias de Descarbonização (CCUS); Desenvolvimento de Novos Biomateriais e Insumos Renováveis. Foco em biocombustíveis (SAF, hidrogênio renovável, green diesel, etanol 2G) e aproveitamento de resíduos/subprodutos.
   - **Aderência provável:** Editais de bioenergia, biocombustíveis, hidrogênio verde, captura de carbono (CCUS), biomateriais, aproveitamento de resíduos industriais/agrícolas, química verde.

> **Nota:** Como os três institutos atuam como ICTs credenciadas (e o ISI Biomassa como unidade Embrapii), eles podem se qualificar tanto em editais regionais (MS) quanto em chamadas nacionais voltadas a ICTs/institutos de pesquisa — não restrinja a busca apenas a editais de Mato Grosso do Sul.

---

## ⚙️ Instruções Passo a Passo

### Passo 0 — Data de referência (Obrigatório, sempre primeiro)
Antes de classificar qualquer edital, confirme a data atual do sistema. Esta é a única referência válida para dizer se um edital está "aberto", "em breve" ou "encerrado". Nunca classifique baseado em memória ou suposição; compare a data de hoje com as datas da fonte.

### Passo 1 — Fontes a pesquisar
Busque nas fontes abaixo (e em outras relevantes que encontrar):
- **Órgãos Nacionais:** FINEP, CNPq, CAPES, BNDES, Embrapii, SEBRAE (nacional e estaduais), MCTI.
- **Órgãos Internos:** https://www.portaldaindustria.com.br/canais/plataforma-inovacao-para-industria/, Site FIEMG, Site FIESP, Site CNI, Site SENAI Nacional.
- **Estaduais:** Fundações de Amparo à Pesquisa (FAPESP, FAPERJ, FAPEMIG, FAPESB, FAPESC, FAPEG, etc. — priorize as do estado do usuário, se souber qual é). Agências de fomento (ex.: Desenvolve SP, AGERIO, BADESC). Secretarias estaduais/municipais de CT&I.
- **Programas Específicos:** Centelha, InovAtiva Brasil, Startup Brasil, RENAI.
- **Privados:** Editais de institutos e fundações privadas ligadas a inovação.
- **Internacionais (pesquisar sempre):**
  - Horizon Europe (chamadas com participação de países associados/terceiros).
  - Eureka Network / Eurostars (Brasil participa via CNPq).
  - Cooperações bilaterais de C,T&I (ex.: Brasil-Alemanha, Brasil-Coreia do Sul, Brasil-EUA, Brasil-União Europeia, Brasil-China).
  - Chamadas de organismos multilaterais (BID, Banco Mundial, ONUDI).
  - Agências de fomento estrangeiras com escritório ou parceria no Brasil.

### Passo 2 — Informações a extrair de cada edital
Para cada edital identificado, colete:
1. Nome do edital/chamada
2. Instituição/fonte responsável
3. Link oficial (página do edital, não notícia terceira)
4. Status — `Aberto` / `Em breve` / `Encerrado` / `Não confirmado`
5. Data de abertura das inscrições
6. Data de encerramento (deadline)
7. Público-alvo — classifique explicitamente: Empresa (MPE, média, grande), Startup, ICT, Pessoa física, ou Consórcio/parceria (indicar quais)
8. Área/tema de inovação contemplado
9. Valor do investimento ou faixa de financiamento (por projeto e/ou total)
10. Contrapartida exigida — financeira, em espécie, percentual mínimo, ou "não exige"
11. Principais exigências e documentos (ex.: CNPJ mínimo de X anos, plano de negócios, certidões, enquadramento setorial)
12. Observações relevantes (retificações, prorrogações, restrições)

### Passo 3 — Quando a data não for encontrada, aprofunde a pesquisa
Se a fonte inicial não deixar claro o status, não pule o edital nem assuma. Aprofunde a pesquisa nesta ordem:
1. Abra o PDF oficial do edital.
2. Procure seção de cronograma, "datas importantes" ou "calendário".
3. Verifique retificações ou "adendos".
4. Consulte a página de FAQ.
5. Busque notícias recentes sobre o lançamento/fechamento.
6. Se nada resolver, busque contato institucional e registre na coluna de observações.

> Só depois de esgotar essas etapas, marque como "Não confirmado".

### Passo 4 — Formato de saída (Tabela Markdown)
- **Antes da tabela**, inclua um **Resumo Executivo** (3–4 linhas) com:
  - Quantos editais estão abertos agora.
  - Quantos estão "em breve".
  - Quais têm prazo de encerramento em menos de 7 dias (alerta).
  - Quantos ficaram "não confirmado" e por quê.
- **Entregue a tabela em Markdown**, ordenada por prazo de encerramento mais próximo primeiro (editais de fluxo contínuo após os abertos; "não confirmado" ao final):

| Edital | Fonte | Status | Abertura | Encerramento | Dias restantes | Público-alvo | Valor/Faixa | Contrapartida | Principais exigências | Link |

> **Regra do Link:** Deve conter a URL completa e clicável da página oficial. Se levar direto ao PDF, melhor, mas inclua também o link da página onde o PDF foi encontrado.

> **Regra do Status:** Use exatamente `Aberto`, `Em breve`, `Fluxo contínuo` (para editais sem prazo) ou `Não confirmado`. O parser diferencia maiúsculas/minúsculas.

### Passo 5 — Avaliação de aderência institucional (Seção final)
Adicione uma seção chamada **"Aderência com os institutos SENAI/MS"**. Para cada edital classificado como Aberto ou Em breve (ignore os Encerrados):
1. Compare o tema/objeto com o escopo dos três institutos-alvo.
2. Classifique a aderência: `Alta`, `Média`, `Baixa` ou `Sem aderência identificada` (indicando qual instituto).
3. Escreva uma justificativa breve (1 frase).
4. Sinalize explicitamente se o edital tiver **Foco educacional** (bolsas, formação, capacitação sem componente de P&D/Inovação). Nesses casos, marque: *"Foco educacional — fora do escopo de P&D dos institutos"*. (Atenção: um edital pode ter ambos os componentes; se for o caso, descreva ambos).
5. Se não for possível avaliar com confiança, diga isso explicitamente em vez de forçar uma classificação.

Apresente esta seção em formato de tabela:

| Edital | Instituto(s) com maior aderência | Grau de aderência | Foco educacional? | Justificativa |

### Passo 6 — Seção "Não confirmado"
Ao final, inclua uma seção **"Editais 'Não confirmado'"** em formato de tabela com colunas:

| Edital | Fonte | Motivo |

Inclua o motivo pelo qual a data não foi extraída (ex.: "Prazo final não localizado", "Apenas comunicado de lançamento; regulamento não localizado").

### Passo 7 — Regras gerais
- Priorize sempre a fonte oficial sobre agregadores e blogs.
- Não invente dados — se não encontrar, deixe explícito.
- Atualize o status de editais encontrados em execuções anteriores; não duplique linhas.
- Ao final de cada execução, rode o parser para atualizar o JSON:
  ```powershell
  python scripts/md_to_json.py Monitoramento_Editais_Inovacao_YYYY-MM-DD.md data/editais.json
  ```
- Recarregue `index.html` para validar a renderização.

### Passo 8 — Geração do relatório consolidado
Ao final de cada execução, garanta que o relatório estruturado siga rigorosamente este padrão para facilitar o consumo pelas equipes técnicas e de inteligência competitiva. A estrutura completa do `.md` deve conter:
1. **Cabeçalho** com Data de referência, Escopo e Metodologia
2. **Resumo Executivo** (bullets com stats)
3. **Tabela de Editais** (ordenada por encerramento)
4. **Tabela "Não confirmado"**
5. **Tabela de Aderência**
6. **Observações de método** (blockquotes com alertas contextuais)
