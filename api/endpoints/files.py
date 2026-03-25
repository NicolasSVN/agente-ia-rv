from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from urllib.parse import quote
from database.database import get_db
from database.models import MaterialFile, Material

router = APIRouter(prefix="/api/files", tags=["files"])


def safe_content_disposition(filename: str, disposition: str = "inline") -> str:
    sanitized = filename.replace("\r", "").replace("\n", "").replace("\0", "")
    if not sanitized.strip():
        sanitized = "documento.pdf"

    try:
        sanitized.encode("ascii")
        is_ascii = True
    except UnicodeEncodeError:
        is_ascii = False

    escaped = sanitized.replace("\\", "\\\\").replace('"', '\\"')

    if is_ascii:
        return f'{disposition}; filename="{escaped}"'

    ascii_fallback = sanitized.encode("ascii", errors="ignore").decode("ascii").strip()
    if not ascii_fallback or ascii_fallback == ".pdf":
        ascii_fallback = "documento.pdf"
    ascii_escaped = ascii_fallback.replace("\\", "\\\\").replace('"', '\\"')

    utf8_encoded = quote(sanitized, safe="")

    return f"{disposition}; filename=\"{ascii_escaped}\"; filename*=UTF-8''{utf8_encoded}"


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
            "Content-Disposition": safe_content_disposition(material_file.filename),
            "Content-Length": str(material_file.file_size),
            "Cache-Control": "public, max-age=3600",
        }
    )
