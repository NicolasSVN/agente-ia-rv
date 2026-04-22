"""
Reembedding idempotente dos blocos de conteúdo (Task #152).

Para blocos com `embedding_version < TARGET_VERSION` (default 2):
1. Recalcula `content_for_embedding` (markdown para tabelas) e persiste no bloco.
2. Reindexa o bloco via ProductIngestor.
3. Marca o bloco com `embedding_version = TARGET_VERSION`.

É seguro rodar múltiplas vezes — só reprocessa o que ainda está em versão antiga.
Pode ser executado sob load (processa em lotes pequenos com sleep entre lotes).

Uso:
    python -m scripts.reembed_blocks --batch 50 --sleep 1.5
    python -m scripts.reembed_blocks --product-id 42
    python -m scripts.reembed_blocks --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from typing import List, Optional

from sqlalchemy import and_, or_

TARGET_VERSION = 2


def _iter_blocks(db, product_id: Optional[int], batch: int, force: bool = False):
    """
    Itera blocos elegíveis usando cursor por id (estável mesmo quando
    `embedding_version` é atualizado durante o processamento). NUNCA usa OFFSET,
    que pularia registros conforme o conjunto encolhe.

    Quando `force=True` (Task #153), ignora o filtro por `embedding_version` e
    reembeda TODOS os blocos aprovados, garantindo que o novo metadata
    (`product_type`, `product_id`) chegue até embeddings que já estavam em v2
    mas foram gerados antes da Task #153.
    """
    from database.models import ContentBlock, ContentBlockStatus, Material

    last_id = 0
    while True:
        q = db.query(ContentBlock).join(Material, ContentBlock.material_id == Material.id)
        q = q.filter(ContentBlock.id > last_id)
        if not force:
            q = q.filter(
                or_(
                    ContentBlock.embedding_version.is_(None),
                    ContentBlock.embedding_version < TARGET_VERSION,
                )
            )
        else:
            # Em modo force, só faz sentido reembedar blocos aprovados (os
            # únicos que `index_approved_blocks` indexa de fato).
            q = q.filter(
                ContentBlock.status.in_([
                    ContentBlockStatus.APPROVED.value,
                    ContentBlockStatus.AUTO_APPROVED.value,
                ])
            )
        if product_id is not None:
            q = q.filter(Material.product_id == product_id)
        rows = q.order_by(ContentBlock.id.asc()).limit(batch).all()
        if not rows:
            break
        for r in rows:
            yield r
        last_id = rows[-1].id


def _markdown_for_block(ingestor, block, product_name: str, product_ticker: Optional[str]) -> Optional[str]:
    """Gera markdown para tabela; retorna None para blocos não-tabela."""
    from database.models import ContentBlockType

    if block.block_type not in (ContentBlockType.TABLE.value, ContentBlockType.FINANCIAL_TABLE.value):
        return None
    try:
        data = json.loads(block.content)
        data.pop("_financial_metrics_detected", None)
    except Exception:
        return None
    try:
        return ingestor._table_to_markdown(
            data,
            title=block.title,
            product_name=product_name,
            product_ticker=product_ticker,
        )
    except Exception as e:
        print(f"[REEMBED] Falha gerar markdown bloco {block.id}: {e}")
        return None


def run(batch: int, sleep: float, product_id: Optional[int], dry_run: bool, force: bool = False) -> dict:
    """
    Estratégia segura (Task #152):
    1. Coleta IDs elegíveis de blocos (cursor por id, sem offset).
    2. Para cada material com blocos pendentes:
       a. Atualiza `content_for_embedding` em todos os blocos do material e commita.
       b. Tenta `index_material(material_id)` (chamada idempotente).
       c. Só marca `embedding_version=TARGET_VERSION` em ContentBlock E em
          DocumentEmbedding APÓS o reindex retornar sucesso.
    Falhas em um material não impedem o reembed dos demais e NÃO marcam blocos
    com a nova versão (próxima execução tentará novamente).
    """
    from database.database import SessionLocal
    from database.models import ContentBlock, Material, Product
    from sqlalchemy import text as sql_text
    from services.product_ingestor import get_product_ingestor

    ingestor = get_product_ingestor()
    db = SessionLocal()
    processed_blocks = 0
    upgraded_blocks = 0
    materials_done = 0
    reindex_failed = 0

    materials_to_blocks: dict = {}
    try:
        for block in _iter_blocks(db, product_id, batch, force=force):
            processed_blocks += 1
            materials_to_blocks.setdefault(block.material_id, []).append(block)

        for mid, blocks in materials_to_blocks.items():
            material = db.query(Material).filter(Material.id == mid).first()
            if not material:
                continue
            product = db.query(Product).filter(Product.id == material.product_id).first()
            if not product:
                continue

            for block in blocks:
                md = _markdown_for_block(ingestor, block, product.name, product.ticker)
                if md is not None:
                    block.content_for_embedding = md
            if not dry_run:
                db.commit()

            if dry_run:
                upgraded_blocks += len(blocks)
                continue

            try:
                # Task #153 — método correto é `index_approved_blocks` (não existe `index_material`).
                ingestor.index_approved_blocks(
                    material_id=mid,
                    product_name=product.name,
                    product_ticker=product.ticker,
                    db=db,
                )
            except Exception as e:
                reindex_failed += 1
                print(f"[REEMBED] Reindex falhou material {mid} — blocos NÃO marcados v{TARGET_VERSION}: {e}")
                time.sleep(sleep)
                continue

            block_ids = [b.id for b in blocks]
            db.query(ContentBlock).filter(ContentBlock.id.in_(block_ids)).update(
                {ContentBlock.embedding_version: TARGET_VERSION},
                synchronize_session=False,
            )
            db.execute(
                sql_text(
                    "UPDATE document_embeddings SET embedding_version = :v "
                    "WHERE material_id = :mid"
                ),
                {"v": TARGET_VERSION, "mid": str(mid)},
            )
            db.commit()
            upgraded_blocks += len(blocks)
            materials_done += 1
            time.sleep(sleep / 2)

        return {
            "processed_blocks": processed_blocks,
            "upgraded_blocks": upgraded_blocks,
            "materials_reindexed": materials_done,
            "reindex_failed": reindex_failed,
            "dry_run": dry_run,
            "target_version": TARGET_VERSION,
        }
    finally:
        db.close()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Reembedding idempotente — Task #152")
    parser.add_argument("--batch", type=int, default=50)
    parser.add_argument("--sleep", type=float, default=1.5, help="Segundos entre lotes (proteção rate-limit)")
    parser.add_argument("--product-id", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Reembeda TODOS os blocos aprovados, ignorando o filtro por "
            "embedding_version. Útil quando o pipeline de indexação ganhou "
            "novos campos de metadata e precisamos repropagar (Task #153)."
        ),
    )
    args = parser.parse_args(argv)

    summary = run(
        batch=args.batch,
        sleep=args.sleep,
        product_id=args.product_id,
        dry_run=args.dry_run,
        force=args.force,
    )
    print("[REEMBED] Resumo:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
