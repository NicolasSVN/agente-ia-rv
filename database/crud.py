"""
Funções CRUD (Create, Read, Update, Delete) para usuários e tickets.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from database.models import User, Ticket, TicketStatus
from core.security import get_password_hash, verify_password


# ========== CRUD de Usuários ==========

def get_user(db: Session, user_id: int) -> Optional[User]:
    """Busca um usuário pelo ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Busca um usuário pelo nome de usuário."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Busca um usuário pelo email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
    """Busca um usuário pelo número de telefone."""
    return db.query(User).filter(User.phone == phone).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Lista todos os usuários com paginação."""
    return db.query(User).offset(skip).limit(limit).all()


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    phone: Optional[str] = None,
    role: str = "client"
) -> User:
    """Cria um novo usuário com senha hasheada."""
    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        phone=phone,
        role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
    """Atualiza um usuário existente."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    for key, value in kwargs.items():
        if hasattr(db_user, key) and value is not None:
            if key == "password":
                setattr(db_user, "hashed_password", get_password_hash(value))
            else:
                setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    """Deleta um usuário pelo ID."""
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Autentica um usuário verificando username e senha."""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ========== CRUD de Tickets ==========

def get_ticket(db: Session, ticket_id: int) -> Optional[Ticket]:
    """Busca um ticket pelo ID."""
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def get_tickets(db: Session, skip: int = 0, limit: int = 100) -> List[Ticket]:
    """Lista todos os tickets com paginação."""
    return db.query(Ticket).offset(skip).limit(limit).all()


def get_tickets_by_status(db: Session, status: str) -> List[Ticket]:
    """Lista tickets por status."""
    return db.query(Ticket).filter(Ticket.status == status).all()


def get_tickets_by_broker(db: Session, broker_id: int) -> List[Ticket]:
    """Lista tickets atribuídos a um broker específico."""
    return db.query(Ticket).filter(Ticket.broker_id == broker_id).all()


def create_ticket(
    db: Session,
    title: str,
    description: Optional[str] = None,
    client_id: Optional[int] = None,
    client_phone: Optional[str] = None,
    broker_id: Optional[int] = None
) -> Ticket:
    """Cria um novo ticket."""
    db_ticket = Ticket(
        title=title,
        description=description,
        client_id=client_id,
        client_phone=client_phone,
        broker_id=broker_id,
        status=TicketStatus.OPEN.value
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def update_ticket_status(db: Session, ticket_id: int, status: str) -> Optional[Ticket]:
    """Atualiza o status de um ticket."""
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None
    db_ticket.status = status
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def update_ticket(db: Session, ticket_id: int, **kwargs) -> Optional[Ticket]:
    """Atualiza um ticket existente."""
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None
    
    for key, value in kwargs.items():
        if hasattr(db_ticket, key) and value is not None:
            setattr(db_ticket, key, value)
    
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def delete_ticket(db: Session, ticket_id: int) -> bool:
    """Deleta um ticket pelo ID."""
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return False
    db.delete(db_ticket)
    db.commit()
    return True
