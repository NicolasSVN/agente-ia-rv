# Sistema de Avaliação RAG

Mede precisão da busca semântica (Recall, Precision, MRR, Hit Rate) usando
"golden sets" — conjuntos curados de perguntas com os chunks corretos esperados.

## Como rodar

### Avaliar um produto (sem prompt interativo)

```bash
# Modo padrão, com summary formatado
python -m tests.rag_evaluation --evaluate MANA11 --top-k 6 --no-save

# Salva relatório com nome customizado
python -m tests.rag_evaluation --evaluate MANA11 --top-k 6 --save baseline_pre_reembedding

# Saída JSON pura (não pergunta nada, ideal para pipelines)
python -m tests.rag_evaluation --evaluate MANA11 --top-k 6 --json
```

> A flag `--no-save` pula o prompt `Salvar relatório? [s/N]`. O prompt também é
> automaticamente pulado quando `stdin` não é um TTY (ex.: rodando via pipe ou CI).

### Comparar baseline vs nova versão

```bash
python -m tests.rag_evaluation --evaluate MANA11 --top-k 6 --save baseline
# ... aplicar mudança no RAG (ex.: reembedding) ...
python -m tests.rag_evaluation --evaluate MANA11 --top-k 6 --save pos_reembedding
python -m tests.rag_evaluation --compare baseline.json pos_reembedding.json
```

### Descobrir chunks para criar um golden set

```bash
python -m tests.rag_evaluation --discover MANA11
```

Os IDs impressos seguem o formato `product_block_<id>` — copie-os direto para
o campo `expected_chunk_ids` no JSON do golden set.

### Listar recursos disponíveis

```bash
python -m tests.rag_evaluation --list
```

## Formato dos IDs

Os golden sets usam o formato canônico `product_block_<id>` (ex.:
`product_block_47`), que corresponde à coluna `doc_id` em
`document_embeddings`. O `evaluator.execute_search` normaliza qualquer
resultado da busca para esse formato — usa `doc_id` quando disponível e, na
ausência dele, prefixa `metadata.block_id` com `product_block_`.
