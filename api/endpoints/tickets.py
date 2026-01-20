"""
Endpoints para gerenciamento de tickets/chamados.
Permite criar, listar, atualizar e deletar tickets.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database.database import get_db
from database import crud
from database.models import TicketStatus
from core.security import decode_token

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


class TicketCreate(BaseModel):
    """Schema para criação de ticket."""
    title: str
    description: Optional[str] = None
    client_id: Optional[int] = None
    client_phone: Optional[str] = None
    broker_id: Optional[int] = None


class TicketUpdate(BaseModel):
    """Schema para atualização de ticket."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    broker_id: Optional[int] = None


class TicketStatusUpdate(BaseModel):
    """Schema para atualização apenas do status."""
    status: str


class TicketResponse(BaseModel):
    """Schema para resposta de ticket."""
    id: int
    title: str
    description: Optional[str]
    status: str
    client_id: Optional[int]
    client_phone: Optional[str]
    broker_id: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


def get_current_staff(request: Request, db: Session = Depends(get_db)):
    """
    Dependency que verifica se o usuário atual é admin ou broker.
    Usado para proteger rotas do painel.
    """
    token = request.cookies.get("access_token")
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado"
        )
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    if payload.get("role") not in ["admin", "broker"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )
    
    return payload


@router.get("/", response_model=List[TicketResponse])
async def list_tickets(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_staff)
):
    """Lista todos os tickets."""
    if status:
        tickets = crud.get_tickets_by_status(db, status)
    else:
        tickets = crud.get_tickets(db, skip=skip, limit=limit)
    return tickets


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db)
):
    """Cria um novo ticket (pode ser chamado pelo webhook ou API)."""
    new_ticket = crud.create_ticket(
        db,
        title=ticket.title,
        description=ticket.description,
        client_id=ticket.client_id,
        client_phone=ticket.client_phone,
        broker_id=ticket.broker_id
    )
    return new_ticket


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_staff)
):
    """Busca um ticket por ID."""
    ticket = crud.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket não encontrado"
        )
    return ticket


@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_staff)
):
    """Atualiza um ticket."""
    ticket = crud.update_ticket(db, ticket_id, **ticket_update.model_dump(exclude_unset=True))
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket não encontrado"
        )
    return ticket


@router.patch("/{ticket_id}/status", response_model=TicketResponse)
async def update_ticket_status(
    ticket_id: int,
    status_update: TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_staff)
):
    """
    Atualiza apenas o status de um ticket.
    Usado pelo quadro Kanban para arrastar cards.
    """
    # Valida o status
    valid_statuses = [s.value for s in TicketStatus]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status inválido. Use: {', '.join(valid_statuses)}"
        )
    
    ticket = crud.update_ticket_status(db, ticket_id, status_update.status)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket não encontrado"
        )
    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_staff)
):
    """Deleta um ticket."""
    success = crud.delete_ticket(db, ticket_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket não encontrado"
        )
    return None
