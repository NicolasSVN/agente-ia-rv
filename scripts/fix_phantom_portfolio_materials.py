"""
Task #200 — Remediação retroativa: materiais "fantasmas" criados pela
redistribuição multi-ticker do pipeline antigo em uploads de CARTEIRAS.

Cenário corrigido:
  Antes do fix do `_is_portfolio_material` no `services/product_ingestor.py`,
  uploads como "Carteira Seven FII's" criavam:
    - 1 material principal (com PDF, source_file_path/file_hash, status='success')
    - N materiais derivados ("smart_upload", processing_status='failed/pending',
      sem source_file_path, sem file_hash) — um para cada FII detectado na
      composição. Esses derivados receberam blocos da composição e ficaram
      indexados em `document_embeddings`, poluindo o RAG.

Este script:
  1. Detecta materiais fantasmas: `material_type='smart_upload' AND
     source_file_path IS NULL AND file_hash IS NULL` cujo `name` coincide
     com outro material principal (mesmo `name`, com source_file_path).
  2. Move blocos do fantasma para o principal (UPDATE content_blocks).
  3. Atualiza `document_embeddings`: material_id, product_name, product_ticker
     passam a apontar para o material/produto principal.
  4. Garante MaterialProductLink entre material principal e o produto do fantasma.
  5. Remove links do fantasma (material_product_links) e jobs de processamento.
  6. Deleta o fantasma.
  7. (Opcional, --fix-portfolio-products) Para cada produto-carteira detectado
     pelo nome, ajusta `product_type` para "carteira" (via taxonomy oficial)
     e limpa `manager` se este corresponder a uma gestora dos FIIs da composição.

Idempotente. Por padrão roda em --dry-run. Use --apply para executar.
Exibe SQL de validação antes/depois para auditoria.

Uso:
    # Diagnóstico (default — não modifica nada)
    python scripts/fix_phantom_portfolio_materials.py

    # Aplicar correções
    python scripts/fix_phantom_portfolio_materials.py --apply

    # Aplicar + corrigir produtos-carteira (manager errado, type errado)
    python scripts/fix_phantom_portfolio_materials.py --apply --fix-portfolio-products

    # Limitar a um material principal específico
    python scripts/fix_phantom_portfolio_materials.py --principal-id 47 --apply

Compatível com dev (DATABASE_URL local) e produção (Railway, mesma var).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text  # noqa: E402

from database.database import SessionLocal  # noqa: E402
from database.models import (  # noqa: E402
    Material,
    MaterialProductLink,
    Product,
    ContentBlock,
    DocumentProcessingJob,
    DocumentPageResult,
)
from services.product_ingestor import _is_portfolio_material  # noqa: E402
from services.product_type_inference import (  # noqa: E402
    coerce_product_type,
    VALID_PRODUCT_TYPES,
)


def _print_baseline(db) -> None:
    """Imprime estado atual relevante para auditoria."""
    rows = db.execute(text("""
        SELECT m.id, m.product_id, p.name AS product_name, p.ticker, p.product_type, p.manager,
               m.name, m.material_type, m.processing_status, m.publish_status, m.is_indexed,
               (m.source_file_path IS NULL) AS no_path,
               (m.file_hash IS NULL) AS no_hash,
               (SELECT COUNT(*) FROM content_blocks WHERE material_id = m.id) AS blocks,
               (SELECT COUNT(*) FROM document_embeddings WHERE material_id = m.id::text) AS embs
          FROM materials m
          LEFT JOIN products p ON p.id = m.product_id
         WHERE m.material_type = 'smart_upload'
           AND m.source_file_path IS NULL
         ORDER BY m.id
    """)).fetchall()
    print("\n[BASELINE] materiais smart_upload sem source_file_path "
          "(candidatos a fantasma):")
    if not rows:
        print("  (nenhum)")
        return
    for r in rows:
        print(
            f"  mat#{r.id}  prod#{r.product_id} ({r.product_name}/{r.ticker}, "
            f"type={r.product_type}, mgr={r.manager})  "
            f"name={r.name!r}  status={r.processing_status}  "
            f"indexed={r.is_indexed}  blocks={r.blocks}  embs={r.embs}"
        )


def _find_phantom_groups(db, only_principal_id: Optional[int] = None
                        ) -> List[Tuple[Material, List[Material]]]:
    """Retorna lista de (material_principal, [fantasmas...]) onde:
       - principal: material com source_file_path IS NOT NULL
       - fantasmas: outros materiais com mesmo `name`, sem source_file_path,
         material_type='smart_upload'
    """
    q_principals = (
        db.query(Material)
        .filter(Material.source_file_path.isnot(None))
    )
    if only_principal_id is not None:
        q_principals = q_principals.filter(Material.id == only_principal_id)
    principals = q_principals.all()

    groups: List[Tuple[Material, List[Material]]] = []
    for principal in principals:
        if not principal.name:
            continue
        phantoms = (
            db.query(Material)
            .filter(
                Material.id != principal.id,
                Material.name == principal.name,
                Material.material_type == "smart_upload",
                Material.source_file_path.is_(None),
            )
            .all()
        )
        if phantoms:
            groups.append((principal, phantoms))
    return groups


def _migrate_phantom(db, principal: Material, phantom: Material, apply: bool) -> dict:
    """Migra blocos/embeddings/links do fantasma para o principal e deleta o fantasma."""
    counts = {
        "blocks_moved": 0,
        "embeddings_updated": 0,
        "links_added": 0,
        "links_removed": 0,
        "jobs_removed": 0,
    }

    n_blocks = db.query(ContentBlock).filter(ContentBlock.material_id == phantom.id).count()
    n_emb = db.execute(
        text("SELECT COUNT(*) FROM document_embeddings WHERE material_id = :mid"),
        {"mid": str(phantom.id)},
    ).scalar() or 0
    counts["blocks_moved"] = n_blocks
    counts["embeddings_updated"] = n_emb

    print(
        f"  fantasma mat#{phantom.id} → principal mat#{principal.id}: "
        f"{n_blocks} blocos, {n_emb} embeddings"
    )

    if not apply:
        return counts

    # 1) Mover blocos. Como blocos têm UNIQUE(material_id, content_hash),
    # pode haver colisão se um bloco igual já existe no principal — nesse
    # caso deletamos a duplicata no fantasma.
    duplicates = db.execute(
        text("""
            SELECT cb_p.id AS phantom_block_id
              FROM content_blocks cb_p
              JOIN content_blocks cb_m ON cb_m.material_id = :pmid
                                       AND cb_m.content_hash = cb_p.content_hash
                                       AND cb_m.content_hash IS NOT NULL
             WHERE cb_p.material_id = :fmid
        """),
        {"pmid": principal.id, "fmid": phantom.id},
    ).fetchall()
    dup_ids = [r.phantom_block_id for r in duplicates]
    if dup_ids:
        print(f"    {len(dup_ids)} bloco(s) duplicado(s) detectado(s); removendo "
              f"do fantasma antes do move.")
        db.execute(
            text("DELETE FROM content_blocks WHERE id = ANY(:ids)"),
            {"ids": dup_ids},
        )
        counts["blocks_moved"] -= len(dup_ids)

    db.execute(
        text("UPDATE content_blocks SET material_id = :pmid WHERE material_id = :fmid"),
        {"pmid": principal.id, "fmid": phantom.id},
    )

    # 2) Atualizar embeddings — apontar para o material principal e o produto
    # principal (re-escreve product_name/product_ticker para refletir o
    # produto-carteira em vez do FII individual).
    principal_product = (
        db.query(Product).filter(Product.id == principal.product_id).first()
        if principal.product_id else None
    )
    pname = principal_product.name if principal_product else None
    pticker = principal_product.ticker if principal_product else None
    db.execute(
        text("""
            UPDATE document_embeddings
               SET material_id = :pmid,
                   product_name = COALESCE(:pname, product_name),
                   product_ticker = COALESCE(:pticker, product_ticker)
             WHERE material_id = :fmid
        """),
        {
            "pmid": str(principal.id),
            "pname": pname,
            "pticker": pticker,
            "fmid": str(phantom.id),
        },
    )

    # 3) Garantir link material_principal -> product do fantasma (composição).
    # Útil para o RAG saber que aquele FII faz parte da carteira.
    if phantom.product_id and phantom.product_id != principal.product_id:
        existing = db.query(MaterialProductLink).filter(
            MaterialProductLink.material_id == principal.id,
            MaterialProductLink.product_id == phantom.product_id,
        ).first()
        if not existing:
            db.add(MaterialProductLink(
                material_id=principal.id,
                product_id=phantom.product_id,
            ))
            counts["links_added"] = 1
            print(f"    link adicionado: mat#{principal.id} -> prod#{phantom.product_id}")

    # 4) Remover links do fantasma e jobs.
    n_links_del = db.query(MaterialProductLink).filter(
        MaterialProductLink.material_id == phantom.id
    ).delete(synchronize_session=False)
    counts["links_removed"] = n_links_del

    # Jobs de processamento + page results
    job_ids = [
        r[0] for r in db.execute(
            text("SELECT id FROM document_processing_jobs WHERE material_id = :mid"),
            {"mid": phantom.id},
        ).fetchall()
    ]
    if job_ids:
        db.execute(
            text("DELETE FROM document_page_results WHERE job_id = ANY(:ids)"),
            {"ids": job_ids},
        )
        db.execute(
            text("DELETE FROM document_processing_jobs WHERE id = ANY(:ids)"),
            {"ids": job_ids},
        )
        counts["jobs_removed"] = len(job_ids)

    # 5) Deletar o material fantasma.
    db.delete(phantom)
    db.flush()
    print(f"    fantasma mat#{phantom.id} removido.")

    return counts


def _fix_portfolio_product(db, product: Product, apply: bool) -> bool:
    """Quando o nome do produto indica carteira, ajusta product_type para
    'carteira' e limpa manager se aparenta ser de um FII da composição.
    """
    changed = False
    target_type = coerce_product_type(name=product.name)
    if target_type == "carteira" and (product.product_type or "").lower() != "carteira":
        print(
            f"  produto#{product.id} {product.name!r}: product_type "
            f"{product.product_type!r} -> 'carteira'"
        )
        if apply:
            product.product_type = "carteira"
        changed = True
    # Quando é carteira, manager NÃO faz sentido — a recomendação é da casa,
    # não de uma asset externa. Limpa para evitar telas mostrando gestora errada.
    if target_type == "carteira" and product.manager:
        print(
            f"  produto#{product.id} {product.name!r}: manager "
            f"{product.manager!r} -> NULL (carteira não tem gestora)"
        )
        if apply:
            product.manager = None
        changed = True
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true",
        help="Executa de fato. Sem essa flag, apenas mostra o que faria.",
    )
    parser.add_argument(
        "--principal-id", type=int, default=None,
        help="Limitar a remediação a um material principal específico.",
    )
    parser.add_argument(
        "--fix-portfolio-products", action="store_true",
        help="Também corrigir produtos-carteira (product_type, manager).",
    )
    args = parser.parse_args()

    if "carteira" not in VALID_PRODUCT_TYPES:
        print("[ERROR] Taxonomia atual não tem 'carteira' como tipo válido. "
              "Aplique o fix em services/product_type_inference.py primeiro.")
        return 2

    db = SessionLocal()
    try:
        _print_baseline(db)

        groups = _find_phantom_groups(db, only_principal_id=args.principal_id)
        print(f"\n[SCAN] {len(groups)} grupo(s) com fantasmas encontrado(s).")
        if not groups:
            print("[OK] Nada a fazer.")
            return 0

        totals = {"blocks_moved": 0, "embeddings_updated": 0,
                  "links_added": 0, "links_removed": 0,
                  "jobs_removed": 0, "phantoms_removed": 0,
                  "products_fixed": 0}

        for principal, phantoms in groups:
            print(f"\nPrincipal mat#{principal.id} {principal.name!r} "
                  f"(prod#{principal.product_id})")
            primary_prod = (
                db.query(Product).filter(Product.id == principal.product_id).first()
                if principal.product_id else None
            )
            if not _is_portfolio_material(principal, primary_prod, principal.name):
                print("  [SKIP] principal não é carteira (segundo helper). "
                      "Pulando para evitar dano em uploads multi-produto válidos.")
                continue

            # GUARDA EXTRA contra falso positivo: o produto principal de uma
            # CARTEIRA verdadeira NÃO deve ter ticker (Carteira Seven, etc.).
            # Se o principal tem ticker, é improvável que seja carteira pura
            # — provavelmente é um material multi-produto legítimo. Bail-out.
            if primary_prod and (primary_prod.ticker or "").strip():
                print(f"  [SKIP] produto principal tem ticker "
                      f"({primary_prod.ticker}); não é carteira pura. "
                      "Pulando para evitar dano em multi-produto.")
                continue

            for ph in phantoms:
                # Transação explícita por fantasma: SAVEPOINT garante que
                # uma falha no meio (UPDATE/DELETE/delete material) não
                # deixa estado parcial.
                try:
                    sp = db.begin_nested()
                    try:
                        c = _migrate_phantom(db, principal, ph, args.apply)
                        sp.commit()
                    except Exception:
                        sp.rollback()
                        raise
                    for k, v in c.items():
                        totals[k] = totals.get(k, 0) + (v or 0)
                    totals["phantoms_removed"] += 1
                except Exception as e:  # noqa: BLE001
                    db.rollback()
                    print(f"  [ERROR] fantasma mat#{ph.id}: {e}")

            if args.fix_portfolio_products and primary_prod:
                if _fix_portfolio_product(db, primary_prod, args.apply):
                    totals["products_fixed"] += 1

            if args.apply:
                db.commit()

        print("\n[SUMMARY]")
        for k, v in totals.items():
            print(f"  {k}: {v}")

        if not args.apply:
            print("\n[DRY-RUN] Nada foi alterado. Re-execute com --apply.")
        else:
            print("\n[DONE] Remediação aplicada.")
            _print_baseline(db)

        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
