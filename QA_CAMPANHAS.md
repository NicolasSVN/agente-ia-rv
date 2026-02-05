# QA - Sistema de Campanhas

**Data de Início:** 2026-02-05
**Status Geral:** 🔄 Em Andamento
**Número de Teste:** 11947033973 (Nicolas)

---

## Legenda
- ✅ PASSOU
- ❌ FALHOU
- ⚠️ PARCIAL
- 🔄 PENDENTE
- 🔧 CORRIGIDO

---

## A. LISTAGEM DE CAMPANHAS (/campanhas)

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| A1 | Carregamento inicial da página | 🔄 | |
| A2 | Listagem de campanhas existentes | 🔄 | |
| A3 | Filtro por status (Rascunho, Enviando, Enviada, etc) | 🔄 | |
| A4 | Busca por nome de campanha | 🔄 | |
| A5 | Card de campanha com informações corretas | 🔄 | |
| A6 | Botão "Nova Campanha" funciona | 🔄 | |

---

## B. WIZARD DE CRIAÇÃO - PASSO 1 (FONTE DE DADOS)

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| B1 | Exibição das opções: Lista CSV ou Base de Assessores | 🔄 | |
| B2 | Seleção de "Lista de Contatos" (CSV) | 🔄 | |
| B3 | Seleção de "Base de Assessores" | 🔄 | |
| B4 | Navegação para próximo passo | 🔄 | |

---

## C. MODO LISTA CSV

### C1. Upload de Arquivo

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| C1.1 | Upload de arquivo CSV funciona | 🔄 | |
| C1.2 | Upload de arquivo XLSX funciona | 🔄 | |
| C1.3 | Validação de formato inválido | 🔄 | |
| C1.4 | Preview dos dados carregados | 🔄 | |
| C1.5 | Mapeamento de colunas (telefone obrigatório) | 🔄 | |

### C2. Template de Mensagem

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| C2.1 | Seleção de template existente | 🔄 | |
| C2.2 | Criação de template customizado | 🔄 | |
| C2.3 | Variáveis do CSV disponíveis para inserção | 🔄 | |
| C2.4 | Preview da mensagem com dados reais | 🔄 | |

### C3. Seções Repetíveis

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| C3.1 | Adicionar seção repetível | 🔄 | |
| C3.2 | Remover seção repetível | 🔄 | |
| C3.3 | Editar conteúdo da seção | 🔄 | |
| C3.4 | Variáveis dentro de seção repetível | 🔄 | |

---

## D. MODO BASE DE ASSESSORES

### D1. Seleção de Assessores

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| D1.1 | Carregamento da lista de assessores | 🔄 | |
| D1.2 | Filtro por unidade | 🔄 | |
| D1.3 | Filtro por broker | 🔄 | |
| D1.4 | Seleção individual de assessor | 🔄 | |
| D1.5 | Seleção em lote (todos/nenhum) | 🔄 | |
| D1.6 | Contador de selecionados | 🔄 | |

### D2. Template de Mensagem

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| D2.1 | Variáveis de assessor disponíveis | ✅ | Verificado via preview |
| D2.2 | Variável {{nome}} funciona | ✅ | Substituído: "Nicolas Oliveira Garcia" |
| D2.3 | Variável {{primeiro_nome}} funciona | 🔧 | CORRIGIDO - dispatch_campaign não verificava source_type |
| D2.4 | Variável {{unidade}} funciona | 🔄 | |
| D2.5 | Variável {{broker_responsavel}} funciona | 🔄 | |
| D2.6 | Variável {{data_atual}} funciona | ✅ | Substituído: "05/02/2026" |
| D2.7 | Preview da mensagem com dados reais | 🔄 | |

---

## E. ANEXOS DE ARQUIVO

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| E1 | Upload de imagem (JPG/PNG) como anexo | 🔄 | |
| E2 | Upload de PDF como anexo | 🔄 | |
| E3 | Preview do anexo antes de enviar | 🔄 | |
| E4 | Remoção de anexo | 🔄 | |
| E5 | Envio de mensagem com imagem | 🔄 | |
| E6 | Envio de mensagem com PDF | 🔄 | |
| E7 | Validação de tamanho máximo de arquivo | 🔄 | |

---

## F. PREVIEW E CONFIRMAÇÃO

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| F1 | Preview da mensagem final | 🔄 | |
| F2 | Contagem de destinatários | 🔄 | |
| F3 | Estimativa de tempo de envio | 🔄 | |
| F4 | Botão de confirmar disparo | 🔄 | |
| F5 | Modal de confirmação antes do envio | 🔄 | |

---

## G. DISPARO DE CAMPANHA

### G1. Modo Lista CSV

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| G1.1 | Início do disparo em background | 🔄 | |
| G1.2 | Progresso via SSE em tempo real | 🔄 | |
| G1.3 | Mensagem enviada para número correto | 🔄 | Testar com 11947033973 |
| G1.4 | Variáveis substituídas corretamente | 🔄 | |
| G1.5 | Anexo enviado junto com mensagem | 🔄 | |
| G1.6 | Contador de enviadas/falhadas atualiza | 🔄 | |
| G1.7 | Status final "Enviada" após conclusão | 🔄 | |

### G2. Modo Base de Assessores

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| G2.1 | Início do disparo em background | 🔄 | |
| G2.2 | Progresso via SSE em tempo real | 🔄 | |
| G2.3 | Mensagem enviada para telefone do assessor | 🔄 | Testar com 11947033973 |
| G2.4 | Variável {{nome}} substituída | 🔄 | |
| G2.5 | Variável {{primeiro_nome}} substituída | ❌ | BUG - Fica {primeiro_nome} literal |
| G2.6 | Anexo enviado junto com mensagem | 🔄 | |
| G2.7 | Status final "Enviada" após conclusão | 🔄 | |

---

## H. CANCELAMENTO E ERROS

| ID | Teste | Status | Observações |
|----|-------|--------|-------------|
| H1 | Cancelar disparo em andamento | 🔄 | |
| H2 | Tratamento de número inválido | 🔄 | |
| H3 | Tratamento de falha Z-API | 🔄 | |
| H4 | Lista de falhas acessível após envio | 🔄 | |
| H5 | Retry de mensagens falhadas | 🔄 | |

---

## BUGS ENCONTRADOS

| ID | Descrição | Severidade | Status | Correção |
|----|-----------|------------|--------|----------|
| BUG-C01 | Variável {primeiro_nome} não substituída na mensagem | Alta | 🔄 | Pendente análise |

---

## CENÁRIOS DE TESTE DETALHADOS

### Cenário D2.3: Variável primeiro_nome (BUG CONHECIDO)
```
GIVEN uma campanha modo "Base de Assessores"
  AND template contém "Olá, {primeiro_nome}!"
  AND assessor selecionado tem nome "Nicolas Oliveira Garcia"
WHEN o disparo é executado
THEN a mensagem deve conter "Olá, Nicolas!"
  BUT atualmente contém "Olá, {primeiro_nome}!" (BUG)
```

### Cenário G1.3: Envio para Número de Teste
```
GIVEN uma campanha modo "Lista CSV"
  AND CSV contém linha com telefone "11947033973"
  AND template "Olá, {{nome}}! Teste de campanha."
WHEN o disparo é executado
THEN mensagem "Olá, [nome]! Teste de campanha." é enviada via Z-API
  AND número destino é 5511947033973
  AND status da linha atualiza para "enviada"
```

### Cenário E5: Envio com Imagem
```
GIVEN uma campanha com anexo de imagem (JPG)
  AND mensagem "Confira nosso novo material!"
WHEN o disparo é executado
THEN Z-API recebe chamada sendImage
  AND imagem é enviada antes/junto do texto
  AND destinatário recebe imagem + legenda
```

### Cenário C3: Seções Repetíveis
```
GIVEN uma campanha modo "Lista CSV"
  AND template tem seção repetível {{#clientes}}...{{/clientes}}
  AND CSV tem coluna "clientes" com dados
WHEN a mensagem é montada
THEN a seção é repetida para cada cliente
  AND variáveis internas são substituídas
```

---

## ANÁLISE DO BUG {primeiro_nome}

### Código Relevante Encontrado

**Linha 1193 (build_message_from_base_template):**
```python
primeiro_nome = nome.split()[0] if nome else ""
base_vars = {
    ...
    "primeiro_nome": primeiro_nome,
    ...
}
```

**Linha 1210 (substituição):**
```python
for var_name, value in base_vars.items():
    for pattern in [f"{{{{{var_name}}}}}", f"{{{{ {var_name} }}}}", f"{{{var_name}}}"]:
        message = message.replace(pattern, value)
```

### Padrões Suportados
- `{{primeiro_nome}}` (Jinja double braces)
- `{{ primeiro_nome }}` (Jinja com espaços)
- `{primeiro_nome}` (single braces)

### Hipótese
O usuário pode estar usando um padrão diferente que não está coberto, ou o campo `nome` está vindo vazio/None.

---

## NOTAS DE IMPLEMENTAÇÃO

- **Endpoint de disparo CSV:** `POST /api/campaigns/{id}/dispatch`
- **Endpoint de disparo Base:** `POST /api/campaigns/{id}/dispatch` (detecta source_type)
- **SSE de progresso:** Streaming em tempo real
- **Z-API:** Integração para envio WhatsApp
- **Variáveis suportadas:** nome, primeiro_nome, email, telefone, unidade, equipe, broker_responsavel, data_atual

---

## CORREÇÕES IMPLEMENTADAS

### 2026-02-05: BUG - Variáveis não substituídas em campanhas Base de Assessores

**Problema:** Ao disparar campanhas do tipo "Base de Assessores", as variáveis como `{primeiro_nome}`, `{nome}`, `{data_atual}` não eram substituídas - a mensagem era enviada com os placeholders literais.

**Causa Raiz:** O endpoint `dispatch_campaign` (linha 1466 de campaigns.py) não verificava o campo `source_type` da campanha. Independente do tipo, ele sempre seguia o caminho legacy que usa `column_mapping` e `group_recommendations_by_assessor`, que espera dados em formato CSV.

**Solução:** Adicionada verificação de `source_type` no endpoint `dispatch_campaign`:
```python
source_type = getattr(campaign, 'source_type', 'upload') or 'upload'
if source_type in ["base", "base_assessores"]:
    return await dispatch_campaign_from_base(campaign, db)
```

**Arquivos Modificados:** `api/endpoints/campaigns.py`

**Teste de Validação:**
- Criada campanha 59 com template: "Olá, {primeiro_nome}! Seu nome completo é {nome}. Data: {data_atual}"
- Mensagem recebida: "Olá, Nicolas! Este é um teste de campanha. Seu nome completo é Nicolas Oliveira Garcia. Data: 05/02/2026"
- Status: ✅ CORRIGIDO
