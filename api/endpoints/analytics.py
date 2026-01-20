"""
Endpoints para o dashboard de analytics.
Fornece métricas e indicadores de controle.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, timedelta
from database.database import get_db
from database import crud
from api.endpoints.auth import get_current_user, require_role
from database.models import User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
async def get_analytics_summary(
    start_date: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "broker"]))
):
    """
    Retorna resumo dos indicadores principais.
    """
    summary = crud.get_analytics_summary(db, start_date, end_date)
    return summary


@router.get("/resolution-time")
async def get_resolution_time(
    start_date: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "broker"]))
):
    """
    Retorna tempo médio de resolução por assessor.
    """
    data = crud.get_resolution_time_by_broker(db, start_date, end_date)
    return {"brokers": data}


@router.get("/tickets-by-category")
async def get_tickets_by_category(
    start_date: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "broker"]))
):
    """
    Retorna distribuição de tickets por categoria.
    """
    data = crud.get_tickets_by_category(db, start_date, end_date)
    return {"categories": data}


@router.get("/categories")
async def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """
    Lista todas as categorias disponíveis.
    """
    categories = crud.get_categories(db)
    return [
        {
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "color": cat.color
        }
        for cat in categories
    ]
