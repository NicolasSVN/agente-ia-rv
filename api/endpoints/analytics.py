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
    current_user: User = Depends(require_role(["admin", "broker", "gestao_rv"]))
):
    """
    Retorna resumo dos indicadores principais.
    Brokers veem apenas seus próprios dados.
    """
    broker_filter = int(current_user.id) if str(current_user.role) == "broker" else None
    summary = crud.get_analytics_summary(db, start_date, end_date, broker_id=broker_filter)
    return summary


@router.get("/resolution-time")
async def get_resolution_time(
    start_date: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "broker", "gestao_rv"]))
):
    """
    Retorna tempo médio de resolução por assessor.
    Brokers veem apenas seus próprios dados.
    """
    broker_filter = int(current_user.id) if str(current_user.role) == "broker" else None
    data = crud.get_resolution_time_by_broker(db, start_date, end_date, broker_id=broker_filter)
    return {"brokers": data}


@router.get("/tickets-by-category")
async def get_tickets_by_category(
    start_date: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "broker", "gestao_rv"]))
):
    """
    Retorna distribuição de tickets por categoria.
    Brokers veem apenas seus próprios dados.
    """
    broker_filter = int(current_user.id) if str(current_user.role) == "broker" else None
    data = crud.get_tickets_by_category(db, start_date, end_date, broker_id=broker_filter)
    return {"categories": data}


@router.get("/categories")
async def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "gestao_rv"]))
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
