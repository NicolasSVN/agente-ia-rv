"""
API para testar o agente de IA sem usar WhatsApp.
Simula todas as funcionalidades do webhook mas não registra métricas.
Histórico isolado por usuário.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime

from database.database import get_db
from database.models import User
from api.endpoints.auth import get_current_user
from services.openai_agent import openai_agent
from services.vector_store import get_vector_store

router = APIRouter(prefix="/api/agent", tags=["Agent Test"])

test_conversations: Dict[int, List[dict]] = {}


class TestMessageRequest(BaseModel):
    message: str


class TestMessageResponse(BaseModel):
    response: str
    should_create_ticket: bool
    intent: Optional[str]
    knowledge_documents: List[dict]
    conversation_length: int


class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: str
    knowledge_used: Optional[List[dict]] = None
    intent: Optional[str] = None


@router.post("/test", response_model=TestMessageResponse)
async def test_agent_message(
    request: TestMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Testa uma mensagem com o agente de IA.
    Simula o fluxo completo do webhook mas não registra em whatsapp_messages.
    Histórico é isolado por usuário.
    """
    if current_user.role not in ["admin", "gestao_rv"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    user_id = current_user.id
    message = request.message.strip()
    
    if not message:
        raise HTTPException(status_code=400, detail="Mensagem não pode estar vazia")
    
    if user_id not in test_conversations:
        test_conversations[user_id] = []
    
    history = test_conversations[user_id]
    
    knowledge_context = ""
    knowledge_documents = []
    
    try:
        vector_store = get_vector_store()
        if vector_store:
            search_results = vector_store.search(message, n_results=3)
            
            if search_results:
                knowledge_documents = search_results
                knowledge_context = "\n\n--- Informações da Base de Conhecimento ---\n"
                for i, result in enumerate(search_results, 1):
                    title = result.get("metadata", {}).get("document_title", "Documento")
                    content = result.get("content", "")[:500]
                    knowledge_context += f"\n[{i}] {title}:\n{content}\n"
    except Exception as e:
        print(f"[AGENT_TEST] Erro ao buscar na base de conhecimento: {e}")
    
    history_for_ai = [{"role": msg["role"], "content": msg["content"]} for msg in history[-10:]]
    
    response, should_create_ticket, context = await openai_agent.generate_response(
        message,
        history_for_ai,
        extra_context=knowledge_context
    )
    
    history.append({
        "role": "user",
        "content": message,
        "timestamp": datetime.now().isoformat()
    })
    
    history.append({
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now().isoformat(),
        "knowledge_used": knowledge_documents,
        "intent": context.get("intent") if context else None
    })
    
    test_conversations[user_id] = history[-20:]
    
    return TestMessageResponse(
        response=response,
        should_create_ticket=should_create_ticket,
        intent=context.get("intent") if context else None,
        knowledge_documents=[
            {
                "title": doc.get("metadata", {}).get("document_title", "Documento"),
                "category": doc.get("metadata", {}).get("category", ""),
                "content_preview": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", "")
            }
            for doc in knowledge_documents
        ],
        conversation_length=len(history)
    )


@router.delete("/test/clear")
async def clear_test_conversation(
    current_user: User = Depends(get_current_user)
):
    """
    Limpa o histórico de conversa de teste do usuário atual.
    """
    if current_user.role not in ["admin", "gestao_rv"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    user_id = current_user.id
    
    if user_id in test_conversations:
        del test_conversations[user_id]
    
    return {"success": True, "message": "Conversa de teste limpa com sucesso"}


@router.get("/test/history")
async def get_test_history(
    current_user: User = Depends(get_current_user)
):
    """
    Retorna o histórico de conversa de teste do usuário atual.
    """
    if current_user.role not in ["admin", "gestao_rv"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    user_id = current_user.id
    history = test_conversations.get(user_id, [])
    
    return {
        "messages": history,
        "total": len(history)
    }
