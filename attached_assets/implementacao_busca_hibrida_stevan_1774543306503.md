# Implementação: Busca Híbrida para o Agente Stevan

## Diagnóstico Após Análise do Código

Analisando os 5 arquivos do pipeline, identifiquei 3 pontos de falha e 1 oportunidade já existente:

**Ponto de falha 1 — `search_by_ticker()` em `vector_store.py` (linha 919)**
Faz `WHERE product_ticker = :ticker` exato. Se o campo `product_ticker` do `document_embeddings` está vazio ou preenchido diferente (ex: "VIVT3" vs "vivt3"), retorna zero.

**Ponto de falha 2 — `search_by_product()` em `vector_store.py` (linha 1021)**
Tenta `search_by_ticker()` primeiro. Se não funciona, faz `WHERE product_ticker = :product_upper` — o mesmo filtro exato. Não busca em nenhum lugar além de `document_embeddings.product_ticker`.

**Ponto de falha 3 — `TokenExtractor.extract()` em `semantic_search.py` (linha 185)**
O regex `TICKER_PATTERN = re.compile(r'\b([A-Z]{4}[0-9]{1,2})\b')` só pega tickers com 4 letras + 1-2 dígitos. Tickers como YDUQ3 (4 letras + 1 dígito) são pegos, mas VIVT3 também deveria funcionar. O problema é que mesmo detectando o ticker, o fluxo depois depende de `product_ticker` preenchido.

**Oportunidade existente — `Product.name_aliases` em `models.py` (linha 795)**
O modelo `Product` JÁ TEM um campo `name_aliases` (Text, JSON array) com métodos `get_aliases()` e `add_alias()`. Isso significa que a infraestrutura para aliases já existe no banco — só não é usada na busca do agente.

---

## Estratégia: 3 Intervenções Cirúrgicas

Em vez de criar tabelas novas, vamos usar o que já existe e adicionar o mínimo necessário.

### Intervenção 1: `EntityResolver` — Nova classe em `semantic_search.py`

Busca na tabela `products` usando `ticker`, `name` e `name_aliases` ANTES de ir para o vetor.

```python
# Adicionar em semantic_search.py, após a classe SynonymLookup (linha ~480)

class EntityResolver:
    """
    Camada 0: Resolve termos da query para product_ids concretos
    usando a tabela products (ticker, name, name_aliases).
    
    Não depende de document_embeddings.product_ticker.
    Elimina o ponto único de falha.
    """
    
    # Termos que geram muitos matches irrelevantes
    AMBIGUOUS_TERMS = {
        'xp', 'cdi', 'ibov', 'ifix', 'selic', 'ipca', 'igpm',
        'itau', 'itaú', 'btg', 'bb', 'caixa', 'santander',
        'bradesco', 'safra', 'inter',
    }
    
    @classmethod
    def resolve(cls, terms: List[str], db=None) -> 'EntityResolution':
        """
        Tenta resolver termos para product_ids concretos.
        
        Pipeline:
        1. Match exato em Product.ticker
        2. Match exato em Product.name (ILIKE)
        3. Match em Product.name_aliases (JSON array contains)
        4. Se termo é ambíguo → retorna opções para clarificação
        
        Returns:
            EntityResolution com product_ids resolvidos ou opções de clarificação
        """
        if db is None:
            from database.database import SessionLocal
            db = SessionLocal()
            should_close = True
        else:
            should_close = False
        
        try:
            from database.models import Product
            
            resolved_ids = []
            resolved_products = []
            ambiguous_terms = []
            unresolved_terms = []
            
            for term in terms:
                term_clean = term.strip().upper()
                term_lower = term.strip().lower()
                
                # Check: é ambíguo?
                if term_lower in cls.AMBIGUOUS_TERMS:
                    # Buscar opções concretas para clarificação
                    options = cls._find_ambiguous_options(term_lower, db)
                    if options:
                        ambiguous_terms.append({
                            'term': term,
                            'options': options
                        })
                    continue
                
                # 1. Match exato por ticker
                product = db.query(Product).filter(
                    Product.status == 'ativo',
                    Product.ticker.ilike(term_clean)
                ).first()
                
                if product:
                    resolved_ids.append(product.id)
                    resolved_products.append({
                        'id': product.id,
                        'name': product.name,
                        'ticker': product.ticker,
                        'match_type': 'ticker_exact'
                    })
                    continue
                
                # 2. Match por nome (ILIKE contém)
                product = db.query(Product).filter(
                    Product.status == 'ativo',
                    Product.name.ilike(f'%{term_clean}%')
                ).first()
                
                if product:
                    resolved_ids.append(product.id)
                    resolved_products.append({
                        'id': product.id,
                        'name': product.name,
                        'ticker': product.ticker,
                        'match_type': 'name_ilike'
                    })
                    continue
                
                # 3. Match por name_aliases (JSON array)
                # Product.name_aliases é TEXT com JSON array: ["Vivo", "Telefônica"]
                product = db.query(Product).filter(
                    Product.status == 'ativo',
                    Product.name_aliases.ilike(f'%{term_lower}%')
                ).first()
                
                if product:
                    resolved_ids.append(product.id)
                    resolved_products.append({
                        'id': product.id,
                        'name': product.name,
                        'ticker': product.ticker,
                        'match_type': 'alias_match'
                    })
                    continue
                
                # 4. Não resolvido
                unresolved_terms.append(term)
            
            return EntityResolution(
                product_ids=resolved_ids,
                products=resolved_products,
                ambiguous=ambiguous_terms,
                unresolved=unresolved_terms
            )
        
        finally:
            if should_close:
                db.close()
    
    @classmethod
    def _find_ambiguous_options(cls, term: str, db) -> List[Dict]:
        """
        Para termos ambíguos, retorna opções concretas encontradas na base.
        Ex: "xp" → [XP Inc (XPBR31), XP Log (XPLG11), XP Malls (XPML11)]
        """
        from database.models import Product
        
        products = db.query(Product).filter(
            Product.status == 'ativo',
            (Product.name.ilike(f'%{term}%')) | 
            (Product.ticker.ilike(f'%{term}%'))
        ).limit(5).all()
        
        return [
            {'id': p.id, 'name': p.name, 'ticker': p.ticker}
            for p in products
        ]


@dataclass
class EntityResolution:
    """Resultado da resolução de entidades."""
    product_ids: List[int] = field(default_factory=list)
    products: List[Dict] = field(default_factory=list)
    ambiguous: List[Dict] = field(default_factory=list)
    unresolved: List[str] = field(default_factory=list)
    
    @property
    def has_results(self) -> bool:
        return len(self.product_ids) > 0
    
    @property
    def has_ambiguous(self) -> bool:
        return len(self.ambiguous) > 0
    
    @property
    def needs_clarification(self) -> bool:
        return self.has_ambiguous and not self.has_results
```

---

### Intervenção 2: `search_by_product_id()` — Novo método em `vector_store.py`

Busca blocos pelo `product_id` via join com `content_blocks` e `materials`, sem depender de `product_ticker` no `document_embeddings`.

```python
# Adicionar em vector_store.py, após search_by_product() (após linha ~1124)

def search_by_product_ids(self, product_ids: List[int], n_results: int = 10) -> List[dict]:
    """
    Busca blocos vinculados a product_ids concretos.
    
    CAMINHO ALTERNATIVO que NÃO depende de document_embeddings.product_ticker.
    Usa: products → materials → content_blocks → document_embeddings (via block_id).
    
    Args:
        product_ids: Lista de IDs de produtos resolvidos pelo EntityResolver
        n_results: Número máximo de resultados
        
    Returns:
        Lista de documentos com conteúdo e metadados
    """
    if not product_ids:
        return []
    
    db = SessionLocal()
    try:
        from database.models import Product, Material, ContentBlock
        from datetime import datetime
        
        now = datetime.now()
        
        # Buscar blocos via ORM (caminho products → materials → content_blocks)
        blocks = (
            db.query(ContentBlock, Material, Product)
            .join(Material, Material.id == ContentBlock.material_id)
            .join(Product, Product.id == Material.product_id)
            .filter(
                Material.product_id.in_(product_ids),
                Material.publish_status == 'publicado',
                ContentBlock.status.in_(['auto_approved', 'approved']),
            )
            .order_by(ContentBlock.material_id, ContentBlock.order)
            .limit(n_results * 3)  # Pegar extras para filtrar depois
            .all()
        )
        
        if not blocks:
            print(f"[VECTOR_STORE] search_by_product_ids: 0 blocos para product_ids={product_ids}")
            return []
        
        documents = []
        for block, material, product in blocks:
            # Filtrar expirados
            if material.valid_until and material.valid_until < now:
                continue
            
            # Prioridade por tipo de material
            priority = 0.1
            live_types = ["one_page", "atualizacao_taxas", "argumentos_comerciais"]
            if material.material_type in live_types:
                priority = 0.05
            
            metadata = {
                'product_name': product.name or '',
                'product_ticker': product.ticker or '',
                'products': product.ticker or '',  # Compatibilidade com CompositeScorer
                'gestora': product.manager or '',
                'category': product.category or '',
                'material_type': material.material_type or '',
                'block_type': block.block_type or '',
                'block_id': str(block.id),
                'material_id': str(material.id),
                'product_id': str(product.id),
                'publish_status': material.publish_status,
            }
            
            if material.valid_until:
                metadata['valid_until'] = material.valid_until.strftime("%Y-%m-%d")
            if block.created_at:
                metadata['created_at'] = block.created_at.isoformat()
            
            documents.append({
                'content': block.content or '',
                'metadata': metadata,
                'distance': priority,
                'source': 'entity_resolved',
            })
        
        # Ordenar por prioridade
        documents.sort(key=lambda x: x['distance'])
        
        result = documents[:n_results]
        print(
            f"[VECTOR_STORE] search_by_product_ids: "
            f"{len(result)} blocos de {len(product_ids)} produtos"
        )
        return result
    
    except Exception as e:
        print(f"[VECTOR_STORE] Erro em search_by_product_ids: {e}")
        return []
    finally:
        db.close()
```

---

### Intervenção 3: Integrar Entity Resolution no `EnhancedSearch.search()`

Modificar o método `search()` da classe `EnhancedSearch` para chamar o `EntityResolver` como Camada 0, antes de tudo.

```python
# Em semantic_search.py, método EnhancedSearch.search() (a partir da linha ~1037)
# INSERIR logo após a extração de tokens (linha ~1039), antes da detecção de intent

def search(
    self,
    query: str,
    n_results: int = 5,
    conversation_id: Optional[str] = None,
    similarity_threshold: float = 0.8,
    db: Optional[Any] = None
) -> List[SearchResult]:
    import time
    start_time = time.time()
    
    tokens = TokenExtractor.extract(query)
    normalized_query = QueryNormalizer.normalize(query)
    
    # =========================================================
    # CAMADA 0: ENTITY RESOLUTION (NOVO)
    # Resolve termos para product_ids ANTES de qualquer busca
    # =========================================================
    entity_resolution = None
    entity_results = []
    
    # Termos candidatos: tickers detectados + tokens longos (possíveis nomes)
    entity_terms = list(tokens.possible_tickers)
    for token in tokens.all_tokens:
        if len(token) >= 4 and token.upper() not in [t.upper() for t in entity_terms]:
            entity_terms.append(token)
    
    if entity_terms:
        entity_resolution = EntityResolver.resolve(entity_terms, db=db)
        
        # Se precisa clarificação e não tem resultados, retornar vazio
        # (o agente vai ver zero resultados e pedir clarificação)
        if entity_resolution.needs_clarification:
            print(
                f"[EnhancedSearch] Termo ambíguo detectado: "
                f"{entity_resolution.ambiguous}"
            )
            # Salvar info de ambiguidade nos resultados para o agente usar
            # O agente pode acessar isso via SearchAuditLog
        
        # Se resolveu product_ids, buscar blocos por esse caminho
        if entity_resolution.has_results:
            entity_results = self.vector_store.search_by_product_ids(
                entity_resolution.product_ids,
                n_results=n_results * 2
            )
            print(
                f"[EnhancedSearch] Entity resolved: "
                f"{entity_resolution.products} → "
                f"{len(entity_results)} blocos"
            )
    
    # =========================================================
    # DETECÇÃO DE INTENÇÃO (existente, não muda)
    # =========================================================
    query_intent = TokenExtractor.detect_query_intent(query, tokens)
    is_comparative = query_intent == 'comparative'
    
    # ... (resto do código existente a partir da linha 1046) ...
    
    # =========================================================
    # MERGE: entity_results + resultados existentes
    # =========================================================
    # Adicionar entity_results ao all_results com deduplicação
    for r in entity_results:
        doc_id = r.get('metadata', {}).get('block_id', r.get('content', '')[:50])
        if doc_id not in seen_ids:
            seen_ids.add(doc_id)
            all_results.append(r)
    
    # ... (resto continua igual: composite scoring, etc) ...
```

**Onde exatamente inserir no código existente:**

1. **Após linha 1040** (`normalized_query = QueryNormalizer.normalize(query)`), inserir o bloco de Entity Resolution
2. **Após linha 1098** (onde `all_results` e `seen_ids` já existem), inserir o merge dos `entity_results`

---

## Intervenção 4 (Opcional): Clarificação Estruturada no Agente

No `agent_tools.py`, modificar `_execute_search_knowledge_base` para detectar quando o `EntityResolver` encontrou ambiguidade e retornar opções ao GPT.

```python
# Em agent_tools.py, dentro de _execute_search_knowledge_base (linha ~232)
# Após a chamada enhanced.search(), ANTES do processamento de resultados

async def _execute_search_knowledge_base(args: dict, db=None, conversation_id=None) -> Dict[str, Any]:
    from services.semantic_search import EnhancedSearch, EntityResolver, TokenExtractor
    from services.vector_store import get_vector_store, filter_expired_results

    query = args.get("query", "")
    if not query:
        return {"error": "Query vazia", "results": []}

    vector_store = get_vector_store()
    if not vector_store:
        return {"error": "Base de conhecimento indisponível", "results": []}

    # =========================================================
    # PRE-CHECK: Entity Resolution para detectar ambiguidade
    # Se o termo é ambíguo, retorna opções ANTES de buscar
    # =========================================================
    tokens = TokenExtractor.extract(query)
    entity_terms = list(tokens.possible_tickers) + [
        t for t in tokens.all_tokens if len(t) >= 4
    ]
    
    if entity_terms and db:
        resolution = EntityResolver.resolve(entity_terms, db=db)
        
        if resolution.needs_clarification:
            # Retornar opções para o GPT formular a clarificação
            options_text = []
            for amb in resolution.ambiguous:
                term = amb['term']
                for opt in amb['options']:
                    options_text.append(
                        f"- {opt['name']} ({opt['ticker'] or 'sem ticker'})"
                    )
            
            return {
                "results": [],
                "clarification_needed": True,
                "ambiguous_term": resolution.ambiguous[0]['term'],
                "options": options_text,
                "message": (
                    f"O termo '{resolution.ambiguous[0]['term']}' é ambíguo. "
                    f"Encontrei {len(options_text)} possibilidades na base. "
                    f"Pergunte ao assessor qual ele quer."
                )
            }

    # ... (resto do código existente) ...
```

---

## Resumo Visual: O Que Muda em Cada Arquivo

| Arquivo | O que muda | Linhas afetadas |
|---------|-----------|-----------------|
| `semantic_search.py` | + classe `EntityResolver` (nova) | Inserir após linha ~480 |
| `semantic_search.py` | + dataclass `EntityResolution` (nova) | Inserir após EntityResolver |
| `semantic_search.py` | Modificar `EnhancedSearch.search()` | Linhas 1037-1098 |
| `vector_store.py` | + método `search_by_product_ids()` (novo) | Inserir após linha ~1124 |
| `agent_tools.py` | Modificar `_execute_search_knowledge_base()` | Linhas 232-255 |
| `models.py` | NADA — `Product.name_aliases` já existe | Nenhuma |
| `openai_agent.py` | NADA | Nenhuma |
| `product_ingestor.py` | NADA | Nenhuma |

---

## Antes vs Depois — Cenários Reais

| Cenário | Hoje | Com Entity Resolution |
|---------|------|----------------------|
| "O que vc sabe sobre YDUQ3?" | ❌ `search_by_ticker('YDUQ3')` → 0 (product_ticker vazio) | ✅ EntityResolver → `Product.ticker ILIKE 'YDUQ3'` → product_id → blocos via ORM |
| "E sobre VIVT3?" | ❌ Mesmo problema | ✅ Mesmo fix |
| "Me fala da Vivo" | ❌ Nenhum ticker detectado, busca vetorial genérica | ✅ EntityResolver busca `Product.name ILIKE '%Vivo%'` → resolve → blocos |
| "O que tem sobre XP?" | ❌ Retorna mix caótico | ✅ `is_ambiguous=True` → retorna opções: XP Inc, XP Log, XP Malls → GPT clarifica |
| "Quais ações de telecom?" | Sem mudança — continua usando busca vetorial semântica | Sem mudança — Camada 3 (vetor) cuida |

---

## Plano de Execução

### Fase 1 — Quick Win (1 dia de dev)

1. Criar `EntityResolver` e `EntityResolution` em `semantic_search.py`
2. Criar `search_by_product_ids()` em `vector_store.py`
3. Inserir chamada na `EnhancedSearch.search()` como Camada 0
4. Testar com VIVT3, YDUQ3 e termos que hoje falham

**Resultado:** Os produtos que já estão na base mas tinham `product_ticker` vazio passam a ser encontrados.

### Fase 2 — Anti-ruído (2-3 dias)

5. Implementar detecção de ambiguidade em `agent_tools.py`
6. Popular `name_aliases` dos produtos existentes via script de admin
7. Adicionar logging de `entity_resolution` no `SearchAuditLog`

**Resultado:** Termos ambíguos como "XP" geram clarificação em vez de ruído.

### Fase 3 — Feedback loop (contínuo)

8. Dashboard com queries que passaram por Entity Resolution vs. fallback vetorial
9. Endpoint de admin para gerenciar aliases diretamente
10. Sugestão automática de aliases baseada em queries sem match

---

## Por Que NÃO Criar Nova Tabela

O modelo `Product` já tem:
- `ticker` (indexado)
- `name` (indexado)
- `name_aliases` (JSON array com `get_aliases()` e `add_alias()`)
- `manager`
- `category`
- `status`

Tudo que o `EntityResolver` precisa já está lá. Criar uma tabela `entity_aliases` separada adicionaria complexidade de sync (manter duas fontes de verdade). A abordagem proposta usa a tabela `products` como fonte única e o campo `name_aliases` como extensão.

A única desvantagem é que `name_aliases` é TEXT com JSON (não é searchable por índice GIN). Se a base crescer para milhares de produtos, pode valer criar um índice. Para a escala atual da SVN (dezenas/centenas de produtos), `ILIKE '%term%'` no `name_aliases` é suficiente.
