# QA - Upload Inteligente de Documentos

**Data de Início:** 2026-02-05
**Status Geral:** 🔄 Em Andamento

---

## Legenda
- ✅ PASSOU
- ❌ FALHOU
- ⚠️ PARCIAL
- 🔄 PENDENTE
- 🔧 CORRIGIDO

---

## A. LISTAGEM DE DOCUMENTOS (/documentos)

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| A1 | Carregamento inicial da página | 🔄 | |
| A2 | Exibição de contadores (Total, Indexados, Pendentes, Este Mês) | 🔄 | |
| A3 | Alerta de documentos pendentes exibido | 🔄 | |
| A4 | Filtro por busca (texto) | 🔄 | |
| A5 | Filtro por categoria | 🔄 | |
| A6 | Card de documento com status correto | 🔄 | |
| A7 | Botão "Processar" em documento pendente | 🔄 | |
| A8 | Botão "Excluir" em documento | 🔄 | |
| A9 | Botão "Novo Upload" redireciona corretamente | 🔄 | |

---

## B. NOVO UPLOAD (/base-conhecimento/upload)

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| B1 | Página de upload carrega corretamente | 🔄 | |
| B2 | Drag and drop de arquivo PDF funciona | 🔄 | |
| B3 | Seleção de arquivo via botão funciona | 🔄 | |
| B4 | Validação de tipo de arquivo (apenas PDF) | 🔄 | |
| B5 | Validação de tamanho máximo de arquivo | 🔄 | |
| B6 | Preview do PDF antes de processar | 🔄 | |
| B7 | Extração de metadados automática (ticker, gestora, fundo) | 🔄 | |
| B8 | Seleção/criação de produto associado | 🔄 | |
| B9 | Início do processamento com SSE | 🔄 | |
| B10 | Barra de progresso durante processamento | 🔄 | |
| B11 | Logs de processamento em tempo real | 🔄 | |
| B12 | Mensagem de sucesso ao concluir | 🔄 | |
| B13 | Tratamento de erro durante processamento | 🔄 | |

---

## C. REPROCESSAMENTO DE DOCUMENTO

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| C1 | GIVEN documento pendente WHEN clica em "Processar" THEN inicia reprocessamento | 🔄 | |
| C2 | GIVEN job anterior existe WHEN reprocessa THEN continua de onde parou | 🔄 | |
| C3 | GIVEN job anterior NÃO existe WHEN reprocessa THEN processa do zero automaticamente | 🔄 | Corrigido - endpoint agora detecta e cria novo job |
| C4 | GIVEN arquivo original não existe WHEN reprocessa THEN exibe erro "Faça novo upload" | 🔄 | |
| C5 | Barra de progresso durante reprocessamento | 🔄 | |
| C6 | Status atualizado para "Indexado" após sucesso | 🔄 | |

---

## D. EXCLUSÃO DE DOCUMENTO

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| D1 | GIVEN documento na lista WHEN clica em "Excluir" THEN exibe modal de confirmação | 🔄 | |
| D2 | GIVEN modal exibido WHEN confirma exclusão THEN documento é removido | 🔄 | |
| D3 | GIVEN modal exibido WHEN cancela THEN documento permanece | 🔄 | |
| D4 | GIVEN documento indexado WHEN excluído THEN blocos ChromaDB são removidos | 🔄 | |

---

## E. PROCESSAMENTO GPT-4 VISION

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| E1 | Extração de tabelas de PDF | 🔄 | |
| E2 | Detecção de ticker (padrão 4 letras + 11/12/13) | 🔄 | |
| E3 | Detecção de gestora (fuzzy match) | 🔄 | |
| E4 | Extração de nome do fundo | 🔄 | |
| E5 | Criação de blocos de conteúdo | 🔄 | |
| E6 | Geração de chunks narrativos para RAG | 🔄 | |
| E7 | Indexação no ChromaDB | 🔄 | |

---

## F. FILA DE REVISÃO (/review-queue ou similar)

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| F1 | Listagem de itens pendentes de revisão | 🔄 | |
| F2 | Preview do conteúdo extraído | 🔄 | |
| F3 | Preview do PDF original | 🔄 | |
| F4 | Aprovação individual de item | 🔄 | |
| F5 | Rejeição individual de item | 🔄 | |
| F6 | Aprovação em lote (bulk) | 🔄 | |
| F7 | Reprocessamento de página específica | 🔄 | |
| F8 | Edição de conteúdo antes de aprovar | 🔄 | |

---

## BUGS ENCONTRADOS

| ID | Descrição | Severidade | Status | Correção |
|----|-----------|------------|--------|----------|
| BUG-U01 | Reprocessamento falhava quando não havia job anterior | Alta | 🔧 | Endpoint agora cria job do zero automaticamente |

---

## CENÁRIOS DE TESTE DETALHADOS

### Cenário C1: Reprocessamento com Job Existente
```
GIVEN um documento com status "pendente"
  AND existe um DocumentProcessingJob anterior
  AND o arquivo PDF original existe
WHEN o usuário clica no botão "Processar"
THEN o sistema retoma o processamento de onde parou
  AND exibe progresso em tempo real
  AND atualiza o status para "Indexado" ao concluir
```

### Cenário C3: Reprocessamento sem Job Anterior
```
GIVEN um documento com status "pendente"
  AND NÃO existe DocumentProcessingJob
  AND o arquivo PDF original existe (material.file_path)
WHEN o usuário clica no botão "Processar"
THEN o sistema detecta ausência de job
  AND cria um novo DocumentProcessingJob
  AND processa o documento do zero
  AND exibe progresso em tempo real
```

### Cenário C4: Arquivo Não Encontrado
```
GIVEN um documento com status "pendente"
  AND o arquivo PDF original NÃO existe
WHEN o usuário clica no botão "Processar"
THEN o sistema exibe mensagem "Arquivo PDF não encontrado. Faça um novo upload do documento."
```

---

## NOTAS DE IMPLEMENTAÇÃO

- **Endpoint de reprocessamento:** `POST /api/products/materials/{material_id}/resume-upload`
- **Detecção automática:** Se não há job ou arquivo no job path, usa material.file_path
- **Streaming SSE:** Progresso enviado via Server-Sent Events
- **ChromaDB:** Blocos indexados para busca semântica
