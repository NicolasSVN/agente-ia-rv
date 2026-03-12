"""
Gerenciamento de memória conversacional persistente com debounce.

Camada 1 — Sessão ativa: mensagens recentes carregadas do banco (com cache em memória).
Camada 2 — Resumo de sessão anterior: resumo GPT da sessão anterior (armazenado em conversations).
Camada 3 — Histórico completo: permanece no banco, acessível via "Carregar mais".

Debounce: acumula mensagens rápidas (6s) antes de processar.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from sqlalchemy.orm import Session
from sqlalchemy import desc


SESSION_GAP_HOURS = 2
HISTORY_WINDOW = 10
DEBOUNCE_SECONDS = 6


_history_cache: Dict[str, list] = {}

_debounce_messages: Dict[str, list] = {}
_debounce_timers: Dict[str, asyncio.Task] = {}
_debounce_locks: Dict[str, asyncio.Lock] = {}
_debounce_contexts: Dict[str, dict] = {}
_processing_locks: Dict[str, asyncio.Lock] = {}


def _get_lock(phone: str, lock_dict: dict) -> asyncio.Lock:
    if phone not in lock_dict:
        lock_dict[phone] = asyncio.Lock()
    return lock_dict[phone]


def load_history_from_db(phone: str, db: Session, limit: int = HISTORY_WINDOW, after_timestamp=None) -> list:
    from database.models import WhatsAppMessage, MessageDirection
    
    query = db.query(WhatsAppMessage).filter(
        WhatsAppMessage.phone == phone,
        WhatsAppMessage.message_type == "text",
        WhatsAppMessage.body.isnot(None),
        WhatsAppMessage.body != "",
    )
    
    if after_timestamp:
        query = query.filter(WhatsAppMessage.created_at > after_timestamp)
    
    messages = (
        query
        .order_by(desc(WhatsAppMessage.created_at))
        .limit(limit * 2)
        .all()
    )
    
    messages.reverse()
    
    history = []
    for msg in messages:
        if msg.direction == MessageDirection.INBOUND.value or not msg.from_me:
            content = msg.body
            if content:
                history.append({"role": "user", "content": content})
        elif msg.direction == MessageDirection.OUTBOUND.value or msg.from_me:
            content = msg.ai_response or msg.body
            if content:
                entry = {"role": "assistant", "content": content}
                if msg.ai_intent:
                    entry["metadata"] = {"intent": msg.ai_intent}
                history.append(entry)
    
    return history[-limit:]


def get_history(phone: str, db: Session) -> list:
    if phone in _history_cache and _history_cache[phone]:
        return _history_cache[phone]
    
    history = load_history_from_db(phone, db)
    _history_cache[phone] = history
    print(f"[MEMORY] Histórico carregado do banco para {phone}: {len(history)} mensagens")
    return history


def update_history(phone: str, history: list):
    _history_cache[phone] = history[-HISTORY_WINDOW:]


def append_to_history(phone: str, role: str, content: str, metadata: dict = None):
    if phone not in _history_cache:
        _history_cache[phone] = []
    entry = {"role": role, "content": content}
    if metadata:
        entry["metadata"] = metadata
    _history_cache[phone].append(entry)
    _history_cache[phone] = _history_cache[phone][-HISTORY_WINDOW:]


def detect_session_gap(phone: str, db: Session) -> bool:
    from database.models import WhatsAppMessage, MessageDirection
    
    last_msg = (
        db.query(WhatsAppMessage.created_at)
        .filter(
            WhatsAppMessage.phone == phone,
            WhatsAppMessage.direction == MessageDirection.OUTBOUND.value,
        )
        .order_by(desc(WhatsAppMessage.created_at))
        .first()
    )
    
    if not last_msg or not last_msg.created_at:
        return False
    
    last_time = last_msg.created_at
    if last_time.tzinfo is None:
        last_time = last_time.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    gap = now - last_time
    
    return gap > timedelta(hours=SESSION_GAP_HOURS)


async def generate_session_summary(history: list, client) -> str:
    if not history or not client:
        return ""
    
    recent_msgs = history[-HISTORY_WINDOW:]
    if len(recent_msgs) < 2:
        return ""
    
    conversation_text = ""
    for msg in recent_msgs:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if content:
            label = "Assessor" if role == "user" else "Stevan"
            conversation_text += f"{label}: {content[:200]}\n"
    
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Resuma a conversa abaixo em 2-3 frases concisas. "
                            "Foque nos ativos/produtos discutidos, decisões tomadas, "
                            "e qualquer pedido pendente. Formato: texto corrido, sem bullets."
                        )
                    },
                    {"role": "user", "content": conversation_text}
                ],
                max_tokens=150,
                temperature=0.3
            )
        )
        summary = response.choices[0].message.content.strip()
        print(f"[MEMORY] Resumo de sessão gerado: {summary[:100]}...")
        return summary
    except Exception as e:
        print(f"[MEMORY] Erro ao gerar resumo de sessão: {e}")
        return ""


async def handle_session_transition(phone: str, db: Session, conversation):
    if not detect_session_gap(phone, db):
        return
    
    print(f"[MEMORY] Gap de sessão detectado para {phone}")
    
    old_history = _history_cache.get(phone, [])
    if not old_history:
        old_history = load_history_from_db(phone, db)
    
    if old_history and len(old_history) >= 2:
        try:
            from services.openai_agent import openai_agent
            if openai_agent.client:
                summary = await generate_session_summary(old_history, openai_agent.client)
                if summary and conversation:
                    conversation.last_session_summary = summary
                    conversation.last_session_ended_at = datetime.now(timezone.utc)
                    db.commit()
                    print(f"[MEMORY] Resumo salvo na conversa {conversation.id}")
        except Exception as e:
            print(f"[MEMORY] Erro ao salvar resumo de sessão: {e}")
    
    _history_cache[phone] = []
    
    if conversation and hasattr(conversation, 'last_session_ended_at') and conversation.last_session_ended_at:
        fresh_history = load_history_from_db(phone, db, after_timestamp=conversation.last_session_ended_at)
        if fresh_history:
            _history_cache[phone] = fresh_history
            print(f"[MEMORY] Histórico pós-gap carregado: {len(fresh_history)} msgs da sessão atual")


def build_context_with_summary(history: list, conversation, rewrite_result=None) -> list:
    if not conversation or not hasattr(conversation, 'last_session_summary'):
        return history
    
    summary = conversation.last_session_summary
    if not summary:
        return history
    
    if rewrite_result and rewrite_result.topic_switch:
        print(f"[MEMORY] Topic switch detectado — ignorando resumo de sessão anterior")
        return history
    
    summary_msg = {
        "role": "system",
        "content": f"[Contexto da sessão anterior]: {summary}"
    }
    
    return [summary_msg] + history


async def debounce_text_message(
    phone: str, 
    body: str, 
    db_factory, 
    message_record_id: int,
    conversation_id: int,
    process_fn
):
    lock = _get_lock(phone, _debounce_locks)
    
    async with lock:
        if phone not in _debounce_messages:
            _debounce_messages[phone] = []
        _debounce_messages[phone].append({
            "body": body,
            "message_record_id": message_record_id,
            "conversation_id": conversation_id,
            "timestamp": datetime.now(timezone.utc)
        })
        
        if phone in _debounce_timers and not _debounce_timers[phone].done():
            _debounce_timers[phone].cancel()
            print(f"[DEBOUNCE] Timer resetado para {phone} — acumulando mensagens")
        
        _debounce_timers[phone] = asyncio.create_task(
            _debounce_fire(phone, db_factory, process_fn)
        )
        print(f"[DEBOUNCE] Timer de {DEBOUNCE_SECONDS}s iniciado para {phone} ({len(_debounce_messages.get(phone, []))} msg acumuladas)")


async def _debounce_fire(phone: str, db_factory, process_fn):
    try:
        await asyncio.sleep(DEBOUNCE_SECONDS)
    except asyncio.CancelledError:
        return
    
    lock = _get_lock(phone, _debounce_locks)
    async with lock:
        messages = _debounce_messages.pop(phone, [])
        _debounce_timers.pop(phone, None)
    
    if not messages:
        return
    
    proc_lock = _get_lock(phone, _processing_locks)
    async with proc_lock:
        try:
            db = db_factory()
        except Exception as e:
            print(f"[DEBOUNCE] Erro ao criar sessão de banco para {phone}: {e}")
            return
        try:
            from database.models import WhatsAppMessage, Conversation
            
            first_msg = messages[0]
            conversation = db.query(Conversation).filter(
                Conversation.id == first_msg["conversation_id"]
            ).first()
            
            message_record = db.query(WhatsAppMessage).filter(
                WhatsAppMessage.id == first_msg["message_record_id"]
            ).first() if first_msg["message_record_id"] else None
            
            if len(messages) == 1:
                combined_body = first_msg["body"]
                print(f"[DEBOUNCE] Processando 1 mensagem de {phone}")
            else:
                bodies = [m["body"] for m in messages if m["body"]]
                combined_body = "\n".join(bodies)
                print(f"[DEBOUNCE] Processando {len(messages)} mensagens acumuladas de {phone}: {combined_body[:80]}...")
                
                for extra_msg in messages[1:]:
                    if extra_msg["message_record_id"]:
                        extra_record = db.query(WhatsAppMessage).filter(
                            WhatsAppMessage.id == extra_msg["message_record_id"]
                        ).first()
                        if extra_record:
                            extra_record.ai_intent = "debounced_merged"
                            db.commit()
            
            await process_fn(phone, combined_body, db, message_record, conversation)
            
        except Exception as e:
            print(f"[DEBOUNCE] Erro ao processar mensagens acumuladas de {phone}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
