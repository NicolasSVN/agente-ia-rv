"""
Migração de dados: infere e preenche `Product.product_type` para registros
existentes que estejam com NULL, vazio ou com valores legados (ex.: "Ação").

Usa o helper compartilhado em `services/product_type_inference.py` para garantir
que a heurística aplicada aqui é exatamente a mesma usada pelos endpoints de
auto-criação de produto.

Uso:
    python scripts/backfill_product_types.py [--dry-run]
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(dry_run: bool = False) -> None:
    from database.database import SessionLocal
    from database.models import Product
    from services.product_type_inference import (
        infer_product_type,
        normalize_product_type,
    )

    db = SessionLocal()
    try:
        print("=== Backfill de Product.product_type ===")
        print(f"Modo: {'DRY-RUN' if dry_run else 'EXECUÇÃO REAL'}\n")

        products = db.query(Product).all()
        total = len(products)
        normalized = 0
        inferred = 0
        unchanged = 0
        outro_after = 0
        changes_sample: list[tuple[int, str, str | None, str]] = []

        for p in products:
            current = (p.product_type or "").strip()
            new_value: str | None = None

            if current:
                norm = normalize_product_type(current)
                if norm:
                    if norm != current:
                        new_value = norm
                        normalized += 1
                    else:
                        unchanged += 1
                else:
                    # Valor existente não-canônico e não mapeável — força
                    # convergência ao conjunto válido via inferência.
                    new_value = infer_product_type(
                        ticker=p.ticker, name=p.name, description=p.description
                    )
                    inferred += 1
            else:
                new_value = infer_product_type(
                    ticker=p.ticker, name=p.name, description=p.description
                )
                inferred += 1

            if new_value:
                if new_value == "outro":
                    outro_after += 1
                if len(changes_sample) < 20:
                    changes_sample.append((p.id, p.ticker or "—", current or None, new_value))
                if not dry_run:
                    p.product_type = new_value

        if not dry_run:
            db.commit()

        print(f"Produtos analisados:       {total}")
        print(f"  - Inferidos (estavam vazios): {inferred}")
        print(f"  - Normalizados (alias→canon): {normalized}")
        print(f"  - Já corretos:                {unchanged}")
        print(f"  - Resultaram em 'outro':      {outro_after} (revisar manualmente)")

        if changes_sample:
            print("\nAmostra das alterações (até 20):")
            print(f"{'ID':>5}  {'TICKER':<10}  {'ANTES':<14}  →  DEPOIS")
            for pid, tk, before, after in changes_sample:
                print(f"{pid:>5}  {tk:<10}  {str(before):<14}  →  {after}")

        if not dry_run:
            print("\n[OK] Migração concluída.")
        else:
            print("\n[DRY-RUN] Nenhuma alteração foi salva.")

    except Exception as e:
        db.rollback()
        print(f"[ERRO] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Infere e preenche product_type para produtos sem tipo definido."
    )
    parser.add_argument("--dry-run", action="store_true", help="Executa sem salvar.")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
