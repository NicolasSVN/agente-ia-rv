"""
Centralised cleanup of all rows that reference a Material row.

Background
----------
Several FKs in the database point to ``materials.id`` (and to its child
``content_blocks.id``) without ``ON DELETE CASCADE``.  Whenever the application
needs to delete a material — either because the user pressed "Excluir" or
because the upload worker realised it was creating a "ghost" material that has
to be discarded — every one of those child rows must be removed manually,
otherwise PostgreSQL raises ``ForeignKeyViolation`` and the whole transaction
is rolled back.  In production this manifested as the upload pipeline dying
silently right after the user confirmed a duplicate file: the ghost material
stayed in ``processing`` forever, the new product/links never appeared and the
RAG index never received the new content.

This module gathers the cleanup logic in one place so both the admin
``DELETE /materials/{id}`` endpoint and the background worker can call it.

Two helpers are exposed:

``purge_material_dependencies(db, material_id)``
    Removes **every** child row that references the material so the caller can
    safely run ``db.delete(material); db.commit()`` afterwards.

``purge_processing_artifacts(db, material_id)``
    Removes only the rows that come from a previous processing attempt
    (blocks, versions, visual cache, jobs, page results, ingestion logs,
    queue items).  Keeps ``material_files`` (BYTEA backup), the
    ``material_product_links`` and ``material.product_id`` intact so the
    worker can resume / restart the processing of the same material without
    losing user-confirmed wiring.

Both helpers commit per-table to make a partial failure observable: if a brand
new child table is added in the future and we forget to extend this list, the
log line ``[CLEANUP_FAIL]`` will pin-point the offending table immediately.
"""

from __future__ import annotations

import logging
from typing import Iterable

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _log_fail(table: str, material_id: int, exc: Exception) -> None:
    """Emit a structured log line so production diagnostics can pin-point the
    table that blocked a delete.  Re-raising is the caller's responsibility —
    we only enrich the trace.
    """
    constraint = ""
    msg = str(exc) or ""
    # psycopg2 surfaces the constraint name in the exception message; extract
    # it heuristically so the operator does not need to read the full traceback.
    lower = msg.lower()
    if "constraint" in lower:
        # e.g. ... violates foreign key constraint "fk_xyz" on table "blah"
        try:
            after = msg.split("constraint", 1)[1]
            constraint = after.strip().split()[0].strip('"').strip("'")
        except Exception:
            constraint = ""
    logger.error(
        "[CLEANUP_FAIL] table=%s constraint=%s material_id=%s reason=%s",
        table,
        constraint or "?",
        material_id,
        type(exc).__name__,
    )


def _delete_vector_store_entries(block_ids: Iterable[int]) -> int:
    """Best-effort removal of pgvector entries keyed by ``product_block_<id>``.

    The vector store has its own session; never let a failure here stop the
    relational cleanup, but log it so it is visible in production.
    """
    removed = 0
    try:
        from services.vector_store import VectorStore

        vs = VectorStore()
        for bid in block_ids:
            try:
                vs.delete_document(f"product_block_{bid}")
                removed += 1
            except Exception as inner:
                logger.warning(
                    "[CLEANUP] vector_store delete falhou para block_id=%s: %s",
                    bid,
                    inner,
                )
    except Exception as outer:
        logger.warning(
            "[CLEANUP] vector_store indisponível para limpeza: %s", outer
        )
    return removed


def _list_block_ids(db: Session, material_id: int) -> list[int]:
    from database.models import ContentBlock

    rows = db.query(ContentBlock.id).filter(
        ContentBlock.material_id == material_id
    ).all()
    return [r[0] for r in rows]


def _list_job_ids(db: Session, material_id: int) -> list[int]:
    from database.models import DocumentProcessingJob

    rows = db.query(DocumentProcessingJob.id).filter(
        DocumentProcessingJob.material_id == material_id
    ).all()
    return [r[0] for r in rows]


def purge_processing_artifacts(db: Session, material_id: int) -> dict:
    """Remove processing-derived rows for ``material_id``.

    Keeps the ``Material`` row itself, its ``MaterialFile`` (BYTEA backup),
    ``MaterialProductLink`` rows and ``Material.product_id`` untouched.  Used
    by the worker to safely re-process an orphaned material whose previous run
    died half-way through (status=``processing`` with partial blocks).

    NOTE: Neither this helper nor ``purge_material_dependencies`` touches
    ``upload_queue_items`` (``PersistentQueueItem``).  Those rows belong to
    the upload-queue lifecycle, not to a processing run, and the worker
    often needs the active queue row to survive cleanup so it can persist
    progress / final status to the DB (e.g. the duplicate-blocked path,
    where the worker calls ``purge_material_dependencies + db.delete(mat)``
    and immediately afterwards calls ``_update_db_status`` to mark FAILED).
    The FK ``upload_queue_items.material_id`` has ``ON DELETE SET NULL``,
    so when a material is hard-deleted the queue rows are automatically
    nullified rather than orphaned at the relational level.  Callers that
    *do* want to discard the queue rows of a material being deleted (for
    hygiene) should issue an explicit DELETE on ``PersistentQueueItem``
    *before* invoking the helpers — see ``_delete_material_impl`` in
    ``api/endpoints/products.py`` for the canonical pattern.

    Returns a small dict with counts so the caller can log progress.
    """
    from database.models import (
        BlockVersion,
        ContentBlock,
        DocumentPageResult,
        DocumentProcessingJob,
        IngestionLog,
        PendingReviewItem,
        VisualCache,
    )

    counts: dict[str, int] = {}

    block_ids = _list_block_ids(db, material_id)
    job_ids = _list_job_ids(db, material_id)

    # 1. pgvector — indexed under the block id, so do this BEFORE we lose them.
    counts["vector_store"] = _delete_vector_store_entries(block_ids)

    # 2. document_page_results (FK to processing_jobs)
    if job_ids:
        try:
            counts["page_results"] = db.query(DocumentPageResult).filter(
                DocumentPageResult.job_id.in_(job_ids)
            ).delete(synchronize_session=False)
        except Exception as exc:
            db.rollback()
            _log_fail("document_page_results", material_id, exc)
            raise

    # 3. processing_jobs
    try:
        counts["processing_jobs"] = db.query(DocumentProcessingJob).filter(
            DocumentProcessingJob.material_id == material_id
        ).delete(synchronize_session=False)
    except Exception as exc:
        db.rollback()
        _log_fail("document_processing_jobs", material_id, exc)
        raise

    # 4. visual_cache → pending_review_items → block_versions → content_blocks
    if block_ids:
        for table_name, model, column in (
            ("visual_cache", VisualCache, VisualCache.content_block_id),
            ("pending_review_items", PendingReviewItem, PendingReviewItem.block_id),
            ("block_versions", BlockVersion, BlockVersion.block_id),
        ):
            try:
                counts[table_name] = db.query(model).filter(
                    column.in_(block_ids)
                ).delete(synchronize_session=False)
            except Exception as exc:
                db.rollback()
                _log_fail(table_name, material_id, exc)
                raise

        try:
            counts["content_blocks"] = db.query(ContentBlock).filter(
                ContentBlock.material_id == material_id
            ).delete(synchronize_session=False)
        except Exception as exc:
            db.rollback()
            _log_fail("content_blocks", material_id, exc)
            raise

    # 5. ingestion_logs (FK material_id, no cascade)
    try:
        counts["ingestion_logs"] = db.query(IngestionLog).filter(
            IngestionLog.material_id == material_id
        ).delete(synchronize_session=False)
    except Exception as exc:
        db.rollback()
        _log_fail("ingestion_logs", material_id, exc)
        raise

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        _log_fail("commit_processing_artifacts", material_id, exc)
        raise

    logger.info(
        "[CLEANUP] purge_processing_artifacts material_id=%s counts=%s",
        material_id,
        counts,
    )
    return counts


def purge_material_dependencies(db: Session, material_id: int) -> dict:
    """Remove every child row that references ``material_id`` so the caller
    can safely ``db.delete(material); db.commit()`` afterwards.

    Includes everything ``purge_processing_artifacts`` removes, plus:

    * ``material_product_links`` (multi-product wiring),
    * ``material_files`` (BYTEA backup),
    * ``campaign_structures.material_id`` (set to NULL — campaigns are
      preserved, just unlinked from the material).
    """
    from database.models import (
        CampaignStructure,
        MaterialFile,
        MaterialProductLink,
    )

    counts = purge_processing_artifacts(db, material_id)

    # campaign_structures: nullable FK, preserve campaign row.
    try:
        counts["campaign_structures_unlinked"] = db.query(CampaignStructure).filter(
            CampaignStructure.material_id == material_id
        ).update({"material_id": None}, synchronize_session=False)
    except Exception as exc:
        db.rollback()
        _log_fail("campaign_structures", material_id, exc)
        raise

    try:
        counts["material_product_links"] = db.query(MaterialProductLink).filter(
            MaterialProductLink.material_id == material_id
        ).delete(synchronize_session=False)
    except Exception as exc:
        db.rollback()
        _log_fail("material_product_links", material_id, exc)
        raise

    try:
        counts["material_files"] = db.query(MaterialFile).filter(
            MaterialFile.material_id == material_id
        ).delete(synchronize_session=False)
    except Exception as exc:
        db.rollback()
        _log_fail("material_files", material_id, exc)
        raise

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        _log_fail("commit_material_dependencies", material_id, exc)
        raise

    logger.info(
        "[CLEANUP] purge_material_dependencies material_id=%s counts=%s",
        material_id,
        counts,
    )
    return counts
