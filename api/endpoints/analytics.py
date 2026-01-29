"""
Endpoints para o dashboard de analytics.
Fornece métricas e indicadores de controle.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, timedelta
from database.database import get_db
from database import crud
from api.endpoints.auth import get_current_user, require_role
from database.models import User, RetrievalLog, IngestionLog

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


@router.get("/rag-metrics")
async def get_rag_metrics(
    start_date: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "gestao_rv"]))
):
    """
    Retorna métricas do sistema RAG: buscas, transferências humanas, ingestões.
    """
    query = db.query(RetrievalLog)
    
    if start_date:
        query = query.filter(RetrievalLog.created_at >= start_date)
    if end_date:
        query = query.filter(RetrievalLog.created_at <= end_date)
    
    total_queries = query.count()
    human_transfers = query.filter(RetrievalLog.human_transfer == True).count()
    
    transfer_reasons = db.query(
        RetrievalLog.transfer_reason,
        func.count(RetrievalLog.id).label('count')
    ).filter(
        RetrievalLog.human_transfer == True
    ).group_by(RetrievalLog.transfer_reason).all()
    
    query_types = db.query(
        RetrievalLog.query_type,
        func.count(RetrievalLog.id).label('count')
    ).group_by(RetrievalLog.query_type).all()
    
    avg_response_time = db.query(
        func.avg(RetrievalLog.response_time_ms)
    ).scalar() or 0
    
    ingestion_query = db.query(IngestionLog)
    if start_date:
        ingestion_query = ingestion_query.filter(IngestionLog.created_at >= start_date)
    if end_date:
        ingestion_query = ingestion_query.filter(IngestionLog.created_at <= end_date)
    
    total_ingestions = ingestion_query.count()
    
    blocks_query = db.query(func.sum(IngestionLog.blocks_created))
    pending_query = db.query(func.sum(IngestionLog.blocks_pending_review))
    tables_query = db.query(func.sum(IngestionLog.tables_detected))
    charts_query = db.query(func.sum(IngestionLog.charts_detected))
    
    if start_date:
        blocks_query = blocks_query.filter(IngestionLog.created_at >= start_date)
        pending_query = pending_query.filter(IngestionLog.created_at >= start_date)
        tables_query = tables_query.filter(IngestionLog.created_at >= start_date)
        charts_query = charts_query.filter(IngestionLog.created_at >= start_date)
    if end_date:
        blocks_query = blocks_query.filter(IngestionLog.created_at <= end_date)
        pending_query = pending_query.filter(IngestionLog.created_at <= end_date)
        tables_query = tables_query.filter(IngestionLog.created_at <= end_date)
        charts_query = charts_query.filter(IngestionLog.created_at <= end_date)
    
    total_blocks_created = blocks_query.scalar() or 0
    total_pending_review = pending_query.scalar() or 0
    total_tables_detected = tables_query.scalar() or 0
    total_charts_detected = charts_query.scalar() or 0
    
    return {
        "retrieval": {
            "total_queries": total_queries,
            "human_transfers": human_transfers,
            "transfer_rate": round(human_transfers / total_queries * 100, 2) if total_queries > 0 else 0,
            "avg_response_time_ms": round(float(avg_response_time), 2),
            "query_types": [{"type": qt[0] or "unknown", "count": qt[1]} for qt in query_types],
            "transfer_reasons": [{"reason": tr[0] or "unknown", "count": tr[1]} for tr in transfer_reasons]
        },
        "ingestion": {
            "total_documents": total_ingestions,
            "total_blocks_created": int(total_blocks_created),
            "total_pending_review": int(total_pending_review),
            "tables_detected": int(total_tables_detected),
            "charts_detected": int(total_charts_detected)
        }
    }
