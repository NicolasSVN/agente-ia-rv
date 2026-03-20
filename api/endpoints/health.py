from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.endpoints.auth import get_current_user
from database.models import User

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("/detailed")
async def health_detailed():
    from services.dependency_check import get_detailed_health
    result = get_detailed_health()

    status_code = 200
    if result["status"] == "critical":
        status_code = 503
    elif result["status"] == "degraded":
        status_code = 200

    return JSONResponse(content=result, status_code=status_code)


@router.get("/openai-status")
async def get_openai_status(current_user: User = Depends(get_current_user)):
    from services.dependency_check import get_openai_status_cache
    return get_openai_status_cache()


@router.post("/openai-acknowledge")
async def acknowledge_openai(current_user: User = Depends(get_current_user)):
    if current_user.role not in ("admin", "gerente"):
        return JSONResponse(status_code=403, content={"detail": "Apenas administradores podem reconhecer alertas"})
    from services.dependency_check import acknowledge_openai_status
    acknowledge_openai_status(username=current_user.username)
    return {"success": True, "message": "Status OpenAI reconhecido com sucesso"}
