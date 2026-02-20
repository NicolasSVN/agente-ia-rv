"""
Validação de segurança para uploads de arquivos.
Verifica tipo MIME real (python-magic), tamanho e gera hash de integridade.
"""
import hashlib
import logging

from fastapi import UploadFile, HTTPException

logger = logging.getLogger("security")

MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

EXTENSION_TO_MIME = {
    ".pdf": {"application/pdf"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    ".xls": {"application/vnd.ms-excel"},
    ".csv": {"text/csv", "text/plain", "application/csv"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
}

try:
    import magic
    _magic_available = True
except ImportError:
    _magic_available = False
    logger.warning("python-magic not available, falling back to magic bytes check")

PDF_MAGIC_BYTES = b"%PDF"


def _detect_mime(content: bytes) -> str:
    if _magic_available:
        return magic.from_buffer(content, mime=True)
    if content[:4].startswith(PDF_MAGIC_BYTES):
        return "application/pdf"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if content[:2] == b"\xff\xd8":
        return "image/jpeg"
    return "application/octet-stream"


async def validate_upload(file: UploadFile, allowed_extensions: set = None) -> tuple:
    """
    Valida um arquivo de upload.
    Retorna (content: bytes, file_hash: str).
    Raises HTTPException se inválido.
    """
    if allowed_extensions is None:
        allowed_extensions = {".pdf"}

    filename = file.filename or ""
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo não permitido. Aceitos: {', '.join(allowed_extensions)}"
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo muito grande. Tamanho máximo: {MAX_FILE_SIZE_MB}MB"
        )

    if len(content) < 4:
        raise HTTPException(
            status_code=400,
            detail="Arquivo vazio ou corrompido"
        )

    detected_mime = _detect_mime(content)
    expected_mimes = EXTENSION_TO_MIME.get(ext, set())

    if expected_mimes and detected_mime not in expected_mimes:
        logger.warning(
            f"MIME mismatch: filename={filename}, ext={ext}, "
            f"detected={detected_mime}, expected={expected_mimes}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Conteúdo do arquivo não corresponde à extensão {ext}. "
                   f"O arquivo pode estar corrompido ou ter extensão incorreta."
        )

    file_hash = hashlib.sha256(content).hexdigest()

    return content, file_hash
