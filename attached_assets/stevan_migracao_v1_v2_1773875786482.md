# Stevan — Guia de Migração V1 → V2 (Agentic RAG)

> **Para:** Dev responsável pelo sistema Stevan  
> **Objetivo:** Migrar o pipeline de RAG pré-executado pelo código para RAG controlado pelo modelo, sem perda de funcionalidades existentes e sem deixar código morto ou duplicado.  
> **Abordagem:** Migração incremental com feature flag — o sistema V1 continua funcional durante toda a transição.

---

## Índice

1. [Entendendo o que muda — e o que não muda](#1-entendendo-o-que-muda--e-o-que-não-muda)
2. [Pré-requisitos antes de tocar em qualquer código](#2-pré-requisitos-antes-de-tocar-em-qualquer-código)
3. [Etapa 1 — Feature flag e estrutura paralela](#etapa-1--feature-flag-e-estrutura-paralela)
4. [Etapa 2 — Refatorar a montagem do system prompt](#etapa-2--refatorar-a-montagem-do-system-prompt)
5. [Etapa 3 — Refatorar a montagem do user turn](#etapa-3--refatorar-a-montagem-do-user-turn)
6. [Etapa 4 — Expor tools ao modelo corretamente](#etapa-4--expor-tools-ao-modelo-corretamente)
7. [Etapa 5 — Reescrever o loop de chamada à API](#etapa-5--reescrever-o-loop-de-chamada-à-api)
8. [Etapa 6 — Corrigir o histórico de conversa](#etapa-6--corrigir-o-histórico-de-conversa)
9. [Etapa 7 — Remover código morto](#etapa-7--remover-código-morto)
10. [Etapa 8 — Testes obrigatórios antes de ativar em produção](#etapa-8--testes-obrigatórios-antes-de-ativar-em-produção)
11. [Checklist de deploy](#checklist-de-deploy)
12. [O que NÃO deve ser alterado](#o-que-não-deve-ser-alterado)
13. [Armadilhas comuns — leia antes de começar](#armadilhas-comuns--leia-antes-de-começar)

---

## 1. Entendendo o que muda — e o que não muda

### O problema do V1 (o que você está saindo)

No V1, antes de chamar o modelo, o código:
1. Executa busca no RAG com a mensagem bruta do usuário como query
2. Consulta dados externos de FII se detectar ticker
3. Executa web search se detectar intenção de notícia/preço
4. Monta tudo dentro da mensagem do usuário (user turn)
5. Chama o modelo uma única vez com esse contexto pré-digerido

**O modelo nunca decide o que buscar. Ele só recebe o resultado.**

### O que o V2 faz diferente

No V2:
1. O código **não executa nenhuma busca antes** de chamar o modelo
2. O modelo recebe a mensagem **crua** do usuário
3. As tools (search_knowledge_base, lookup_fii_public, search_web, send_document) são **expostas ao modelo** como funções que ele pode chamar
4. Se o modelo decide buscar, o código **executa a tool** e devolve o resultado ao modelo
5. O modelo avalia o resultado e decide se responde ou busca mais
6. **O código gerencia o loop** — não a lógica de quando buscar

### Mapa do que muda

| Componente | V1 | V2 | Ação |
|---|---|---|---|
| Lógica de quando buscar | No código (antes do LLM) | No system prompt (dentro do LLM) | Mover para prompt |
| Execução das tools | Código executa antes da chamada | Código executa quando modelo solicita | Refatorar loop |
| Contexto RAG | Injetado no user turn | Retornado como `tool_result` no histórico | Remover injeção |
| Contexto FII | Injetado no user turn | Retornado como `tool_result` | Remover injeção |
| Contexto web search | Injetado no user turn | Retornado como `tool_result` | Remover injeção |
| System prompt | Tem regras de classificação | Adiciona loop de raciocínio interno | Atualizar prompt |
| Histórico de conversa | Mensagens user/assistant | Mensagens user/assistant + tool_use/tool_result | Atualizar persistência |
| Identidade / personalidade | Mantida | Mantida | Sem alteração |
| Lista de materiais PDF | No user turn | No system prompt | Mover para system |
| Dados do assessor | No user turn | No system prompt | Mover para system |
| send_document | Chamada pelo código | Chamada pelo modelo via tool | Refatorar |

---

## 2. Pré-requisitos antes de tocar em qualquer código

Antes de iniciar qualquer alteração:

### 2.1 — Mapeie todas as funções que constroem o contexto atual

Identifique e liste todos os pontos do código onde:
- A mensagem do usuário é modificada ou enriquecida antes de ir ao modelo
- O RAG é chamado proativamente
- Dados externos (FII, web) são buscados antes da chamada ao modelo
- O user turn é montado com blocos de contexto injetados

**Documente cada um com:** nome da função, arquivo, linha, qual dado injeta.  
Isso será sua lista de itens a remover na Etapa 7.

### 2.2 — Garanta que as tools existentes estão isoladas como funções puras

Cada tool que será exposta ao modelo deve existir como uma função que:
- Recebe apenas os argumentos necessários (query, ticker, etc.)
- Retorna o resultado em formato estruturado (JSON ou objeto)
- Não tem side effects além de buscar/retornar dado
- Pode ser chamada tanto pelo código (V1) quanto pelo loop do modelo (V2)

Se hoje o código de busca está embutido dentro da lógica de montagem do contexto, **extraia para funções separadas antes de continuar**.

### 2.3 — Garanta cobertura de logs mínima

Antes de migrar, certifique-se de que você consegue observar em produção:
- Quais tool calls o modelo está fazendo (nome + argumentos)
- Quanto tempo cada tool call está levando
- Quantas iterações de tool calls acontecem por mensagem
- Se o modelo está respondendo sem tool call (casos casuais / follow-up)

Sem isso você vai no escuro.

---

## Etapa 1 — Feature flag e estrutura paralela

**Objetivo:** Criar a capacidade de rodar V1 e V2 em paralelo, sem risco para produção.

### 1.1 — Criar a flag

Adicione uma variável de configuração (env var ou banco de dados):

```
STEVAN_PIPELINE_VERSION = "v1"  # ou "v2"
```

### 1.2 — Criar o módulo V2 como arquivo separado

**Não modifique** o pipeline V1 existente. Crie:

```
/pipeline/
  stevan_v1.js     ← não toca
  stevan_v2.js     ← cria do zero
  index.js         ← roteador: lê STEVAN_PIPELINE_VERSION e chama o correto
```

O roteador em `index.js`:

```javascript
import { handleMessageV1 } from './stevan_v1.js'
import { handleMessageV2 } from './stevan_v2.js'

export async function handleMessage(params) {
  const version = process.env.STEVAN_PIPELINE_VERSION || 'v1'
  if (version === 'v2') {
    return handleMessageV2(params)
  }
  return handleMessageV1(params)
}
```

### 1.3 — Validar que o V1 continua funcionando

Antes de escrever qualquer linha do V2, suba o roteador com `STEVAN_PIPELINE_VERSION=v1` e confirme que tudo funciona igual ao estado anterior.

---

## Etapa 2 — Refatorar a montagem do system prompt

**Objetivo:** O system prompt do V2 deve conter tudo que é contexto estrutural estático, mais o novo bloco de loop de raciocínio.

### 2.1 — O que entra no system prompt do V2

```javascript
function buildSystemPromptV2({ assessor, materiaisDisponiveis, dataHora, personalidade }) {
  return [
    buildIdentidadeBlock(),           // quem é o Stevan — sem alteração
    buildPersonalidadeBlock(personalidade), // do banco — sem alteração
    buildRestricoesBlock(),           // o que Stevan nunca faz — sem alteração
    buildContextoTemporalBlock(dataHora),   // data/hora — sem alteração
    buildDadosAssessorBlock(assessor),      // ← MOVIDO do user turn para cá
    buildMateriaisDisponiveisBlock(materiaisDisponiveis), // ← MOVIDO do user turn para cá
    buildLoopRaciocininoBlock(),       // ← NOVO — núcleo do V2
  ].join('\n\n')
}
```

### 2.2 — O novo bloco: `buildLoopRaciocininoBlock()`

```javascript
function buildLoopRaciocininoBlock() {
  return `
### ANTES DE RESPONDER — SEU PROCESSO INTERNO

Antes de formular qualquer resposta, percorra este fluxo:

**PASSO 1 — Classifique a mensagem:**
- CASUAL: saudação, agradecimento, conversa sem conteúdo técnico
- FOLLOW-UP: o assessor continua sobre algo já presente no histórico com dados suficientes
- NOVA CONSULTA: pergunta sobre produto, dado, ticker, gestora, conceito
- AMBÍGUA: intenção não está clara o suficiente para agir

**PASSO 2 — Decida a ação:**
- CASUAL ou FOLLOW-UP com dados já disponíveis → responda direto, sem tool call
- NOVA CONSULTA → identifique qual(is) tools são necessárias antes de responder
- AMBÍGUA → pergunte ao assessor antes de buscar

**PASSO 3 — Formule a query (se for buscar):**
Antes de chamar a tool, defina internamente:
- O que exatamente preciso saber para responder esta pergunta?
- Qual é o termo mais específico para essa busca?
- Se há pronome ou referência ao histórico, resolva: "ele" → "BTLG11"
- Prefira queries específicas: "BTLG11 rentabilidade 2024" em vez de "fundo imobiliário"

**PASSO 4 — Avalie o resultado:**
Após receber o resultado da tool, avalie:
- O resultado é sobre o produto/ticker correto e cobre o aspecto perguntado? → responda
- O resultado é parcial, incorreto ou vazio? → reformule a query e tente novamente
- Após 3 tentativas sem resultado satisfatório → informe o assessor e ofereça alternativas

**PASSO 5 — Componha a resposta:**
Só responda ao assessor após ter os dados necessários em mãos.

### CRITÉRIOS DE SUFICIÊNCIA DO RESULTADO DE BUSCA
Suficiente quando: contém dados do produto/ticker correto E cobre o aspecto perguntado.
Insuficiente quando: produto diferente, aspecto não coberto, ou resultado vazio.
Neste caso: reformule com termos alternativos, use ticker em vez do nome ou vice-versa.
Máximo de 3 tentativas por mensagem.
`.trim()
}
```

### 2.3 — O que remover do system prompt do V1

Verifique se no V1 existem blocos como:
- "Quando receber dados de RAG no contexto, use-os para..."
- "O contexto abaixo contém informações recuperadas da base..."
- Qualquer instrução que pressuponha que o contexto já foi injetado

**Esses blocos devem ser removidos no V2.** Eles instruem o modelo para um fluxo que não existe mais.

---

## Etapa 3 — Refatorar a montagem do user turn

**Objetivo:** O user turn do V2 deve conter **apenas a mensagem crua do assessor**.

### V1 (o que existia)

```javascript
// ❌ V1 — NÃO FAZER ISSO NO V2
function buildUserTurnV1({ mensagemAssessor, assessor, contextRAG, dadosFII, resultadoWeb, materiais }) {
  return `
Assessor: ${assessor.nome} | Equipe: ${assessor.equipe}

Materiais disponíveis para envio:
${materiais.map(m => `- ${m.ticker}: [ID:${m.id}] ${m.nome}`).join('\n')}

Contexto recuperado da base interna:
${contextRAG}

Dados de mercado do FII:
${dadosFII}

Resultado de web search:
${resultadoWeb}

Mensagem do assessor:
${mensagemAssessor}
  `.trim()
}
```

### V2 (o que deve ser)

```javascript
// ✅ V2 — user turn limpo
function buildUserTurnV2({ mensagemAssessor }) {
  return mensagemAssessor
}
```

Isso é tudo. A mensagem do assessor, sem nenhum contexto adicional.

Os dados do assessor e a lista de materiais foram movidos para o system prompt na Etapa 2. O contexto RAG, FII e web chegará como `tool_result` no histórico quando o modelo decidir buscá-los.

---

## Etapa 4 — Expor tools ao modelo corretamente

**Objetivo:** Registrar as tools no formato correto para que o modelo possa chamá-las.

### 4.1 — Definição das tools (formato OpenAI/Anthropic)

```javascript
const TOOLS_V2 = [
  {
    type: "function",
    function: {
      name: "search_knowledge_base",
      description: "Busca materiais internos da SVN sobre fundos, FIIs, COEs, gestoras e produtos de renda variável. Use para perguntas sobre estratégia, composição, rentabilidade, análise ou qualquer conteúdo da base de conhecimento interna.",
      parameters: {
        type: "object",
        properties: {
          query: {
            type: "string",
            description: "Query de busca específica. Exemplos: 'BTLG11 rentabilidade histórica', 'Kinea Rendimentos estratégia', 'COE proteção capital estrutura'"
          }
        },
        required: ["query"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "lookup_fii_public",
      description: "Consulta indicadores públicos e atuais de um FII: DY, P/VP, vacância, último rendimento, patrimônio. Use quando o assessor pede dados quantitativos de mercado de um FII.",
      parameters: {
        type: "object",
        properties: {
          ticker: {
            type: "string",
            description: "Ticker do FII. Exemplo: 'BTLG11', 'HGLG11'"
          }
        },
        required: ["ticker"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "search_web",
      description: "Busca informações em tempo real: cotações, notícias recentes, resultados trimestrais, dados macroeconômicos (Selic, IPCA), eventos corporativos. Use apenas para informações que mudam frequentemente.",
      parameters: {
        type: "object",
        properties: {
          query: {
            type: "string",
            description: "Query de busca. Exemplos: 'PETR4 cotação hoje', 'Vale notícias recentes', 'Selic atual'"
          }
        },
        required: ["query"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "send_document",
      description: "Envia o PDF de um material cadastrado para o assessor. Use APENAS quando o assessor pedir explicitamente para enviar, mandar ou compartilhar um material. NÃO use para gerar textos ou pitches.",
      parameters: {
        type: "object",
        properties: {
          material_id: {
            type: "number",
            description: "ID numérico do material conforme lista no system prompt."
          },
          ticker: {
            type: "string",
            description: "Ticker do produto relacionado ao material."
          }
        },
        required: ["material_id"]
      }
    }
  }
]
```

### 4.2 — Boas práticas nas descriptions das tools

As descriptions são lidas pelo modelo para decidir **quando** chamar cada tool. Elas devem:
- Ser específicas sobre quando usar e quando **não** usar
- Dar exemplos de queries válidas
- Deixar claro o que cada tool retorna

Se uma tool está sendo chamada nos momentos errados, reescreva a description antes de mexer no prompt principal.

---

## Etapa 5 — Reescrever o loop de chamada à API

Esta é a mudança mais estrutural. No V1 há uma única chamada à API. No V2 há um loop.

### V1 (uma chamada)

```javascript
// ❌ V1 — chamada única
async function handleMessageV1({ mensagem, assessor, historico }) {
  const contextRAG = await searchKnowledgeBase(mensagem)  // busca antes
  const dadosFII = await lookupFiiIfNeeded(mensagem)       // decide o código
  const resultadoWeb = await searchWebIfNeeded(mensagem)   // decide o código

  const userTurn = buildUserTurnV1({
    mensagemAssessor: mensagem,
    assessor,
    contextRAG,
    dadosFII,
    resultadoWeb,
    materiais: await getMateriaisDisponiveis()
  })

  const response = await openai.chat.completions.create({
    model: MODEL,
    messages: [...historico, { role: 'user', content: userTurn }],
    system: buildSystemPromptV1({ assessor })
  })

  return response.choices[0].message.content
}
```

### V2 (loop com tool calls)

```javascript
// ✅ V2 — loop agentic
async function handleMessageV2({ mensagem, assessor, historico }) {
  const systemPrompt = buildSystemPromptV2({
    assessor,
    materiaisDisponiveis: await getMateriaisDisponiveis(),
    dataHora: getCurrentDateTimeString(),
    personalidade: await getPersonalidadeFromDB()
  })

  // Histórico já contém tool_use e tool_result de turnos anteriores
  const messages = [
    ...historico,
    { role: 'user', content: mensagem }  // mensagem crua — sem contexto injetado
  ]

  const MAX_ITERATIONS = 6  // proteção contra loop infinito
  let iterations = 0

  while (iterations < MAX_ITERATIONS) {
    iterations++

    const response = await openai.chat.completions.create({
      model: MODEL,
      messages,
      tools: TOOLS_V2,
      tool_choice: 'auto',  // modelo decide se usa tool ou responde direto
      system: systemPrompt
    })

    const assistantMessage = response.choices[0].message

    // Adiciona a resposta do modelo ao histórico local desta rodada
    messages.push(assistantMessage)

    // Verifica se o modelo quer chamar tools
    if (!assistantMessage.tool_calls || assistantMessage.tool_calls.length === 0) {
      // Modelo respondeu diretamente — fim do loop
      return {
        content: assistantMessage.content,
        messages  // retornar para persistência no histórico
      }
    }

    // Executa cada tool call solicitada pelo modelo
    const toolResults = await Promise.all(
      assistantMessage.tool_calls.map(async (toolCall) => {
        const result = await executeToolCall(toolCall)
        return {
          role: 'tool',
          tool_call_id: toolCall.id,
          content: JSON.stringify(result)
        }
      })
    )

    // Adiciona os resultados ao histórico — o modelo vai ver no próximo turno
    messages.push(...toolResults)

    // Loop continua: modelo recebe os resultados e decide o próximo passo
  }

  // Se chegou aqui, atingiu o limite de iterações
  console.error(`[Stevan V2] Loop atingiu MAX_ITERATIONS (${MAX_ITERATIONS}) para mensagem: ${mensagem}`)
  return {
    content: 'Desculpe, não consegui recuperar as informações necessárias. Pode reformular a pergunta?',
    messages
  }
}
```

### 5.1 — Implementar `executeToolCall`

```javascript
async function executeToolCall(toolCall) {
  const { name, arguments: argsString } = toolCall.function
  const args = JSON.parse(argsString)

  console.log(`[Tool Call] ${name}`, args)  // log obrigatório para observabilidade
  const startTime = Date.now()

  try {
    let result

    switch (name) {
      case 'search_knowledge_base':
        result = await searchKnowledgeBase(args.query)
        break
      case 'lookup_fii_public':
        result = await lookupFiiPublic(args.ticker)
        break
      case 'search_web':
        result = await searchWeb(args.query)
        break
      case 'send_document':
        result = await sendDocument(args.material_id, args.ticker)
        break
      default:
        result = { error: `Tool desconhecida: ${name}` }
    }

    console.log(`[Tool Result] ${name} — ${Date.now() - startTime}ms`)
    return result

  } catch (error) {
    console.error(`[Tool Error] ${name}`, error)
    return { error: `Erro ao executar ${name}: ${error.message}` }
  }
}
```

**Importante:** as funções `searchKnowledgeBase`, `lookupFiiPublic`, `searchWeb` e `sendDocument` são **as mesmas funções** que existem no V1. Você não reescreve nenhuma delas — apenas muda quem as chama (o loop, não o código pré-chamada).

---

## Etapa 6 — Corrigir o histórico de conversa

Esta etapa é crítica e frequentemente negligenciada. No V2, o histórico deve incluir as tool calls e seus resultados para que o modelo saiba o que já buscou em turnos anteriores.

### 6.1 — Estrutura do histórico no banco de dados

O histórico persistido deve salvar não apenas mensagens user/assistant, mas também o ciclo completo de tool calls:

```javascript
// Estrutura de uma entrada no histórico (banco de dados)
{
  conversationId: "conv_123",
  turnIndex: 5,
  messages: [
    {
      role: "user",
      content: "me fala do BTLG11"
    },
    {
      role: "assistant",
      content: null,
      tool_calls: [
        {
          id: "call_abc123",
          type: "function",
          function: {
            name: "search_knowledge_base",
            arguments: '{"query": "BTLG11 estratégia composição"}'
          }
        }
      ]
    },
    {
      role: "tool",
      tool_call_id: "call_abc123",
      content: '{ "resultado": "..." }'
    },
    {
      role: "assistant",
      content: "O BTLG11 é um fundo de logística gerido pela BTG..."
    }
  ]
}
```

### 6.2 — Regra de truncagem do histórico

O V1 provavelmente trunca o histórico para as últimas N mensagens. No V2, a truncagem deve respeitar a integridade dos blocos de tool call: **nunca truncar no meio de um ciclo tool_use/tool_result**.

```javascript
function truncateHistory(messages, maxMessages = 20) {
  if (messages.length <= maxMessages) return messages

  const truncated = messages.slice(-maxMessages)

  // Garante que não começa com um tool_result órfão (sem o tool_use correspondente)
  const firstValidIndex = truncated.findIndex(
    m => m.role === 'user' || m.role === 'assistant'
  )

  return truncated.slice(firstValidIndex)
}
```

### 6.3 — Migração do histórico existente

Se o V1 persiste o histórico como pares simples user/assistant com contexto injetado no user turn, você precisa decidir:

**Opção A (recomendada):** Ao ativar o V2, iniciar com histórico limpo (apenas as últimas N mensagens sem contexto injetado). As conversas antigas continuam no formato V1.

**Opção B:** Normalizar o histórico antigo removendo os blocos de contexto injetado. Isso é complexo e arriscado — evite a menos que seja estritamente necessário.

---

## Etapa 7 — Remover código morto

Só execute esta etapa **depois** que o V2 estiver validado e ativo em produção.

### 7.1 — O que pode ser removido

Com base no mapeamento feito na Etapa de Pré-requisitos, remova:

- [ ] Toda lógica de "decidir se busca no RAG antes de chamar o modelo"
- [ ] Toda lógica de "decidir se consulta FII antes de chamar o modelo"
- [ ] Toda lógica de "decidir se faz web search antes de chamar o modelo"
- [ ] A função `buildUserTurnV1` (ou equivalente) que injetava contexto no user turn
- [ ] Qualquer variável/constante usada exclusivamente para montar esse contexto
- [ ] Blocos no system prompt do V1 que instruíam o modelo a usar contexto pré-injetado
- [ ] O arquivo `stevan_v1.js` — após período de observação em produção

### 7.2 — O que NÃO remover

- As funções das tools em si (`searchKnowledgeBase`, `lookupFiiPublic`, etc.) — continuam sendo usadas, agora chamadas pelo loop
- A lógica de persistência do histórico — apenas atualizada para incluir tool messages
- A lógica de montagem do system prompt — apenas refatorada, não removida
- O roteador `index.js` — mantenha por pelo menos 30 dias após migração completa

### 7.3 — Antes de deletar qualquer arquivo

```bash
# Confirme que nenhum arquivo importa o que você vai deletar
grep -r "stevan_v1\|buildUserTurnV1\|contextRAG" ./src --include="*.js" --include="*.ts"
```

---

## Etapa 8 — Testes obrigatórios antes de ativar em produção

### 8.1 — Casos de teste mínimos

Crie um script de testes com pelo menos os seguintes cenários e valide o comportamento esperado:

| # | Mensagem do assessor | Comportamento esperado no V2 |
|---|---|---|
| 1 | "oi, bom dia" | Responde direto, **zero tool calls** |
| 2 | "me fala do BTLG11" | 1 tool call: `search_knowledge_base("BTLG11")` |
| 3 | "e o dividend yield atual dele?" (após falar de BTLG11) | 1 tool call: `lookup_fii_public("BTLG11")` — resolve pronome |
| 4 | "compara o BTLG11 com o HGLG11" | 2 tool calls: busca cada fundo separado |
| 5 | "tem alguma notícia sobre Vale hoje?" | 1 tool call: `search_web("Vale notícias hoje")` |
| 6 | "envia o material do BTLG11" | 1 tool call: `send_document(material_id)` |
| 7 | "me faz um pitch do BTLG11" | Busca + **não chama** `send_document` — gera texto |
| 8 | "o que vocês têm da Kinea?" | 1+ tool calls: busca produtos Kinea, lista, pergunta qual interessa |
| 9 | Ticker inexistente: "me fala do XPTO11" | Tenta busca, não encontra, informa assessor sem inventar |
| 10 | "qual a Selic hoje?" | 1 tool call: `search_web("Selic atual")` |

### 8.2 — Validações de segurança do loop

- [ ] Com `MAX_ITERATIONS = 6`, uma mensagem nunca deve travar indefinidamente
- [ ] Se uma tool retorna erro, o modelo deve informar o assessor graciosamente — nunca lançar exception não tratada
- [ ] O modelo nunca deve chamar `send_document` sem que o assessor tenha pedido explicitamente

### 8.3 — Validação de performance

Meça para os 10 casos de teste:
- Latência total da resposta (do recebimento da mensagem à resposta)
- Número de tool calls por mensagem
- Tokens consumidos por mensagem (comparar com V1)

Espere: casos CASUAL 30-50% mais rápidos (zero tool calls). Casos de consulta 20-80% mais lentos dependendo do número de iterações. Isso é aceitável e esperado.

---

## Checklist de deploy

Execute em ordem. Não pule etapas.

**Antes do deploy:**
- [ ] Pré-requisitos documentados (mapeamento de funções existentes)
- [ ] Tools extraídas como funções puras e testadas isoladamente
- [ ] Logs de tool calls implementados e validados
- [ ] Feature flag `STEVAN_PIPELINE_VERSION` criada no ambiente
- [ ] Arquivo `stevan_v2.js` criado com toda a lógica nova
- [ ] System prompt V2 revisado (inclui bloco de raciocínio, remove instruções de contexto pré-injetado)
- [ ] Histórico de conversa atualizado para suportar tool messages
- [ ] Truncagem de histórico respeita integridade de tool cycles
- [ ] Todos os 10 casos de teste passando em ambiente de desenvolvimento

**Deploy inicial:**
- [ ] Deploy com `STEVAN_PIPELINE_VERSION=v1` (sem mudança de comportamento)
- [ ] Confirmar que V1 continua funcionando normalmente
- [ ] Ativar `STEVAN_PIPELINE_VERSION=v2` para **um subconjunto controlado** (ex: equipe interna, assessores de teste)
- [ ] Monitorar logs de tool calls por 24-48h

**Ativação completa:**
- [ ] Sem erros críticos no período de monitoramento
- [ ] Qualidade de resposta validada manualmente nos casos de teste reais
- [ ] Ativar `STEVAN_PIPELINE_VERSION=v2` para 100% dos usuários
- [ ] Manter V1 disponível via flag por 30 dias (rollback de emergência)

**Limpeza (após 30 dias estável):**
- [ ] Remover código morto (Etapa 7)
- [ ] Remover flag `STEVAN_PIPELINE_VERSION`
- [ ] Arquivar ou deletar `stevan_v1.js`
- [ ] Atualizar documentação técnica do sistema

---

## O que NÃO deve ser alterado

Para evitar regressões, as seguintes partes do sistema **não devem ser tocadas** durante esta migração:

- **Base de dados vetorial e indexação** — o RAG em si não muda, apenas quem o chama
- **Função `searchKnowledgeBase`** — mesma lógica, mesmos parâmetros
- **Função `lookupFiiPublic`** — mesma lógica, mesmos parâmetros
- **Função `searchWeb`** — mesma lógica, mesmos parâmetros
- **Função `sendDocument`** — mesma lógica, mesmos parâmetros
- **Identidade e personalidade do Stevan** — apenas movidas de lugar no prompt, sem alterar o texto
- **Integração com WhatsApp / canal de entrega** — essa camada não tem relação com o pipeline RAG
- **Autenticação e identificação do assessor** — não muda
- **Banco de dados de histórico** — schema pode precisar de uma coluna adicional para `role: 'tool'`, mas nenhuma tabela é removida

---

## Armadilhas comuns — leia antes de começar

**❌ Armadilha 1: Migrar tudo de uma vez**  
Não migre o system prompt, o user turn, o loop e o histórico ao mesmo tempo. Faça em etapas e valide cada uma. Um bug em quatro mudanças simultâneas é impossível de isolar.

**❌ Armadilha 2: Esquecer de remover as instruções do V1 do system prompt**  
Se o system prompt ainda tiver blocos que dizem "use o contexto RAG abaixo", o modelo vai esperar por um contexto que não vem mais — e vai se confundir. Audite o prompt linha a linha.

**❌ Armadilha 3: Não persistir tool messages no histórico**  
Se os resultados das tool calls não forem salvos no histórico persistido, no próximo turno o modelo não vai saber o que já buscou e vai buscar de novo desnecessariamente — aumentando latência e custo.

**❌ Armadilha 4: MAX_ITERATIONS muito alto**  
Valores acima de 8-10 iterations podem resultar em respostas que demoram 30+ segundos em casos de falha. Mantenha em 6 e implemente o fallback de mensagem de erro gracioso.

**❌ Armadilha 5: Descriptions de tools vagas**  
Se `search_knowledge_base` e `search_web` tiverem descriptions similares, o modelo vai escolher a errada com frequência. As descriptions são o roteador das tools — trate-as com o mesmo cuidado que o system prompt.

**❌ Armadilha 6: Deletar o V1 antes de ter 30 dias de V2 estável em produção**  
Mantenha o V1 intacto e acessível via flag. O custo de manter o arquivo é zero. O custo de não ter rollback disponível pode ser alto.

---

*Documento de instrução técnica — Sistema Stevan SVN. Março de 2026.*
