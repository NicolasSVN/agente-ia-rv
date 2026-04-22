"""
Reembedding idempotente dos blocos de conteúdo (Task #152, robustecido na #161).

Para blocos com `embedding_version < TARGET_VERSION` (default 2):
1. Recalcula `content_for_embedding` (markdown para tabelas) e persiste no bloco.
2. Reindexa o bloco via ProductIngestor.
3. Marca o bloco com `embedding_version = TARGET_VERSION`.

É seguro rodar múltiplas vezes — só reprocessa o que ainda está em versão antiga.
Pode ser executado sob load (processa em lotes pequenos com sleep entre lotes).

Uso:
    python -u -m scripts.reembed_blocks --batch 50 --sleep 1.5
    python -u -m scripts.reembed_blocks --product-id 42
    python -u -m scripts.reembed_blocks --dry-run
    python -u -m scripts.reembed_blocks --force         # repropaga metadata novo

Notas de operação (Task #161):
- Cada material processado emite log com flush=True; se você não vê novas linhas
  por mais de ~30s, provavelmente um chamado ao vector store travou.
- Tempo esperado: ~0.3–1.5s por bloco (depende do provedor de embeddings).
  Para 330 blocos espere 2–8 minutos no total + sleep entre lotes.
- Sob load, prefira `--batch 25 --sleep 2.0` para reduzir contenção.
- Sempre rode com `python -u` (ou env PYTHONUNBUFFERED=1) para garantir que o
  stdout não fique bufferizado quando a saída é redirecionada para arquivo.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
import traceback
from typing import List, Optional

from sqlalchemy import or_

TARGET_VERSION = 2


def _log(msg: str) -> None:
    """Print com flush imediato — seguro mesmo se stdout estiver bufferizado."""
    print(msg, flush=True)
    try:
        sys.stdout.flush()
    except Exception:
        pass


def _install_signal_handlers(state: dict) -> None:
    """
    Garante que SIGTERM/SIGINT imprimam um snapshot do progresso antes de morrer.
    Isso responde diretamente à Task #161 — antes, o processo morria silencioso
    quando o ambiente o terminava.
    """
    def _handler(signum, _frame):
        _log(f"[REEMBED] Recebido sinal {signum} — abortando. Snapshot: {json.dumps(state, ensure_ascii=False)}")
        sys.exit(130 if signum == signal.SIGINT else 143)

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _handler)
        except (ValueError, OSError):
            # Pode falhar fora da main thread — não é fatal.
            pass


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
    page = 0
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
        page += 1
        _log(f"[REEMBED] Coleta página {page}: {len(rows)} blocos (last_id={last_id})")
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
        _log(f"[REEMBED] Falha gerar markdown bloco {block.id}: {e}")
        return None


def run(batch: int, sleep: float, product_id: Optional[int], dry_run: bool, force: bool = False) -> dict:
    """
    Estratégia segura (Task #152):
    1. Coleta IDs elegíveis de blocos (cursor por id, sem offset).
    2. Para cada material com blocos pendentes:
       a. Atualiza `content_for_embedding` em todos os blocos do material e commita.
       b. Tenta `index_approved_blocks(material_id)` (chamada idempotente).
       c. Só marca `embedding_version=TARGET_VERSION` em ContentBlock E em
          DocumentEmbedding APÓS o reindex retornar sucesso.
    Falhas em um material não impedem o reembed dos demais e NÃO marcam blocos
    com a nova versão (próxima execução tentará novamente).
    """
    from database.database import SessionLocal
    from database.models import ContentBlock, Material, Product
    from sqlalchemy import text as sql_text
    from services.product_ingestor import get_product_ingestor

    _log(
        f"[REEMBED] Iniciando run — batch={batch} sleep={sleep} "
        f"product_id={product_id} dry_run={dry_run} force={force} "
        f"target_version={TARGET_VERSION}"
    )

    ingestor = get_product_ingestor()
    db = SessionLocal()
    state = {
        "processed_blocks": 0,
        "upgraded_blocks": 0,
        "materials_reindexed": 0,
        "reindex_failed": 0,
        "dry_run": dry_run,
        "target_version": TARGET_VERSION,
        "force": force,
    }
    _install_signal_handlers(state)

    materials_to_blocks: dict = {}
    try:
        _log("[REEMBED] Fase 1/2 — coletando blocos elegíveis…")
        for block in _iter_blocks(db, product_id, batch, force=force):
            state["processed_blocks"] += 1
            materials_to_blocks.setdefault(block.material_id, []).append(block)
        _log(
            f"[REEMBED] Fase 1 concluída — {state['processed_blocks']} blocos em "
            f"{len(materials_to_blocks)} materiais."
        )

        if not materials_to_blocks:
            _log("[REEMBED] Nada a fazer. Saindo.")
            return state

        _log("[REEMBED] Fase 2/2 — reindexando por material…")
        total_materials = len(materials_to_blocks)
        for idx, (mid, blocks) in enumerate(materials_to_blocks.items(), start=1):
            material = db.query(Material).filter(Material.id == mid).first()
            if not material:
                _log(f"[REEMBED] [{idx}/{total_materials}] Material {mid} não encontrado — pulando.")
                continue
            product = db.query(Product).filter(Product.id == material.product_id).first()
            if not product:
                _log(f"[REEMBED] [{idx}/{total_materials}] Material {mid} sem produto — pulando.")
                continue

            _log(
                f"[REEMBED] [{idx}/{total_materials}] Material {mid} "
                f"({product.name}) — {len(blocks)} blocos"
            )

            t0 = time.time()
            for block in blocks:
                md = _markdown_for_block(ingestor, block, product.name, product.ticker)
                if md is not None:
                    block.content_for_embedding = md
            if not dry_run:
                db.commit()

            if dry_run:
                state["upgraded_blocks"] += len(blocks)
                _log(f"[REEMBED]   dry-run: marcaria {len(blocks)} blocos.")
                continue

            try:
                # Task #153 — método correto é `index_approved_blocks` (não existe `index_material`).
                result = ingestor.index_approved_blocks(
                    material_id=mid,
                    product_name=product.name,
                    product_ticker=product.ticker,
                    db=db,
                )
            except Exception as e:
                state["reindex_failed"] += 1
                _log(
                    f"[REEMBED]   ✗ Reindex falhou material {mid} — "
                    f"blocos NÃO marcados v{TARGET_VERSION}: {e}"
                )
                _log(traceback.format_exc())
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
            state["upgraded_blocks"] += len(blocks)
            state["materials_reindexed"] += 1
            elapsed = time.time() - t0
            indexed = (result or {}).get("indexed_count", "?") if isinstance(result, dict) else "?"
            _log(
                f"[REEMBED]   ✓ ok ({elapsed:.1f}s, indexed={indexed}, "
                f"acumulado upgraded={state['upgraded_blocks']})"
            )
            time.sleep(sleep / 2)

        return state
    finally:
        db.close()


def main(argv: Optional[List[str]] = None) -> int:
    # Garantia adicional contra buffering quando o script é executado sem `-u`.
    try:
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
        sys.stderr.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    except Exception:
        pass
    if not os.environ.get("PYTHONUNBUFFERED"):
        os.environ["PYTHONUNBUFFERED"] = "1"

    parser = argparse.ArgumentParser(description="Reembedding idempotente — Task #152/#161")
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

    try:
        summary = run(
            batch=args.batch,
            sleep=args.sleep,
            product_id=args.product_id,
            dry_run=args.dry_run,
            force=args.force,
        )
    except Exception as e:
        _log(f"[REEMBED] ✗ Falha não tratada: {e}")
        _log(traceback.format_exc())
        return 1

    _log("[REEMBED] Resumo:")
    _log(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
