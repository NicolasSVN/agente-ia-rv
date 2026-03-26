# Onde o Ticker Se Perde — Análise de Root Cause

## O Fluxo Completo (com base nos arquivos analisados)

```
Criação do Produto (NÃO está nos arquivos enviados)
    ↓
Product { id, name, ticker?, manager, name_aliases }
    ↓
Upload de PDF → ProductIngestor.process_pdf_to_blocks()
    ↓
Material { product_id, extracted_metadata? }
    ↓
ContentBlock { material_id, content, block_type }
    ↓
index_approved_blocks() → metadata["product_ticker"] = product.ticker
    ↓
VectorStore.add_document() → document_embeddings { product_ticker }
    ↓
EnhancedSearch.search() → search_by_ticker("VIVT3") → WHERE product_ticker = 'VIVT3'
```

## Os 3 Pontos Onde o Ticker Pode Se Perder

### Ponto 1: Produto criado sem ticker (ROOT CAUSE)

O código de criação de produto **não está nos arquivos enviados**. Ele
provavelmente está em `api/endpoints/products.py` (que a análise
comparativa mencionou como `_auto_create_product`) ou na tela de admin
do frontend.

O que sabemos pelo schema do `Product`:

```python
# models.py, linha 790
ticker = Column(String(50), nullable=True, index=True)
```

O campo é **nullable**. Então é perfeitamente possível criar um produto
com `ticker=None` e todos os blocos indexados terão
`product_ticker=""` no `document_embeddings`.

**Isso é o root cause.** Se o produto entra sem ticker, toda a cadeia
downstream herda o campo vazio.

**Para investigar:** Preciso ver o arquivo que cria produtos — seja o
endpoint REST ou o `_auto_create_product`. Provavelmente está em:
- `api/endpoints/products.py` (endpoint de criação via admin)
- `services/product_resolver.py` (criação automática durante ingestão)

### Ponto 2: Indexação propaga o ticker corretamente (NÃO é o problema)

O `index_approved_blocks()` (product_ingestor.py, linhas 877-1026) faz:

```python
# Linha 897
product = db.query(Product).filter(Product.id == material.product_id).first()

# Linha 982
"product_ticker": product_ticker.upper() if product_ticker else "",
```

Se `product.ticker` for None, o resultado é `""`. Não há bug aqui —
ele propaga fielmente o que está no `Product`. O problema é que o
`Product` entrou sem ticker.

### Ponto 3: Material.extracted_metadata não é usado para enriquecer o Product

O campo `Material.extracted_metadata` (models.py, linha 851) é
descrito como:

```python
extracted_metadata = Column(Text, nullable=True)
# JSON com metadados extraídos (fund_name, ticker, gestora, confidence)
```

Isso sugere que durante o processamento do PDF, o GPT-4 Vision detecta
`fund_name`, `ticker`, `gestora` e `confidence` — e salva no
`Material`. Mas **ninguém propaga isso de volta para o `Product`**.

Em nenhum lugar dos 7 arquivos enviados existe código que faça:

```python
# Isso NÃO existe:
if material.extracted_metadata:
    meta = json.loads(material.extracted_metadata)
    if meta.get("ticker") and not product.ticker:
        product.ticker = meta["ticker"]
```

Esse é o segundo gap: mesmo que o GPT extraia o ticker do PDF, ele
fica preso no `Material.extracted_metadata` e nunca chega no
`Product.ticker`.

---

## Diagnóstico Consolidado

| Etapa | Onde | Status |
|-------|------|--------|
| Criar produto com ticker | Arquivo não enviado | **SUSPEITO — preciso ver** |
| extracted_metadata → Product.ticker | Não existe | **GAP CONFIRMADO** |
| Product.ticker → metadata indexação | product_ingestor.py:982 | ✅ Funciona |
| metadata → document_embeddings | vector_store.py:326-366 | ✅ Funciona |
| search_by_ticker() | vector_store.py:919 | ✅ Funciona (se ticker existir) |
| search_by_product() | vector_store.py:1021 | ⚠️ Usa mesmo filtro exato |
| TokenExtractor regex | semantic_search.py:133 | ✅ Detecta VIVT3, YDUQ3 |

---

## Ações Recomendadas (Ordem de Prioridade)

### 1. Me enviar o arquivo de criação de produto

Preciso ver onde produtos são criados para confirmar se há um
`_auto_create_product` que deixa o ticker vazio. Provavelmente é um
desses:

- `api/endpoints/products.py`
- `services/product_resolver.py`
- Ou outro service que crie `Product()` com `ticker=None`

### 2. Criar backfill: extracted_metadata → Product.ticker

Script que roda uma vez para produtos existentes sem ticker:

```python
async def backfill_product_tickers(db: Session):
    """
    Para cada produto sem ticker, tenta extrair do extracted_metadata
    dos seus materiais.
    """
    from database.models import Product, Material
    import json

    products_sem_ticker = db.query(Product).filter(
        (Product.ticker.is_(None)) | (Product.ticker == '')
    ).all()

    updated = 0
    for product in products_sem_ticker:
        # Buscar ticker no extracted_metadata dos materiais
        materials = db.query(Material).filter(
            Material.product_id == product.id,
            Material.extracted_metadata.isnot(None)
        ).all()

        for material in materials:
            try:
                meta = json.loads(material.extracted_metadata)
                ticker = meta.get("ticker", "").strip().upper()
                if ticker and len(ticker) >= 4:
                    product.ticker = ticker
                    updated += 1
                    print(f"[BACKFILL] Product '{product.name}' → ticker={ticker}")
                    break
            except (json.JSONDecodeError, TypeError):
                continue

    db.commit()
    print(f"[BACKFILL] {updated} produtos atualizados com ticker")
    return updated
```

### 3. Criar hook na ingestão: propagar ticker automaticamente

Dentro do `index_approved_blocks()`, após carregar o produto (linha
897), adicionar:

```python
# product_ingestor.py, após linha 898
# Se o produto não tem ticker, tentar extrair do extracted_metadata
if product and not product.ticker and material.extracted_metadata:
    try:
        ext_meta = json.loads(material.extracted_metadata)
        detected_ticker = ext_meta.get("ticker", "").strip().upper()
        if detected_ticker and len(detected_ticker) >= 4:
            product.ticker = detected_ticker
            db.commit()
            print(
                f"[INGESTOR] Ticker auto-preenchido: "
                f"Product '{product.name}' → {detected_ticker}"
            )
    except (json.JSONDecodeError, TypeError):
        pass
```

Isso garante que novos uploads preencham o ticker do produto se ele
estiver vazio.

### 4. EntityResolver (da proposta anterior) como rede de segurança

Mesmo com o fix de dados, o EntityResolver continua necessário porque:

- Produtos antigos podem ter sido criados antes do fix
- O campo `product_ticker` no `document_embeddings` pode já estar
  vazio para blocos existentes (e reindexar tudo é custoso)
- O assessor pode buscar por nome ("Vivo") em vez de ticker

O EntityResolver é a **rede de segurança** que torna a busca
resiliente independente da qualidade dos dados históricos.

---

## Resumo: O Que Fazer em Que Ordem

| # | Ação | Impacto | Esforço |
|---|------|---------|---------|
| 1 | Me enviar arquivo de criação de produto | Confirma root cause | 0 |
| 2 | Backfill script (extracted_metadata → Product.ticker) | Corrige dados existentes | ~1h |
| 3 | Hook no index_approved_blocks() | Previne problema futuro | ~30min |
| 4 | EntityResolver + search_by_product_ids() | Rede de segurança permanente | ~1 dia |

As ações 2 e 3 corrigem a raiz. A ação 4 torna o sistema resiliente
mesmo quando a raiz não foi corrigida. Idealmente, faz as três.
