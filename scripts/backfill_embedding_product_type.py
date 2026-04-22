"""
Backfill idempotente do `product_type` (e `product_id`) no `extra_metadata`
de `document_embeddings` (Task #159).

Por que existe
--------------
O caminho oficial de repropagação é `python -m scripts.reembed_blocks --force`,
que reembeda blocos via OpenAI. Em produção, esse caminho:
  - é caro (chama OpenAI por bloco) e lento (minutos);
  - apresentou comportamento instável (encerrou silenciosamente, ver
    follow-up #161) durante a execução da Task #159.

Como `product_type` e `product_id` são apenas campos de metadata (não
participam do cálculo do vetor de embedding), podemos injetá-los direto via
SQL fazendo JOIN `document_embeddings → materials → products`. O resultado
funcional é idêntico ao do reembed e este script é seguro para rodar quantas
vezes for necessário (idempotente: só atualiza linhas que ainda não têm o
campo preenchido).

O que faz
---------
Para cada linha em `document_embeddings`:
  1. Se `extra_metadata` já tem `product_type` não-vazio → ignora.
  2. Caso contrário, busca o `product` via `material_id` e injeta
     `{"product_type": <lower>, "product_id": "<id>"}` no JSON.
  3. Marca `embedding_version = 2` para refletir que o metadata está no
     formato esperado pela Task #153.

Linhas órfãs (com `material_id` NULL) são ignoradas e listadas no resumo
para tratamento via follow-up #162.

Ordem operacional (runbook)
---------------------------
Este script depende de `products.product_type` já estar populado. A ordem
correta é:

  1. `python scripts/backfill_product_types.py`           (produtos)
  2. `python scripts/backfill_embedding_product_type.py`  (este script)

O orquestrador `scripts/run_product_type_backfill_oneshot.py` cobre o
passo 1 ponta-a-ponta. Se houver produtos sem `product_type` no momento
da execução, este script aborta com mensagem clara antes de tentar o
UPDATE — para evitar atualização parcial silenciosa.

Uso
---
    python scripts/backfill_embedding_product_type.py [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Normalização única do extra_metadata para jsonb. Evita repetir
# `de.extra_metadata::jsonb` em vários pontos e blinda contra NULL/string
# vazia (em ambos os casos retorna `{}`::jsonb, que naturalmente cai no
# critério "ausente").
_META_JSONB = "COALESCE(NULLIF(de.extra_metadata, '')::jsonb, '{}'::jsonb)"

# Considera "ausente" qualquer um dos cenários abaixo (todos derivados do
# mesmo `_META_JSONB` normalizado):
#   - chave "product_type" não existe no JSON
#   - valor é JSON null
#   - valor é string vazia, "null", "none" ou "undefined" (case-insensitive,
#     com trim) — variantes legadas geradas por pipelines antigos
_MISSING_PT_PREDICATE = f"""
    (
        NOT ({_META_JSONB} ? 'product_type')
        OR {_META_JSONB}->>'product_type' IS NULL
        OR LOWER(TRIM({_META_JSONB}->>'product_type'))
               IN ('', 'null', 'none', 'undefined')
    )
"""

_UPDATE_SQL = f"""
WITH src AS (
    SELECT de.id,
           ({_META_JSONB}
              || jsonb_build_object(
                    'product_type', LOWER(p.product_type),
                    'product_id', p.id::text
                 )
           )::text AS new_meta
      FROM document_embeddings de
      JOIN materials m ON m.id::text = de.material_id
      JOIN products p ON p.id = m.product_id
     WHERE p.product_type IS NOT NULL AND p.product_type != ''
       AND {_MISSING_PT_PREDICATE}
)
UPDATE document_embeddings de
   SET extra_metadata = src.new_meta,
       embedding_version = 2,
       updated_at = NOW()
  FROM src
 WHERE de.id = src.id
"""


def _snapshot_label(conn, label: str) -> None:
    from sqlalchemy import text

    rows = conn.execute(
        text(
            f"""
            SELECT COALESCE(
                       NULLIF({_META_JSONB}->>'product_type', ''),
                       '<vazio/null>'
                   ) AS pt,
                   COUNT(*) AS c
              FROM document_embeddings de
             GROUP BY 1
             ORDER BY c DESC
            """
        )
    ).all()
    null_meta = conn.execute(
        text(
            "SELECT COUNT(*) FROM document_embeddings "
            "WHERE extra_metadata IS NULL OR extra_metadata = ''"
        )
    ).scalar_one()
    print(f"--- Snapshot {label} ---")
    print(f"{'product_type':<18}  count")
    for pt, c in rows:
        print(f"{pt:<18}  {c}")
    print(f"(extra_metadata NULL/vazio: {null_meta})\n")


def _orphans_summary(conn) -> int:
    from sqlalchemy import text

    return int(
        conn.execute(
            text(
                "SELECT COUNT(*) FROM document_embeddings WHERE material_id IS NULL"
            )
        ).scalar_one()
        or 0
    )


def main(dry_run: bool = False) -> int:
    from sqlalchemy import text
    from database.database import engine

    print("=== Backfill de product_type/product_id em document_embeddings ===")
    print(f"Modo: {'DRY-RUN' if dry_run else 'EXECUÇÃO REAL'}\n")

    with engine.begin() as conn:
        # Pré-checagem: aborta cedo se a etapa 1 do runbook não foi rodada,
        # evitando atualizar embeddings parcialmente e mascarar pendências.
        products_missing_pt = conn.execute(
            text(
                "SELECT COUNT(*) FROM products "
                "WHERE product_type IS NULL OR TRIM(product_type) = ''"
            )
        ).scalar_one()
        if products_missing_pt:
            print(
                f"[ABORT] {products_missing_pt} produto(s) com product_type "
                "vazio/NULL. Rode `python scripts/backfill_product_types.py` "
                "antes deste script (ou use o orquestrador "
                "`scripts/run_product_type_backfill_oneshot.py`)."
            )
            return 4

        _snapshot_label(conn, "ANTES")

        preview = conn.execute(
            text(
                f"""
                SELECT COUNT(*)
                  FROM document_embeddings de
                  JOIN materials m ON m.id::text = de.material_id
                  JOIN products p ON p.id = m.product_id
                 WHERE p.product_type IS NOT NULL AND p.product_type != ''
                   AND {_MISSING_PT_PREDICATE}
                """
            )
        ).scalar_one()
        print(f"Linhas a atualizar: {preview}\n")

        if not dry_run and preview:
            result = conn.execute(text(_UPDATE_SQL))
            print(f"[OK] Atualizadas {result.rowcount} linhas.\n")
        elif dry_run:
            print("[DRY-RUN] Nenhuma alteração foi salva.\n")

        _snapshot_label(conn, "DEPOIS")

        orphans = _orphans_summary(conn)
        # Mesmo predicado da elegibilidade — inclui 'null'/'none'/'undefined'.
        unresolved = conn.execute(
            text(
                f"SELECT COUNT(*) FROM document_embeddings de WHERE {_MISSING_PT_PREDICATE}"
            )
        ).scalar_one()
        # Cálculo explícito: pendências reais são apenas as que TÊM material_id
        # mas continuam sem product_type. Não dependemos da contagem de órfãos
        # incluir/exluir a interseção.
        unresolved_non_orphans = conn.execute(
            text(
                f"""
                SELECT COUNT(*) FROM document_embeddings de
                 WHERE de.material_id IS NOT NULL
                   AND {_MISSING_PT_PREDICATE}
                """
            )
        ).scalar_one()

        # Critério de aceite literal da Task #159:
        # SELECT COUNT(*) FROM document_embeddings
        #  WHERE extra_metadata::jsonb->>'product_type' = 'null'  →  0
        literal_null = conn.execute(
            text(
                f"""
                SELECT COUNT(*) FROM document_embeddings de
                 WHERE {_META_JSONB}->>'product_type' = 'null'
                """
            )
        ).scalar_one()

        print(f"Embeddings sem product_type (total): {unresolved}")
        print(f"  - Órfãos (material_id NULL, irrecuperáveis aqui): {orphans}")
        print(f"  - Não-órfãos pendentes (devem ser 0): {unresolved_non_orphans}")
        print(f"Linhas com product_type literal 'null' (aceite Task #159): {literal_null}")

        if literal_null and not dry_run:
            print(
                "[FALHA] Critério de aceite violado: ainda há linhas com "
                "extra_metadata::jsonb->>'product_type' = 'null'. Investigue."
            )
            return 3

        if unresolved_non_orphans and not dry_run:
            print(
                "[ALERTA] Sobraram embeddings NÃO-órfãos sem product_type. "
                "Verifique se algum produto está sem product_type "
                "e re-execute (ou rode scripts/backfill_product_types.py antes)."
            )
            return 2

        if orphans:
            print(
                f"[INFO] {orphans} embedding(s) órfão(s) ficam sem product_type "
                "(sem material vinculado). Tratamento: follow-up #162."
            )
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Injeta product_type/product_id no extra_metadata de "
            "document_embeddings via JOIN com materials/products."
        )
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run))
