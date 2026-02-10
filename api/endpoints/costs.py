"""
Endpoints para Central de Custos.
Métricas de custos variáveis (APIs) e custos fixos mensais.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional

from database.database import get_db
from database.models import User, CostTracking, FixedCost
from api.endpoints.auth import get_current_user
from services.cost_tracker import OPENAI_PRICING, TAVILY_PRICING

router = APIRouter(prefix="/api/costs", tags=["costs"])


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return current_user


@router.get("/summary")
async def get_cost_summary(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    date_end = datetime.utcnow()
    date_start = date_end - timedelta(days=days)

    base_query = db.query(CostTracking).filter(
        CostTracking.created_at >= date_start,
        CostTracking.created_at <= date_end
    )

    totals = db.query(
        func.coalesce(func.sum(CostTracking.cost_brl), 0).label('total_brl'),
        func.coalesce(func.sum(CostTracking.cost_usd), 0).label('total_usd')
    ).filter(
        CostTracking.created_at >= date_start,
        CostTracking.created_at <= date_end
    ).first()

    variable_costs_brl = float(totals.total_brl)
    variable_costs_usd = float(totals.total_usd)

    by_service = db.query(
        CostTracking.service,
        func.coalesce(func.sum(CostTracking.cost_brl), 0).label('cost_brl'),
        func.coalesce(func.sum(CostTracking.cost_usd), 0).label('cost_usd'),
        func.count(CostTracking.id).label('count')
    ).filter(
        CostTracking.created_at >= date_start,
        CostTracking.created_at <= date_end
    ).group_by(CostTracking.service).all()

    by_operation = db.query(
        CostTracking.operation,
        CostTracking.model,
        func.coalesce(func.sum(CostTracking.cost_brl), 0).label('cost_brl'),
        func.count(CostTracking.id).label('count')
    ).filter(
        CostTracking.created_at >= date_start,
        CostTracking.created_at <= date_end
    ).group_by(CostTracking.operation, CostTracking.model).all()

    fixed_costs_list = db.query(FixedCost).filter(FixedCost.is_active == True).all()
    fixed_costs_brl = sum(fc.monthly_cost_brl for fc in fixed_costs_list)

    total_cost_brl = variable_costs_brl + fixed_costs_brl

    return {
        "period": {
            "start": date_start.isoformat(),
            "end": date_end.isoformat(),
            "days": days
        },
        "total_cost_brl": round(total_cost_brl, 2),
        "total_cost_usd": round(variable_costs_usd, 2),
        "variable_costs_brl": round(variable_costs_brl, 2),
        "fixed_costs_brl": round(fixed_costs_brl, 2),
        "by_service": [
            {
                "service": row.service,
                "cost_brl": round(float(row.cost_brl), 2),
                "cost_usd": round(float(row.cost_usd), 2),
                "count": row.count
            }
            for row in by_service
        ],
        "by_operation": [
            {
                "operation": row.operation,
                "model": row.model,
                "cost_brl": round(float(row.cost_brl), 2),
                "count": row.count
            }
            for row in by_operation
        ],
        "fixed_costs": [
            {
                "name": fc.name,
                "monthly_cost_brl": fc.monthly_cost_brl,
                "category": fc.category
            }
            for fc in fixed_costs_list
        ]
    }


@router.get("/daily")
async def get_daily_costs(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    date_end = datetime.utcnow()
    date_start = date_end - timedelta(days=days)

    results = db.query(
        func.date(CostTracking.created_at).label('date'),
        func.coalesce(func.sum(CostTracking.cost_brl), 0).label('cost_brl'),
        func.coalesce(func.sum(CostTracking.cost_usd), 0).label('cost_usd'),
        func.count(CostTracking.id).label('count')
    ).filter(
        CostTracking.created_at >= date_start,
        CostTracking.created_at <= date_end
    ).group_by(
        func.date(CostTracking.created_at)
    ).order_by(
        func.date(CostTracking.created_at)
    ).all()

    return [
        {
            "date": str(row.date),
            "cost_brl": round(float(row.cost_brl), 2),
            "cost_usd": round(float(row.cost_usd), 2),
            "count": row.count
        }
        for row in results
    ]


@router.get("/breakdown")
async def get_cost_breakdown(
    days: int = Query(30, ge=1, le=365),
    service: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    date_end = datetime.utcnow()
    date_start = date_end - timedelta(days=days)

    query = db.query(
        CostTracking.service,
        CostTracking.operation,
        CostTracking.model,
        func.coalesce(func.sum(CostTracking.cost_brl), 0).label('cost_brl'),
        func.coalesce(func.sum(CostTracking.cost_usd), 0).label('cost_usd'),
        func.coalesce(func.sum(CostTracking.prompt_tokens), 0).label('total_prompt_tokens'),
        func.coalesce(func.sum(CostTracking.completion_tokens), 0).label('total_completion_tokens'),
        func.coalesce(func.sum(CostTracking.total_tokens), 0).label('total_tokens'),
        func.count(CostTracking.id).label('count')
    ).filter(
        CostTracking.created_at >= date_start,
        CostTracking.created_at <= date_end
    )

    if service:
        query = query.filter(CostTracking.service == service)

    results = query.group_by(
        CostTracking.service,
        CostTracking.operation,
        CostTracking.model
    ).order_by(
        func.sum(CostTracking.cost_brl).desc()
    ).all()

    return [
        {
            "service": row.service,
            "operation": row.operation,
            "model": row.model,
            "cost_brl": round(float(row.cost_brl), 2),
            "cost_usd": round(float(row.cost_usd), 2),
            "total_prompt_tokens": int(row.total_prompt_tokens),
            "total_completion_tokens": int(row.total_completion_tokens),
            "total_tokens": int(row.total_tokens),
            "count": row.count
        }
        for row in results
    ]


@router.get("/fixed")
async def list_fixed_costs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    costs = db.query(FixedCost).order_by(FixedCost.created_at.desc()).all()
    return [
        {
            "id": fc.id,
            "name": fc.name,
            "description": fc.description,
            "monthly_cost_brl": fc.monthly_cost_brl,
            "category": fc.category,
            "is_active": fc.is_active,
            "plan_details": fc.plan_details,
            "created_at": fc.created_at.isoformat() if fc.created_at else None,
            "updated_at": fc.updated_at.isoformat() if fc.updated_at else None
        }
        for fc in costs
    ]


@router.post("/fixed")
async def create_fixed_cost(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    fc = FixedCost(
        name=data.get("name"),
        description=data.get("description"),
        monthly_cost_brl=data.get("monthly_cost_brl"),
        category=data.get("category", "infrastructure"),
        is_active=data.get("is_active", True),
        plan_details=data.get("plan_details")
    )
    if not fc.name or fc.monthly_cost_brl is None:
        raise HTTPException(status_code=400, detail="name e monthly_cost_brl são obrigatórios")
    db.add(fc)
    db.commit()
    db.refresh(fc)
    return {
        "id": fc.id,
        "name": fc.name,
        "description": fc.description,
        "monthly_cost_brl": fc.monthly_cost_brl,
        "category": fc.category,
        "is_active": fc.is_active,
        "plan_details": fc.plan_details,
        "created_at": fc.created_at.isoformat() if fc.created_at else None,
        "updated_at": fc.updated_at.isoformat() if fc.updated_at else None
    }


@router.put("/fixed/{cost_id}")
async def update_fixed_cost(
    cost_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    fc = db.query(FixedCost).filter(FixedCost.id == cost_id).first()
    if not fc:
        raise HTTPException(status_code=404, detail="Custo fixo não encontrado")
    
    if "name" in data:
        fc.name = data["name"]
    if "description" in data:
        fc.description = data["description"]
    if "monthly_cost_brl" in data:
        fc.monthly_cost_brl = data["monthly_cost_brl"]
    if "category" in data:
        fc.category = data["category"]
    if "is_active" in data:
        fc.is_active = data["is_active"]
    if "plan_details" in data:
        fc.plan_details = data["plan_details"]
    
    db.commit()
    db.refresh(fc)
    return {
        "id": fc.id,
        "name": fc.name,
        "description": fc.description,
        "monthly_cost_brl": fc.monthly_cost_brl,
        "category": fc.category,
        "is_active": fc.is_active,
        "plan_details": fc.plan_details,
        "created_at": fc.created_at.isoformat() if fc.created_at else None,
        "updated_at": fc.updated_at.isoformat() if fc.updated_at else None
    }


@router.delete("/fixed/{cost_id}")
async def delete_fixed_cost(
    cost_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    fc = db.query(FixedCost).filter(FixedCost.id == cost_id).first()
    if not fc:
        raise HTTPException(status_code=404, detail="Custo fixo não encontrado")
    db.delete(fc)
    db.commit()
    return {"detail": "Custo fixo removido com sucesso"}


@router.get("/pricing")
async def get_pricing_table(
    current_user: User = Depends(get_current_user)
):
    return {
        "openai": OPENAI_PRICING,
        "tavily": TAVILY_PRICING
    }
