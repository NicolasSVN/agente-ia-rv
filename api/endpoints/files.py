from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import MaterialFile, Material

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/{material_id}/download")
async def download_material_file(material_id: int, db: Session = Depends(get_db)):
    material_file = db.query(MaterialFile).filter(
        MaterialFile.material_id == material_id
    ).first()

    if not material_file:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    return Response(
        content=material_file.file_data,
        media_type=material_file.content_type,
        headers={
            "Content-Disposition": f'inline; filename="{material_file.filename}"',
            "Content-Length": str(material_file.file_size),
            "Cache-Control": "public, max-age=3600",
        }
    )
