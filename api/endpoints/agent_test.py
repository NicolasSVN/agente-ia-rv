"""
API para testar o agente de IA sem usar WhatsApp.
Usa Pipeline V2 (agentic RAG) — mesmo pipeline do WhatsApp.
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

router = APIRouter(prefix="/api/agent", tags=["Agent Test"])

test_conversations: Dict[int, List[dict]] = {}
test_session_data: Dict[int, Dict[str, Any]] = {}


class TestMessageRequest(BaseModel):
    message: str


class TestMessageResponse(BaseModel):
    response: str
    should_create_ticket: bool
    intent: Optional[str]
    query_type: Optional[str] = None
    entities_detected: Optional[List[str]] = None
    knowledge_documents: List[dict]
    conversation_length: int
    identified_assessor: Optional[Dict[str, Any]] = None
    rewritten_query: Optional[str] = None
    topic_switch: Optional[bool] = None
    is_comparative: Optional[bool] = None
    clarification_needed: Optional[bool] = None
    retrieval_strategy: Optional[str] = None
    is_implicit_continuation: Optional[bool] = None
    emotional_tone: Optional[str] = None
    tool_calls: Optional[List[dict]] = None
    pipeline: Optional[str] = None
    iterations: Optional[int] = None
    elapsed_ms: Optional[int] = None


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
    Usa EnhancedSearch (mesmo pipeline do WhatsApp) para garantir comportamento idêntico.
    Histórico é isolado por usuário.
    """
    if current_user.role not in ["admin", "gestao_rv"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    user_id = current_user.id
    from services.conversation_flow import normalize_message
    message = normalize_message(request.message)

    if not message:
        raise HTTPException(status_code=400, detail="Mensagem não pode estar vazia")

    if user_id not in test_conversations:
        test_conversations[user_id] = []

    if user_id not in test_session_data:
        test_session_data[user_id] = {"identified_assessor": None}

    history = test_conversations[user_id]
    session = test_session_data[user_id]

    try:
        SESSION_GAP_MINUTES = 120
        last_ts = session.get("last_response_at")
        if last_ts:
            from datetime import timedelta
            gap = datetime.now() - last_ts
            if gap > timedelta(minutes=SESSION_GAP_MINUTES) and len(history) >= 4:
                from services.conversation_memory import generate_session_summary
                history_for_summary = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in history[-10:]
                ]
                old_summary = await generate_session_summary(history_for_summary, openai_agent.client)
                if old_summary:
                    session["last_session_summary"] = old_summary
                    test_conversations[user_id] = []
                    history = test_conversations[user_id]
                    print(f"[AGENT_TEST] Gap de sessão detectado ({gap}), resumo gerado")
    except Exception as e:
        print(f"[AGENT_TEST] Erro na detecção de sessão (não-bloqueante): {e}")

    history_for_ai = []
    for msg in history[-20:]:
        entry = {
            "role": msg["role"],
            "content": msg["content"],
            "metadata": msg.get("metadata", {})
        }
        if msg.get("timestamp"):
            entry["timestamp"] = msg["timestamp"]
        history_for_ai.append(entry)

    if session.get("last_session_summary"):
        history_for_ai = [{"role": "system", "content": f"[Contexto da sessão anterior]: {session['last_session_summary']}"}] + history_for_ai

    try:
        response, should_create_ticket, context = await openai_agent.generate_response_v2(
            user_message=message,
            conversation_history=history_for_ai,
            sender_phone=None,
            identified_assessor=session.get("identified_assessor"),
            db=db,
            conversation_id=f"test_{user_id}",
            allow_tools=True,
        )

        if context and context.get("identified_assessor"):
            session["identified_assessor"] = context["identified_assessor"]
            test_session_data[user_id] = session

    except Exception as e:
        print(f"[AGENT_TEST] Erro ao gerar resposta V2: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar resposta: {str(e)}")

    session["last_response_at"] = datetime.now()
    test_session_data[user_id] = session

    try:
        import json as _json
        from database.models import RetrievalLog
        is_human_transfer = should_create_ticket or (context and context.get("human_transfer"))
        transfer_reason = context.get("transfer_reason") if context else None

        tool_calls_for_log = context.get("tool_calls", []) if context else []
        search_tools = [tc for tc in (tool_calls_for_log or []) if tc.get("name") == "search_knowledge_base"]

        retrieval_log = RetrievalLog(
            query=message,
            query_type="v2_agentic",
            result_count=len(search_tools),
            threshold_applied="v2_auto",
            human_transfer=is_human_transfer,
            transfer_reason=transfer_reason,
            user_id=user_id,
            conversation_id=f"test_{user_id}",
            response_time_ms=context.get("elapsed_ms") if context else None
        )
        db.add(retrieval_log)
        db.commit()
    except Exception as log_err:
        print(f"[AGENT_TEST] Erro ao salvar RetrievalLog (não-bloqueante): {log_err}")

    knowledge_documents = []
    if context and context.get("tool_calls"):
        for tc in context["tool_calls"]:
            if tc.get("name") == "search_knowledge_base":
                knowledge_documents.append({
                    "title": f"Tool: {tc['name']}",
                    "category": "",
                    "content_preview": tc.get("result_preview", "")[:200],
                    "composite_score": None,
                    "block_type": "tool_result",
                    "product": "",
                })

    history.append({
        "role": "user",
        "content": message,
        "timestamp": datetime.now().isoformat()
    })

    history.append({
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now().isoformat(),
        "metadata": context if context else {}
    })

    test_conversations[user_id] = history[-20:]

    identified = session.get("identified_assessor")
    intent_from_context = context.get("intent") if context else None

    return TestMessageResponse(
        response=response,
        should_create_ticket=should_create_ticket,
        intent=intent_from_context,
        knowledge_documents=knowledge_documents,
        conversation_length=len(history),
        identified_assessor={
            "nome": identified.get("nome"),
            "broker": identified.get("broker"),
            "equipe": identified.get("equipe"),
            "unidade": identified.get("unidade")
        } if identified else None,
        tool_calls=context.get("tool_calls") if context and context.get("tool_calls") else None,
        pipeline=context.get("pipeline") if context else None,
        iterations=context.get("iterations") if context else None,
        elapsed_ms=context.get("elapsed_ms") if context else None,
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

    if user_id in test_session_data:
        del test_session_data[user_id]

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
