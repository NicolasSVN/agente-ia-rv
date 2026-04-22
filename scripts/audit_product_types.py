"""
Auditoria: lista produtos com `product_type` vazio/NULL ou definido como
'outro', que merecem revisão manual no Knowledge Base UI.

Saída: tabela em texto puro com ID, ticker, nome, manager e tipo atual,
agrupada por categoria (NULL/'outro').

Uso:
    python scripts/audit_product_types.py [--limit 200]
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(limit: int) -> None:
    from database.database import SessionLocal
    from database.models import Product
    from sqlalchemy import or_

    db = SessionLocal()
    try:
        print("=== Auditoria de Product.product_type ===\n")

        nulls = (
            db.query(Product)
            .filter(or_(Product.product_type.is_(None), Product.product_type == ""))
            .order_by(Product.id.asc())
            .limit(limit)
            .all()
        )
        outros = (
            db.query(Product)
            .filter(Product.product_type == "outro")
            .order_by(Product.id.asc())
            .limit(limit)
            .all()
        )

        def _print_group(title: str, rows: list) -> None:
            print(f"\n--- {title} ({len(rows)}) ---")
            if not rows:
                print("Nenhum produto encontrado nesta categoria.")
                return
            print(f"{'ID':>5}  {'TICKER':<10}  {'TIPO':<11}  NOME  |  GESTOR")
            for p in rows:
                print(
                    f"{p.id:>5}  {(p.ticker or '—'):<10}  "
                    f"{(p.product_type or 'NULL'):<11}  "
                    f"{(p.name or '—')[:60]}  |  {(p.manager or '—')[:40]}"
                )

        _print_group("Sem product_type (NULL ou vazio)", nulls)
        _print_group("Com product_type = 'outro' (verificar se é o tipo correto)", outros)

        total = len(nulls) + len(outros)
        print(f"\nTotal a revisar: {total} (limite por grupo: {limit})")
        if total == 0:
            print("[OK] Todos os produtos têm tipo específico definido.")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Lista produtos sem product_type ou marcados como 'outro'."
    )
    parser.add_argument("--limit", type=int, default=500, help="Máximo por grupo.")
    args = parser.parse_args()
    main(limit=args.limit)
