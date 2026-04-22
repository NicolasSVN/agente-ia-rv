"""
Re-rota um material que ficou erradamente vinculado ao ATIVO SUBJACENTE
em vez do produto-ESTRUTURA correspondente (ex.: "POP RAPT4.pdf" caiu no
produto research RAPT4 (ação) em vez de criar/usar "POP sobre RAPT4").

Idempotente. Por padrão roda em --dry-run e só explica o que faria.
Use --apply para executar.

Uso:
    python scripts/fix_misrouted_structure_material.py --material-id 123
    python scripts/fix_misrouted_structure_material.py --material-id 123 --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.models import Material, MaterialProductLink, Product  # noqa: E402
from database.database import SessionLocal  # noqa: E402
from services.upload_queue import UploadQueue  # noqa: E402


STRUCTURE_TYPES = {"estruturada", "estrutura", "estruturado"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--material-id", type=int, required=True)
    parser.add_argument("--apply", action="store_true",
                        help="Executa de fato. Sem essa flag, apenas explica.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        mat = db.query(Material).filter(Material.id == args.material_id).first()
        if not mat:
            print(f"[ERROR] Material id={args.material_id} não encontrado.")
            return 2

        filename_hint = (
            getattr(mat, "source_filename", None)
            or (Path(mat.source_file_path).name if mat.source_file_path else None)
            or mat.name
        )
        struct_kw = UploadQueue._detect_structure_in_name(
            filename_hint, mat.name, getattr(mat, "source_filename", None)
        )

        print(f"Material #{mat.id}: {mat.name!r}")
        print(f"  filename: {filename_hint!r}")
        print(f"  product_id atual: {mat.product_id}")
        print(f"  estrutura detectada: {struct_kw or 'NENHUMA'}")

        if not struct_kw:
            print("Nada a fazer: o material não parece ser uma estrutura.")
            return 0

        if not mat.product_id:
            print("Material sem produto vinculado — nada a desvincular. "
                  "Reprocesse via SmartUpload para criar a estrutura.")
            return 0

        linked = db.query(Product).filter(Product.id == mat.product_id).first()
        linked_type = (linked.product_type or "").lower() if linked else ""
        if linked and linked_type in STRUCTURE_TYPES:
            print(f"Vínculo já é estrutura ({linked.name}, type={linked.product_type}). "
                  "Nada a corrigir.")
            return 0

        print(f"  produto vinculado: {linked.name if linked else '?'} "
              f"(type={linked.product_type if linked else '?'})")
        print(f"  → Vai DESVINCULAR e o worker criará a estrutura no próximo "
              f"reprocessamento.")

        if not args.apply:
            print("\n[DRY-RUN] Use --apply para executar.")
            return 0

        if linked:
            db.query(MaterialProductLink).filter(
                MaterialProductLink.material_id == mat.id,
                MaterialProductLink.product_id == linked.id,
            ).delete()
        mat.product_id = None
        db.commit()
        print(f"[OK] Material #{mat.id} desvinculado de {linked.name if linked else '?'}.")
        print("     Reprocesse o material para que a estrutura seja criada/encontrada.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
