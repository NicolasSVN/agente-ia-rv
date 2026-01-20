"""
Webhook para receber mensagens do WhatsApp via WAHA.
Processa mensagens e gera respostas usando a IA.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from database.database import get_db
from database import crud
from services.whatsapp_client import whatsapp_client
from services.openai_agent import openai_agent

router = APIRouter(prefix="/api/webhook", tags=["WhatsApp Webhook"])

# Armazena histórico de conversas em memória (em produção, usar Redis ou banco de dados)
conversation_history: Dict[str, list] = {}


class WAHAMessage(BaseModel):
    """Schema para mensagem recebida do WAHA."""
    event: str
    session: str
    payload: Dict[str, Any]


class WebhookPayload(BaseModel):
    """Schema alternativo para payload do webhook."""
    from_: Optional[str] = None
    body: Optional[str] = None
    chatId: Optional[str] = None
    
    class Config:
        populate_by_name = True


async def process_message(phone: str, message: str, db: Session):
    """
    Processa uma mensagem recebida e envia resposta.
    Esta função é executada em background para não bloquear o webhook.
    """
    try:
        # Indica que está digitando
        await whatsapp_client.start_typing(phone)
        
        # Recupera histórico da conversa
        history = conversation_history.get(phone, [])
        
        # Gera resposta usando a IA
        response, should_create_ticket, context = await openai_agent.generate_response(
            message,
            history
        )
        
        # Atualiza histórico
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})
        conversation_history[phone] = history[-10:]  # Mantém últimas 10 mensagens
        
        # Cria ticket se necessário
        if should_create_ticket:
            # Busca usuário pelo telefone
            user = crud.get_user_by_phone(db, phone.replace("@c.us", ""))
            
            ticket = crud.create_ticket(
                db,
                title=f"Chamado via WhatsApp - {phone}",
                description=f"Cliente solicitou atendimento.\n\nÚltima mensagem: {message}",
                client_id=user.id if user else None,
                client_phone=phone.replace("@c.us", "")
            )
            
            response += f"\n\nChamado #{ticket.id} criado com sucesso!"
        
        # Para de digitar
        await whatsapp_client.stop_typing(phone)
        
        # Envia resposta
        await whatsapp_client.send_message(phone, response)
        
    except Exception as e:
        # Em caso de erro, envia mensagem padrão
        error_msg = (
            "Desculpe, ocorreu um erro ao processar sua mensagem. "
            "Por favor, tente novamente mais tarde ou entre em contato com seu assessor."
        )
        await whatsapp_client.send_message(phone, error_msg)


@router.post("/whatsapp")
async def whatsapp_webhook(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Endpoint que recebe mensagens do WAHA.
    Processa apenas mensagens de texto recebidas.
    """
    # Extrai informações do payload do WAHA
    event = payload.get("event", "")
    
    # Processa apenas eventos de mensagem recebida
    if event != "message":
        return {"status": "ignored", "reason": "not a message event"}
    
    message_payload = payload.get("payload", {})
    
    # Verifica se é uma mensagem recebida (não enviada por nós)
    if message_payload.get("fromMe", False):
        return {"status": "ignored", "reason": "message from self"}
    
    # Extrai dados da mensagem
    chat_id = message_payload.get("from", "")
    body = message_payload.get("body", "")
    
    # Ignora mensagens vazias ou de grupos
    if not body or "@g.us" in chat_id:
        return {"status": "ignored", "reason": "empty or group message"}
    
    # Marca como visto
    await whatsapp_client.send_seen(chat_id)
    
    # Processa a mensagem em background
    background_tasks.add_task(process_message, chat_id, body, db)
    
    return {"status": "processing"}


@router.get("/health")
async def health_check():
    """Endpoint de verificação de saúde do webhook."""
    return {
        "status": "ok",
        "ai_available": openai_agent.is_available()
    }
