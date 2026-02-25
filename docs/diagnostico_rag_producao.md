# Diagnóstico RAG — Produção
**Data:** 25/02/2026  
**Ambiente:** Produção (https://agente-ia-rv-svn.replit.app)  
**Analista:** Agente IA (Stevan)

---

## 1. Contexto da Investigação

O usuário reportou que o agente de IA não encontrava informações sobre fundos ao ser testado na tela "Testar Agente". A pergunta "MANATÍ HEDGE FUND FII preciso de informações sobre esse fundo" resultou em:
- Resposta sobre estruturas de derivativos (Collar, Fence, Step-up) em vez de dados do fundo
- Texto completamente sem sentido (hallucination multilíngue) na continuação

A partir desse relato, foi conduzida uma investigação completa do pipeline RAG em produção.

---

## 2. Metodologia de Investigação

### 2.1 Passo 1 — Análise do endpoint "Testar Agente"

Comparei o código do endpoint de teste (`api/endpoints/agent_test.py`) com o webhook do WhatsApp (`api/endpoints/whatsapp_webhook.py`).

**Descoberta:** O endpoint de teste chamava `generate_response()` com `extra_context=None`, ou seja, **não fazia nenhuma busca na base de conhecimento** antes de gerar a resposta. O webhook do WhatsApp, por outro lado, executa:

```python
# Webhook WhatsApp (whatsapp_webhook.py, linhas 846-862)
vector_store = get_vector_store()
search_results = vector_store.search(normalized_message, n_results=6, similarity_threshold=0.8)
search_results = filter_expired_results(search_results, db)[:3]
knowledge_context = "--- Informações da Base de Conhecimento ---\n..."

# Passa o contexto para o GPT
response = await openai_agent.generate_response(
    message, history, extra_context=knowledge_context, ...
)
```

**Conclusão:** Sem contexto da base de conhecimento, o GPT não tinha informações sobre os fundos e respondia com dados inventados (hallucination). Isso explica o texto sem sentido e a confusão com derivativos.

**Ação já tomada:** O endpoint de teste foi corrigido para incluir a mesma busca RAG do webhook. Essa correção já está em produção.

### 2.2 Passo 2 — Mapeamento dos produtos e materiais em produção

Consultei diretamente o banco de dados de produção para mapear o estado real de todos os produtos, materiais e blocos de conteúdo.

**Query executada:**
```sql
SELECT p.name, p.ticker,
       (SELECT COUNT(*) FROM materials m WHERE m.product_id = p.id) as materiais,
       (SELECT COUNT(*) FROM content_blocks cb 
        JOIN materials m2 ON cb.material_id = m2.id 
        WHERE m2.product_id = p.id AND cb.status = 'approved') as blocos_approved
FROM products p ORDER BY p.name;
```

**Resultado inicial (enganoso):**

| Produto | Ticker | Materiais | Blocos "approved" |
|---------|--------|:-:|:-:|
| MANATÍ HEDGE FUND FII | MANA11 | 2 | 41 |
| LIFE11 | LIFE11 | 1 | 9 |
| LVBI11 | LVBI11 | 1 | 8 |
| FII BTG Pactual Logística | BTLG11 | 1 | 4 |
| FII Guardian Real Estate | GARE11 | 1 | 4 |
| MCRE11 | MCRE11 | 1 | 3 |
| PCIP11 | PCIP11 | 1 | 3 |
| RZAT11 | RZAT11 | 1 | 1 |
| **TVRI11** | TVRI11 | 1 | **0** |
| **VGHF11** | VGHF11 | 1 | **0** |
| XP Log Prime II | — | 2 | 1 |

Neste momento, TVRI11 e VGHF11 pareciam não ter conteúdo aprovado. Porém, o usuário apontou que na interface da aba Documentos eles apareciam com a tag verde "indexado".

### 2.3 Passo 3 — Descoberta dos 3 status de blocos

Investiguei a distribuição real de status dos blocos:

```sql
SELECT status, COUNT(*) FROM content_blocks GROUP BY status;
```

| Status | Quantidade |
|--------|:-:|
| `auto_approved` | 245 |
| `approved` | 74 |
| `pending_review` | 10 |

**Descoberta:** O sistema utiliza 3 status, não 2. A função `_create_block()` em `services/product_ingestor.py` (linha 763-768) classifica automaticamente:

```python
is_high_risk, risk_reason, confidence = detect_high_risk(content, block_type)
if is_high_risk:
    status = ContentBlockStatus.PENDING_REVIEW.value   # "pending_review"
else:
    status = ContentBlockStatus.AUTO_APPROVED.value     # "auto_approved"
```

Ou seja, blocos de baixo risco são `auto_approved` automaticamente, e blocos de alto risco vão para `pending_review`. O status `approved` é para aprovação manual.

**O sistema RAG aceita ambos:** O código de reindexação (`check_and_reindex_embeddings` em `main.py`, linha 234-235) filtra por `['auto_approved', 'approved']`, então ambos os status são indexáveis. A query inicial que mostrava "0 blocos aprovados" para TVRI11 estava filtrando apenas `approved`, ignorando `auto_approved`.

**Resultado corrigido:**

| Produto | Ticker | Blocos auto_approved | Blocos approved | Blocos pending_review | Total |
|---------|--------|:-:|:-:|:-:|:-:|
| MANA11 | MANA11 | 47 | 41 | 0 | 88 |
| LIFE11 | LIFE11 | 31 | 9 | 0 | 40 |
| GARE11 | GARE11 | 26 | 4 | 0 | 30 |
| LVBI11 | LVBI11 | 19 | 8 | 0 | 27 |
| MCRE11 | MCRE11 | 24 | 3 | 0 | 27 |
| RZAT11 | RZAT11 | 33 | 1 | 0 | 34 |
| TVRI11 | TVRI11 | 23 | 0 | 9 | 32 |
| BTLG11 | BTLG11 | 18 | 4 | 0 | 22 |
| PCIP11 | PCIP11 | 7 | 3 | 0 | 10 |
| XP Log Prime II | — | 9 | 1 | 0 | 10 |
| VGHF11 | VGHF11 | 8 | 0 | 1 | 9 |

Agora sim, TVRI11 tem 23 blocos indexáveis (auto_approved) e VGHF11 tem 8. A tag "indexado" na interface está correta — os blocos existem e foram processados.

### 2.4 Passo 4 — A descoberta crítica: embeddings órfãos no vector store

Com os blocos existindo e sendo indexáveis, o próximo passo foi verificar se os embeddings correspondentes existiam na tabela `document_embeddings` (pgvector):

```sql
SELECT product_ticker, product_name, COUNT(*) as embedding_count
FROM document_embeddings
GROUP BY product_ticker, product_name
ORDER BY embedding_count DESC;
```

**Resultado:**

| product_ticker (no embedding) | product_name (no embedding) | Embeddings |
|-------------------------------|---------------------------|:-:|
| **`__SYSTEM_UNASSIGNED__`** | **[Sistema] Documentos Não Vinculados** | **169** |
| MANA11 | MANATÍ HEDGE FUND FII | 88 |
| GARE11 | FII Guardian Real Estate | 30 |
| BTLG11 | FII BTG Pactual Logística | 22 |
| (vazio) | XP Log Prime II | 10 |

**169 embeddings (53% do total de 319) estão marcados como `__SYSTEM_UNASSIGNED__`.**

Detalhando quais documentos estão sob esse ticker fantasma:

```sql
SELECT title, COUNT(*) FROM document_embeddings 
WHERE product_ticker = '__SYSTEM_UNASSIGNED__'
GROUP BY title ORDER BY title;
```

| Documento (campo title no embedding) | Embeddings Órfãos |
|--------------------------------------|:-:|
| Relatório gerencial LIFE11 | 40 |
| Relatório gerencial RZAT11 | 34 |
| Relatório gerencial LVBI11 | 27 |
| Relatório gerencial MCRE11 | 27 |
| Relatório gerencial TVRI11 | 23 |
| Relatório gerencial PCIP11 | 10 |
| Relatório gerencial VGHF11 | 8 |
| **TOTAL** | **169** |

### 2.5 Passo 5 — Entendendo a causa raiz

#### Como os embeddings ficaram órfãos

A sequência de eventos foi:

1. **Upload dos PDFs:** Os relatórios gerenciais de LIFE11, LVBI11, MCRE11, PCIP11, RZAT11, TVRI11 e VGHF11 foram subidos via interface
2. **Criação de produto placeholder:** Como o sistema não encontrou um produto existente para associar, criou um produto chamado `__SYSTEM_UNASSIGNED__` com esse ticker
3. **Processamento e indexação:** Os PDFs foram processados, blocos de conteúdo criados, e embeddings gerados. Nesse momento, os embeddings foram gravados com `product_ticker = '__SYSTEM_UNASSIGNED__'` nos metadados
4. **Correção no banco relacional:** Posteriormente, a função `_resolve_orphan_materials()` (adicionada ao startup) detectou esses materiais órfãos, criou os produtos corretos (LIFE11, LVBI11, etc.) e atualizou `material.product_id` para apontar ao produto certo
5. **Embeddings não atualizados:** A função de resolução tenta reindexar os blocos via `reindex_block()`, mas esse passo **não funcionou em produção** porque o produto `__SYSTEM_UNASSIGNED__` já havia sido removido manualmente do banco antes do deploy da versão com resolução automática

#### Por que o `check_and_reindex_embeddings()` não corrigiu

A função `check_and_reindex_embeddings()` (tarefa em background no startup, `main.py` linha 211) verifica se existem blocos aprovados **sem** embedding correspondente:

```python
existing_doc_ids = set()
rows = db.execute(sql_text("SELECT doc_id FROM document_embeddings")).fetchall()
for row in rows:
    existing_doc_ids.add(row[0])

blocks = db.query(ContentBlock).filter(
    ContentBlock.status.in_(['auto_approved', 'approved'])
).all()

missing_blocks = []
for block in blocks:
    expected_doc_id = f"product_block_{block.id}"
    if expected_doc_id not in existing_doc_ids:
        missing_blocks.append(block)
```

O problema: os embeddings **existem** (o `doc_id` está lá), apenas com **metadados errados**. A função verifica existência mas não valida conteúdo dos metadados. Por isso reportou no log de produção:

```
[REINDEX] Todos os blocos aprovados já possuem embedding. Total: 408
```

Tudo parece OK, mas 169 embeddings estão com `product_ticker = '__SYSTEM_UNASSIGNED__'`.

#### Diagrama do fluxo de dados

```
┌─────────────────────────────────────────────────────────────────┐
│                     BANCO RELACIONAL                            │
│                                                                 │
│  products              materials              content_blocks    │
│  ┌──────────┐         ┌──────────────┐       ┌──────────────┐  │
│  │ id: 30   │    ┌───→│ id: 32       │  ┌───→│ id: 154      │  │
│  │ name:    │    │    │ product_id:30│  │    │ material_id:32│  │
│  │  LIFE11  │◄───┘    │ name: Rel.   │◄─┘    │ status:      │  │
│  │ ticker:  │  CORRETO│  gerencial   │       │ auto_approved│  │
│  │  LIFE11  │         │  LIFE11      │       │ content: "..."│  │
│  └──────────┘         └──────────────┘       └──────────────┘  │
│       ✓ Corrigido pela resolução de órfãos                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     VECTOR STORE (pgvector)                      │
│                                                                 │
│  document_embeddings                                            │
│  ┌──────────────────────────────────────────────────┐           │
│  │ doc_id: "product_block_154"                      │           │
│  │ product_ticker: "__SYSTEM_UNASSIGNED__"  ← ERRADO│           │
│  │ product_name: "[Sistema] Docs Não Vinculados"    │           │
│  │ gestora: ""                                      │           │
│  │ title: "Relatório gerencial LIFE11"              │           │
│  │ content: "Destaques financeiros do LIFE11..."    │           │
│  │ embedding: [0.0234, -0.0891, ...]  (3072 dims)  │           │
│  └──────────────────────────────────────────────────┘           │
│       ✗ NÃO foi atualizado — metadados ainda apontam           │
│         para o produto fantasma                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Impacto nas buscas RAG

Quando o agente recebe uma pergunta sobre "LIFE11", o vector store faz:

```sql
-- Busca por ticker (vector_store.py, linhas 903-907)
SELECT * FROM document_embeddings 
WHERE product_ticker = 'LIFE11'   -- NÃO encontra nada, porque está como __SYSTEM_UNASSIGNED__
LIMIT 10;

-- Busca semântica genérica (vector_store.py, linhas 573-578)
SELECT *, (embedding <=> :query_vec) as distance
FROM document_embeddings
WHERE 1=1 AND publish_status NOT IN ('rascunho', 'arquivado')
ORDER BY embedding <=> :query_vec
LIMIT 20;
-- PODE encontrar, mas sem filtro de ticker, pode misturar com outros fundos
```

A busca por ticker falha completamente. A busca semântica genérica pode encontrar os embeddings, mas sem associação correta ao produto, o ranking e a relevância ficam comprometidos.

### 2.6 Passo 6 — Documentos completamente ausentes

O usuário mencionou dois documentos que não foram encontrados em **nenhuma tabela** do banco de produção:

```sql
-- Busca 1: por nome
SELECT id, name FROM materials 
WHERE name ILIKE '%eurogarden%' OR name ILIKE '%MP TG%' OR name ILIKE '%vale%';
-- Resultado: 0 linhas

-- Busca 2: por produto
SELECT id, name FROM products 
WHERE name ILIKE '%eurogarden%' OR name ILIKE '%vale%';
-- Resultado: 0 linhas

-- Busca 3: nos embeddings
SELECT title FROM document_embeddings 
WHERE title ILIKE '%eurogarden%' OR title ILIKE '%vale%';
-- Resultado: 0 linhas
```

**Documentos ausentes:**
1. **"MP TG Eurogarden (vf) (3)"** — zero registros em materials, products ou document_embeddings
2. **"Vale3 research BTG"** — zero registros em materials, products ou document_embeddings

**Possíveis causas:**
- O upload pode ter falhado silenciosamente durante o processamento do PDF (erro na extração GPT-4 Vision, timeout, etc.)
- O upload pode ter sido feito no ambiente de desenvolvimento (URL diferente) em vez da produção
- O arquivo pode ter sido corrompido durante o envio

**Nota:** Não há registro de erro ou job de processamento falhado associado a esses documentos no banco de produção, o que sugere que o upload nunca chegou a criar o registro inicial do material.

---

## 3. Resumo dos Problemas Encontrados

### Problema 1: Endpoint "Testar Agente" sem busca RAG
- **Gravidade:** Alta (já corrigido)
- **Impacto:** Todas as respostas no teste eram sem contexto da base de conhecimento
- **Status:** Corrigido e em produção

### Problema 2: 169 embeddings órfãos no vector store (53% da base)
- **Gravidade:** Crítica
- **Impacto:** 7 fundos (LIFE11, LVBI11, MCRE11, PCIP11, RZAT11, TVRI11, VGHF11) não são encontrados em buscas por ticker
- **Causa:** Banco relacional foi corrigido, mas metadados dos embeddings no pgvector não foram atualizados
- **Status:** Pendente de correção

### Problema 3: 2 documentos nunca registrados na produção
- **Gravidade:** Média
- **Impacto:** "MP TG Eurogarden" e "Vale3 research BTG" não existem na base
- **Causa:** Upload provavelmente falhou ou foi feito em ambiente errado
- **Status:** Requer re-upload

---

## 4. Métricas Atuais da Base de Produção

| Métrica | Valor |
|---------|-------|
| Total de embeddings | 319 |
| Embeddings utilizáveis (ticker correto) | 150 (47%) |
| Embeddings órfãos (__SYSTEM_UNASSIGNED__) | 169 (53%) |
| Produtos com conteúdo funcional | 4 (MANA11, BTLG11, GARE11, XP Log Prime II) |
| Produtos com conteúdo quebrado | 7 (LIFE11, LVBI11, MCRE11, PCIP11, RZAT11, TVRI11, VGHF11) |
| Documentos ausentes | 2 (MP TG Eurogarden, Vale3 research BTG) |
| Blocos de conteúdo total | 329 |
| Blocos auto_approved | 245 |
| Blocos approved | 74 |
| Blocos pending_review | 10 |

---

## 5. Arquivos Relevantes do Código

| Arquivo | Responsabilidade | Linhas-chave |
|---------|-----------------|-------------|
| `main.py` | Startup, resolução de órfãos, reindexação background | `_resolve_orphan_materials()` L111-208, `check_and_reindex_embeddings()` L211-340 |
| `services/vector_store.py` | Busca semântica, filtros de ticker, `PUBLISH_STATUS_FILTER` | `search()` L540-580, `search_by_product()` L900-910 |
| `services/product_ingestor.py` | Processamento de PDFs, criação de blocos, auto-aprovação | `_create_block()` L738-780 |
| `api/endpoints/products.py` | `reindex_block()` — gera embedding com metadados | L37-116 |
| `api/endpoints/agent_test.py` | Endpoint "Testar Agente" (corrigido) | L45-141 |
| `api/endpoints/whatsapp_webhook.py` | Webhook WhatsApp com busca RAG | L846-907 |

---

## 6. Recomendações de Correção (para validação do consultor)

### 6.1 Correção imediata — Embeddings órfãos
Atualizar os metadados dos 169 embeddings na tabela `document_embeddings` para refletir o produto correto. Duas abordagens possíveis:

**Opção A — UPDATE SQL direto (rápido, sem re-gerar embeddings):**
Atualizar apenas os campos de metadados (`product_ticker`, `product_name`, `gestora`, `category`) sem tocar no vetor de embedding em si. O conteúdo textual e o embedding já estão corretos — só os metadados de associação estão errados.

**Opção B — DELETE + reindexação via código (mais seguro, mais lento):**
Deletar os 169 embeddings órfãos e executar `reindex_block()` para cada bloco, que vai regerar o embedding com metadados corretos e contexto global atualizado. Mais lento por causa das chamadas à API OpenAI para gerar novos embeddings.

### 6.2 Prevenção futura
A função `_resolve_orphan_materials()` precisa ser expandida para também atualizar os embeddings no pgvector quando reassocia um material a um novo produto. Atualmente ela só atualiza o banco relacional.

### 6.3 Documentos ausentes
Necessário re-upload dos PDFs "MP TG Eurogarden" e "Vale3 research BTG" pela interface de produção.
