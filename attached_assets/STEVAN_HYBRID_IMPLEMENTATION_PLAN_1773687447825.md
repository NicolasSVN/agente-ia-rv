# STEVAN 3.0 — PLANO DE IMPLEMENTAÇÃO HÍBRIDO
## Melhorias de Fluidez Conversacional com Referências Diretas ao Código

**Versão:** 3.0 (Plano Híbrido Otimizado)  
**Data:** Março 2026  
**Repositório:** https://github.com/NicolasSVN/agente-ia-rv  
**Objetivo:** Implementar melhorias de naturalidade conversacional integrando o melhor de dois planos de evolução, com referências diretas aos arquivos do código atual.

---

## 📋 ÍNDICE

1. [Introdução ao Plano Híbrido](#1-introdução-ao-plano-híbrido)
2. [Estrutura Atual do Projeto](#2-estrutura-atual-do-projeto)
3. [Arquitetura Híbrida Proposta](#3-arquitetura-híbrida-proposta)
4. [Implementações por Arquivo](#4-implementações-por-arquivo)
5. [Novos Componentes](#5-novos-componentes)
6. [Migrações de Banco de Dados](#6-migrações-de-banco-de-dados)
7. [Plano de Implementação Faseado](#7-plano-de-implementação-faseado)
8. [Testes e Validação](#8-testes-e-validação)
9. [Checklist para Replit](#9-checklist-para-replit)

---

## 1. INTRODUÇÃO AO PLANO HÍBRIDO

### 1.1 O que é este Plano

Este documento integra **o melhor de dois planos de evolução** do agente Stevan:

**Plano A (STEVAN_IMPROVEMENTS_SPEC.md):**
- ✅ Modelo único orquestrador (GPT-4o)
- ✅ Function calling nativo
- ✅ ConversationState com contexto implícito
- ✅ Conversational boost no RAG

**Plano B (Stevan 2.0):**
- ✅ Retrieval Planner (decide onde buscar)
- ✅ Self-Correction Layer (valida respostas)
- ✅ Resumo incremental para conversas longas
- ✅ Uso estratégico de GPT-4o-mini

**Resultado:** Arquitetura híbrida que maximiza naturalidade + eficiência + custo

---

### 1.2 Filosofia do Plano Híbrido

```
CORE: GPT-4o orquestra a conversa (menos perda de contexto)
  ↓
+ Retrieval Planner (decide ONDE buscar - interno vs web)
  ↓
+ Self-Correction (valida resposta antes de enviar)
  ↓
+ Resumo Incremental (conversas longas)
  ↓
= MELHOR NATURALIDADE + MENOR CUSTO + MAIOR PRECISÃO
```

---

## 2. ESTRUTURA ATUAL DO PROJETO

### 2.1 Estrutura de Diretórios

```
agente-ia-rv/
├── api/
│   └── endpoints/
│       └── whatsapp_webhook.py          # Entry point do webhook
├── services/
│   ├── openai_agent.py                  # Geração de respostas (GPT-4o)
│   ├── query_rewriter.py                # Query rewriting (SERÁ MODIFICADO)
│   ├── conversation_flow.py             # Gestão de fluxo
│   ├── conversation_memory.py           # Memória conversacional
│   ├── retrieval.py                     # RAG + busca vetorial
│   ├── media_processor.py               # Áudio/imagem/documento
│   └── cost_tracker.py                  # Tracking de custos
├── database/
│   └── models/
│       ├── conversation.py              # Modelo Conversation
│       ├── whatsapp_message.py          # Modelo WhatsAppMessage
│       └── assessor.py                  # Modelo Assessor
├── core/
│   └── config.py                        # Configurações
└── main.py                              # FastAPI app
```

---

### 2.2 ⚠️ INSTRUÇÕES PARA O REPLIT

**ANTES DE COMEÇAR A IMPLEMENTAÇÃO:**

1. **Explore o código atual:**
   ```bash
   # Liste todos os arquivos em services/
   ls -la services/
   
   # Visualize a estrutura completa
   tree -L 3
   ```

2. **Leia os arquivos principais:**
   - `services/openai_agent.py` - entender como funciona geração atual
   - `services/query_rewriter.py` - entender reescrita atual
   - `api/endpoints/whatsapp_webhook.py` - entender pipeline atual
   - `database/models/conversation.py` - entender modelo atual

3. **Identifique dependências:**
   ```bash
   # Veja todas as importações
   grep -r "from services" api/ services/
   ```

4. **⚠️ PERGUNTE AO USUÁRIO antes de prosseguir:**

```
📋 CHECKLIST DE VERIFICAÇÃO INICIAL

Antes de implementar, confirme com o usuário:

[ ] Você confirmou que a estrutura de diretórios está correta?
[ ] Você leu e entendeu o código atual de:
    - services/openai_agent.py
    - services/query_rewriter.py
    - api/endpoints/whatsapp_webhook.py
    
[ ] Qual versão do OpenAI SDK está sendo usada? (openai>=1.0.0)
[ ] O banco de dados usa PostgreSQL + pgvector?
[ ] O sistema atual usa marcadores [SEND_PDF] ou já usa function calling?

🔴 AGUARDAR RESPOSTA DO USUÁRIO ANTES DE CONTINUAR
```

---

## 3. ARQUITETURA HÍBRIDA PROPOSTA

### 3.1 Pipeline Atual vs Novo Pipeline

**PIPELINE ATUAL (conforme DESCRITIVO_EXECUTIVO_AGENTE.md):**

```
Webhook WhatsApp
↓
Media Processor (se aplicável)
↓
Query Rewriter (gpt-4o-mini) - reescreve + classifica
↓
Busca RAG (pgvector)
↓
GPT-4o Response Generator
↓
Post-processing (extrai marcadores)
↓
Envio WhatsApp
```

**PIPELINE HÍBRIDO NOVO:**

```
Webhook WhatsApp
↓
Media Processor (se aplicável)
↓
┌─────────────────────────────────────────────────┐
│ CONVERSATIONAL ANALYZER (GPT-4o)                │
│ - Analisa mensagem em contexto                  │
│ - Detecta continuação implícita                 │
│ - Identifica mudança de tópico                  │
│ - Atualiza ConversationState                    │
└─────────────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────┐
│ RETRIEVAL PLANNER (gpt-4o-mini) ✨ NOVO         │
│ - Decide: INTERNAL_ONLY | WEB_ONLY |            │
│   INTERNAL_PLUS_WEB | NO_RETRIEVAL              │
└─────────────────────────────────────────────────┘
↓
Busca RAG (com conversational boost) ou Web Search
↓
┌─────────────────────────────────────────────────┐
│ RESPONSE GENERATOR (GPT-4o)                     │
│ - Usa function calling (não marcadores)         │
│ - Contexto enriquecido com state                │
└─────────────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────┐
│ SELF-CORRECTION (gpt-4o-mini) ✨ NOVO           │
│ - Valida se resposta responde a pergunta        │
│ - Regenera se inválido                          │
└─────────────────────────────────────────────────┘
↓
Function Execution (send_document, etc)
↓
Envio WhatsApp
↓
Analytics + Resumo Incremental (se >15 msgs)
```

---

### 3.2 Componentes Chave

| Componente | Modelo | Responsabilidade | Status |
|------------|--------|------------------|--------|
| **Conversational Analyzer** | GPT-4o | Analisa contexto + intenção | ✅ NOVO |
| **Retrieval Planner** | gpt-4o-mini | Decide estratégia de busca | ✨ NOVO |
| **ConversationStateManager** | - | Mantém estado semântico | ✅ NOVO |
| **Response Generator** | GPT-4o | Gera resposta com functions | 🔄 MODIFICAR |
| **Self-Correction** | gpt-4o-mini | Valida resposta | ✨ NOVO |
| **Incremental Summarizer** | gpt-4o-mini | Resume a cada 15 msgs | ✨ NOVO |

---

## 4. IMPLEMENTAÇÕES POR ARQUIVO

### 4.1 📁 `database/models/conversation.py`

**ARQUIVO ATUAL:** Define modelo `Conversation`

**MODIFICAÇÕES NECESSÁRIAS:**

```python
# ⚠️ REPLIT: Adicione estes campos ao modelo Conversation existente

# LOCALIZAR a classe Conversation
# ADICIONAR os seguintes campos:

class Conversation(Base):
    __tablename__ = "conversations"
    
    # ... campos existentes ...
    
    # ✨ NOVOS CAMPOS PARA CONVERSATION STATE
    current_topic = Column(String(200), nullable=True)
    topic_started_at = Column(DateTime, nullable=True)
    implicit_context = Column(JSONB, default={}, nullable=False)
    conversation_mode = Column(String(50), default="question_answering")
    pending_clarification = Column(String(255), nullable=True)
    
    # ✨ NOVO CAMPO PARA RESUMO INCREMENTAL
    incremental_summary = Column(Text, nullable=True)
    last_summary_at = Column(DateTime, nullable=True)
    message_count_since_summary = Column(Integer, default=0)
```

**🔴 IMPORTANTE - PERGUNTE AO USUÁRIO:**

```
ANTES de modificar database/models/conversation.py:

1. O modelo Conversation usa SQLAlchemy declarative base?
2. Há migrations configuradas (Alembic)?
3. Posso criar uma migration ou devo alterar direto?
4. O campo JSONB está disponível? (PostgreSQL >= 9.4)

AGUARDAR RESPOSTA ANTES DE PROSSEGUIR
```

---

### 4.2 📁 `services/conversation_state_manager.py`

**ARQUIVO:** ✨ NOVO (criar do zero)

**LOCALIZAÇÃO:** `services/conversation_state_manager.py`

```python
"""
Gerenciador de estado conversacional semântico.

Este módulo mantém a "memória de trabalho" da conversa:
- Qual tópico está sendo discutido
- Quais entidades foram mencionadas
- Qual o modo de conversa
- Contexto implícito
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from database.models.conversation import Conversation
import json


class ConversationState:
    """
    Representação do estado conversacional ativo.
    
    ⚠️ NÃO confundir com ConversationState do sistema antigo (técnico).
    Este é um estado SEMÂNTICO da conversa.
    """
    
    def __init__(
        self,
        current_topic: Optional[str] = None,
        topic_started_at: Optional[datetime] = None,
        implicit_context: Optional[Dict[str, Any]] = None,
        conversation_mode: str = "question_answering",
        pending_clarification: Optional[str] = None,
        recent_entities: Optional[List[Dict]] = None,
        documents_in_context: Optional[List[str]] = None
    ):
        self.current_topic = current_topic
        self.topic_started_at = topic_started_at
        self.implicit_context = implicit_context or {}
        self.conversation_mode = conversation_mode
        self.pending_clarification = pending_clarification
        self.recent_entities = recent_entities or []
        self.documents_in_context = documents_in_context or []
    
    def to_dict(self) -> Dict:
        """Serializa para salvar no banco"""
        return {
            "current_topic": self.current_topic,
            "topic_started_at": self.topic_started_at.isoformat() if self.topic_started_at else None,
            "implicit_context": self.implicit_context,
            "conversation_mode": self.conversation_mode,
            "pending_clarification": self.pending_clarification,
            "recent_entities": self.recent_entities,
            "documents_in_context": self.documents_in_context
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ConversationState":
        """Deserializa do banco"""
        topic_started_at = None
        if data.get("topic_started_at"):
            topic_started_at = datetime.fromisoformat(data["topic_started_at"])
        
        return cls(
            current_topic=data.get("current_topic"),
            topic_started_at=topic_started_at,
            implicit_context=data.get("implicit_context", {}),
            conversation_mode=data.get("conversation_mode", "question_answering"),
            pending_clarification=data.get("pending_clarification"),
            recent_entities=data.get("recent_entities", []),
            documents_in_context=data.get("documents_in_context", [])
        )


class ConversationStateManager:
    """
    Gerencia o estado conversacional através dos turnos.
    
    Responsabilidades:
    - Carregar estado do banco
    - Atualizar estado com base em análise
    - Decidir quando pedir confirmação de mudança de tópico
    - Limpar entidades antigas
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_or_create_state(self, conversation_id: str) -> ConversationState:
        """
        Recupera estado ativo da conversa ou cria novo.
        
        ⚠️ NÃO crie estado novo se conversa tiver >2h de inatividade
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            # Conversa não existe, criar estado vazio
            return ConversationState()
        
        # Verificar inatividade
        if conversation.updated_at:
            inactive_time = datetime.now() - conversation.updated_at
            if inactive_time > timedelta(hours=2):
                # Conversa inativa há mais de 2h, resetar estado
                return ConversationState()
        
        # Carregar estado existente
        if conversation.current_topic or conversation.implicit_context:
            return ConversationState(
                current_topic=conversation.current_topic,
                topic_started_at=conversation.topic_started_at,
                implicit_context=conversation.implicit_context or {},
                conversation_mode=conversation.conversation_mode,
                pending_clarification=conversation.pending_clarification
            )
        
        return ConversationState()
    
    def update_with_analysis(
        self,
        state: ConversationState,
        analysis: Dict,
        message: str
    ) -> ConversationState:
        """
        Atualiza estado com base na análise da mensagem.
        
        Args:
            state: Estado atual
            analysis: Resultado do ConversationalAnalyzer
            message: Mensagem original do assessor
        
        Returns:
            Estado atualizado
        
        ⚠️ NÃO sobrescreva current_topic sem confirmação do assessor
        ⚠️ NÃO limpe implicit_context completamente
        """
        
        # Atualizar contexto implícito incrementalmente
        if analysis.get("implicit_assumptions"):
            state.implicit_context.update(analysis["implicit_assumptions"])
        
        # Adicionar entidades mencionadas
        if analysis.get("entities_mentioned"):
            for entity in analysis["entities_mentioned"]:
                state.recent_entities.append({
                    "type": entity["type"],
                    "value": entity["value"],
                    "mentioned_at": datetime.now().isoformat()
                })
        
        # Limpar entidades antigas (>30 min)
        cutoff_time = datetime.now() - timedelta(minutes=30)
        state.recent_entities = [
            e for e in state.recent_entities
            if datetime.fromisoformat(e["mentioned_at"]) > cutoff_time
        ]
        
        # Detectar mudança de tópico
        if analysis.get("topic_change_detected"):
            new_topic = analysis.get("new_topic")
            
            # ⚠️ NÃO mude current_topic imediatamente
            # Marcar para confirmação (será tratado no pipeline principal)
            if state.current_topic and new_topic != state.current_topic:
                state.pending_clarification = f"topic_change_to_{new_topic}"
        
        # Atualizar modo de conversa
        if analysis.get("conversation_flow"):
            flow = analysis["conversation_flow"]
            if flow == "wrapping_up":
                state.conversation_mode = "wrapping_up"
            elif flow == "new_topic":
                state.conversation_mode = "exploring"
            else:
                state.conversation_mode = "question_answering"
        
        return state
    
    def should_confirm_topic_change(
        self,
        state: ConversationState,
        new_topic: str,
        message: str
    ) -> bool:
        """
        Decide se deve pedir confirmação antes de mudar tópico.
        
        Confirmar quando:
        - Tópico atual está ativo há <5 minutos
        - Novo tópico não relacionado
        - Assessor NÃO usou palavras de transição
        
        NÃO confirmar quando:
        - Tópico inativo há >10 minutos
        - Mensagem tem marcadores explícitos ("agora", "mudando")
        - Assessor finalizou ("obrigado!", "beleza!")
        """
        
        # Se não há tópico ativo, não precisa confirmar
        if not state.current_topic:
            return False
        
        # Se tópico é o mesmo, não precisa confirmar
        if state.current_topic == new_topic:
            return False
        
        # Verificar tempo desde início do tópico
        if state.topic_started_at:
            topic_age = datetime.now() - state.topic_started_at
            
            # Tópico muito antigo (>10 min), não confirmar
            if topic_age > timedelta(minutes=10):
                return False
            
            # Tópico recente (<5 min), verificar palavras de transição
            if topic_age < timedelta(minutes=5):
                # Palavras de transição explícitas
                transition_words = [
                    "agora", "mudando", "outra coisa", "aliás",
                    "valeu", "obrigado", "beleza", "é isso"
                ]
                message_lower = message.lower()
                
                has_transition = any(
                    word in message_lower for word in transition_words
                )
                
                # Se tem transição explícita, não precisa confirmar
                if has_transition:
                    return False
                
                # Tópico recente + sem transição = CONFIRMAR
                return True
        
        # Default: não confirmar
        return False
    
    def save_state(
        self,
        conversation_id: str,
        state: ConversationState
    ):
        """
        Persiste estado no banco de dados.
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation:
            conversation.current_topic = state.current_topic
            conversation.topic_started_at = state.topic_started_at
            conversation.implicit_context = state.implicit_context
            conversation.conversation_mode = state.conversation_mode
            conversation.pending_clarification = state.pending_clarification
            
            self.db.commit()
```

**🔴 PERGUNTE AO USUÁRIO:**

```
Após criar services/conversation_state_manager.py:

1. Este módulo está usando as importações corretas?
   - from database.models.conversation import Conversation
   
2. A sessão do banco está sendo passada corretamente?

3. Executar testes unitários antes de integrar?

AGUARDAR CONFIRMAÇÃO
```

---

### 4.3 📁 `services/conversational_analyzer.py`

**ARQUIVO:** ✨ NOVO (criar do zero)

**LOCALIZAÇÃO:** `services/conversational_analyzer.py`

```python
"""
Analisador conversacional usando GPT-4o.

Este módulo SUBSTITUI o Query Rewriter + Classificador atuais.
Usa GPT-4o (não mini) para manter máxima capacidade contextual.
"""

from typing import Dict, List, Optional
from openai import AsyncOpenAI
from datetime import datetime
import json
from services.conversation_state_manager import ConversationState


class ConversationalAnalyzer:
    """
    Analisa mensagens no contexto conversacional completo.
    
    ⚠️ IMPORTANTE:
    - Usa GPT-4o (NÃO gpt-4o-mini) - precisa capacidade completa
    - Temperature = 0.3 (NÃO 0.1) - precisa flexibilidade interpretativa
    - Retorna análise multi-dimensional (não classificação binária)
    """
    
    def __init__(self, openai_client: AsyncOpenAI):
        self.client = openai_client
    
    async def analyze_message(
        self,
        message: str,
        conversation_history: List[Dict],
        current_state: ConversationState
    ) -> Dict:
        """
        Analisa mensagem e retorna estrutura multi-dimensional.
        
        Args:
            message: Mensagem do assessor
            conversation_history: Últimas N mensagens
            current_state: Estado conversacional atual
        
        Returns:
            Dict com análise completa (ver schema abaixo)
        
        ❌ DON'T: Usar gpt-4o-mini
        ❌ DON'T: Usar temperature < 0.3
        ✅ DO: Incluir histórico completo
        ✅ DO: Passar current_topic no contexto
        """
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            message=message,
            history=conversation_history,
            state=current_state
        )
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",  # ⚠️ NÃO usar gpt-4o-mini
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # ⚠️ NÃO usar < 0.3
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            return analysis
            
        except Exception as e:
            # Fallback em caso de erro
            return {
                "primary_intent": "question",
                "conversation_flow": "unclear",
                "is_implicit_continuation": False,
                "needs_clarification": False,
                "suggested_rag_query": message,
                "can_answer_directly": False,
                "error": str(e)
            }
    
    def _build_system_prompt(self) -> str:
        """
        System prompt do analisador conversacional.
        
        ✅ DO: Usar instruções positivas
        ❌ DON'T: Encher de "NUNCA"
        """
        return """Você é um analisador conversacional especializado em diálogos técnicos de mercado financeiro entre brokers/assessores.

Seu trabalho é entender a INTENÇÃO e CONTEXTO de mensagens, considerando:
- O que foi discutido anteriormente (tópico ativo, entidades mencionadas)
- O que o assessor NÃO disse mas está implícito pelo contexto
- Se ele mudou de assunto ou está continuando
- Se precisa de esclarecimento ou já dá pra responder

SOBRE CONTINUAÇÕES IMPLÍCITAS:

Exemplos de CONTINUAÇÃO (is_implicit_continuation: true):

Contexto: Assessor perguntou sobre BTLG11
Mensagem: "e o dividend yield?"
→ Está perguntando do DY do BTLG11 (continuação implícita)

Contexto: Assessor perguntou sobre estratégia call spread
Mensagem: "como monta?"
→ Quer saber como montar call spread (continuação implícita)

Contexto: Assessor perguntou sobre COE autocallable
Mensagem: "qual o risco?"
→ Quer saber risco daquele COE (continuação implícita)

Contexto: Assessor perguntou sobre PETR4
Mensagem: "manda o material"
→ Quer material de PETR4 (continuação implícita)

Exemplos de NOVO TÓPICO (is_implicit_continuation: false):

Contexto: Assessor perguntou sobre BTLG11
Mensagem: "e o PETR4?"
→ Novo ticker = novo tópico

Contexto: Assessor perguntou sobre FIIs
Mensagem: "agora quero saber sobre COEs"
→ Palavra de transição + produto diferente = novo tópico

Contexto: Assessor perguntou sobre venda coberta
Mensagem: "valeu! outra coisa, tem relatório de VALE3?"
→ Agradecimento + "outra coisa" = encerrou tópico anterior

SOBRE MUDANÇAS DE TÓPICO:

Detecte topic_change_detected: true quando:
- Mensagem menciona novo ativo/produto SEM referência ao anterior
- Usa palavras de transição: "agora", "mudando", "outra coisa", "aliás"
- Pergunta genérica após específica pode ser expansão ou novo tópico (analise!)

SOBRE TOM EMOCIONAL:

Categorize emotional_tone:
- "neutral": Tom normal
- "frustrated": "isso não funciona", "já perguntei isso"
- "urgent": "urgente", "rápido", "já"
- "satisfied": "obrigado", "valeu", "perfeito"
- "confused": "não entendi", "como assim"

SOBRE NECESSIDADE DE CLARIFICAÇÃO:

Marque needs_clarification: true quando:
- Ticker ambíguo: "BTLG" → BTLG11 ou BTLG12?
- Pergunta vaga sem contexto: "qual a performance?" → de quê?
- Informação essencial faltando

Marque needs_clarification: false quando:
- Contexto deixa óbvio
- Pergunta autocontida
- Assessor está continuando assunto anterior

SOBRE QUERY PARA RAG:

O campo suggested_rag_query deve ser otimizado:

Mensagem: "e o DY?"
Contexto: BTLG11
→ suggested_rag_query: "dividend yield BTLG11"

Mensagem: "como monta?"
Contexto: call spread
→ suggested_rag_query: "como montar estrutura call spread passo a passo"

Sempre retorne JSON válido com esta estrutura:
{
  "primary_intent": "question" | "document_request" | "clarification" | "confirmation" | "casual_chat" | "complaint",
  "secondary_intents": ["intent2", "intent3"],
  "conversation_flow": "continuing_topic" | "new_topic" | "wrapping_up" | "unclear",
  "topic_change_detected": true | false,
  "new_topic": "string ou null",
  "is_implicit_continuation": true | false,
  "needs_clarification": true | false,
  "clarification_reason": "string ou null",
  "emotional_tone": "neutral" | "frustrated" | "urgent" | "satisfied" | "confused",
  "entities_mentioned": [
    {"type": "ticker", "value": "BTLG11"},
    {"type": "strategy", "value": "call spread"}
  ],
  "implicit_assumptions": {
    "assessor_knowledge_level": "basic" | "intermediate" | "advanced",
    "response_urgency": "low" | "medium" | "high"
  },
  "suggested_rag_query": "string",
  "can_answer_directly": true | false
}"""
    
    def _build_user_prompt(
        self,
        message: str,
        history: List[Dict],
        state: ConversationState
    ) -> str:
        """Monta prompt do usuário com contexto"""
        
        context_parts = []
        
        # Tópico ativo
        if state.current_topic:
            context_parts.append(f"TÓPICO ATIVO: {state.current_topic}")
            if state.topic_started_at:
                age = datetime.now() - state.topic_started_at
                context_parts.append(f"Ativo há: {age.seconds // 60} minutos")
        
        # Contexto implícito
        if state.implicit_context:
            context_parts.append(f"CONTEXTO IMPLÍCITO: {state.implicit_context}")
        
        # Entidades recentes
        if state.recent_entities:
            entities_str = ", ".join([
                e["value"] for e in state.recent_entities[-5:]
            ])
            context_parts.append(f"ENTIDADES MENCIONADAS: {entities_str}")
        
        # Histórico
        history_formatted = self._format_history(history)
        
        return f"""CONTEXTO ATUAL:
{chr(10).join(context_parts) if context_parts else "Nenhum contexto ativo"}

HISTÓRICO RECENTE:
{history_formatted}

NOVA MENSAGEM DO ASSESSOR:
{message}

Analise esta mensagem e retorne JSON:"""
    
    def _format_history(self, history: List[Dict]) -> str:
        """Formata histórico para o prompt"""
        if not history:
            return "(Início de conversa)"
        
        formatted = []
        for msg in history[-10:]:  # Últimas 10
            sender = "Assessor" if msg.get("sender_type") == "user" else "Stevan"
            text = msg.get("text", "")
            formatted.append(f"{sender}: {text}")
        
        return "\n".join(formatted)
```

**🔴 PERGUNTE AO USUÁRIO:**

```
Após criar services/conversational_analyzer.py:

1. A importação do OpenAI client está correta?
   from openai import AsyncOpenAI
   
2. O formato esperado do conversation_history está correto?
   List[Dict] com campos: sender_type, text
   
3. Este módulo deve substituir completamente o query_rewriter.py
   ou rodar em paralelo durante transição?

AGUARDAR RESPOSTA
```

---

### 4.4 📁 `services/retrieval_planner.py`

**ARQUIVO:** ✨ NOVO (criar do zero)

**LOCALIZAÇÃO:** `services/retrieval_planner.py`

```python
"""
Retrieval Planner - Decide ONDE buscar informação.

Este módulo decide a estratégia de busca ANTES de executar RAG/Web:
- INTERNAL_ONLY: Busca apenas na base de conhecimento
- WEB_ONLY: Busca apenas na web
- INTERNAL_PLUS_WEB: Busca em ambos
- NO_RETRIEVAL: Não precisa buscar (saudação, confirmação, etc)

✨ Esta é uma das MELHORES ideias do Plano B (Stevan 2.0)
"""

from typing import Dict
from openai import AsyncOpenAI
import json


class RetrievalStrategy:
    """Estratégias de busca"""
    INTERNAL_ONLY = "INTERNAL_ONLY"
    WEB_ONLY = "WEB_ONLY"
    INTERNAL_PLUS_WEB = "INTERNAL_PLUS_WEB"
    NO_RETRIEVAL = "NO_RETRIEVAL"


class RetrievalPlanner:
    """
    Decide estratégia de busca antes de executar RAG.
    
    ✅ Usa gpt-4o-mini (task simples, não precisa GPT-4o)
    ✅ Temperature = 0 (decisão binária, precisa consistência)
    """
    
    def __init__(self, openai_client: AsyncOpenAI):
        self.client = openai_client
    
    async def plan_retrieval(
        self,
        message: str,
        analysis: Dict,
        current_topic: str = None
    ) -> str:
        """
        Decide estratégia de busca.
        
        Args:
            message: Mensagem original
            analysis: Resultado do ConversationalAnalyzer
            current_topic: Tópico ativo (se houver)
        
        Returns:
            Uma das estratégias: INTERNAL_ONLY, WEB_ONLY, 
            INTERNAL_PLUS_WEB, NO_RETRIEVAL
        
        Exemplos:
        - "Qual o preço do PETR4 agora?" → WEB_ONLY
        - "Qual a estratégia do comitê pro BTLG11?" → INTERNAL_ONLY
        - "Como está BTLG11 vs mercado?" → INTERNAL_PLUS_WEB
        - "Obrigado!" → NO_RETRIEVAL
        """
        
        system_prompt = """Você decide como o sistema deve buscar informação para responder ao usuário.

Opções:
- INTERNAL_ONLY: Base de conhecimento interna tem a resposta
- WEB_ONLY: Precisa de dados em tempo real da web
- INTERNAL_PLUS_WEB: Precisa de ambos
- NO_RETRIEVAL: Não precisa buscar (saudação, confirmação)

Use INTERNAL_ONLY quando:
- Pergunta sobre estratégia/recomendação do comitê
- Pergunta sobre materiais/documentos da casa
- Pergunta sobre produtos recomendados
- Pergunta sobre teses de investimento da SVN

Use WEB_ONLY quando:
- Pergunta sobre preço/cotação atual
- Pergunta sobre notícias recentes
- Pergunta sobre dados de mercado em tempo real
- Pergunta "agora", "hoje", "atual"

Use INTERNAL_PLUS_WEB quando:
- Comparação produto SVN vs mercado
- Performance de recomendado vs benchmark
- Análise de produto com contexto de mercado

Use NO_RETRIEVAL quando:
- Saudações ("oi", "bom dia")
- Confirmações ("ok", "obrigado")
- Conversação casual

Retorne APENAS a estratégia, sem explicação."""
        
        user_prompt = f"""Mensagem: {message}

Intenção primária: {analysis.get('primary_intent')}
Tópico atual: {current_topic or 'nenhum'}
Tom emocional: {analysis.get('emotional_tone')}

Estratégia:"""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Task simples, mini suficiente
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0,  # Decisão binária, precisa consistência
                max_tokens=50
            )
            
            strategy = response.choices[0].message.content.strip()
            
            # Validar resposta
            valid_strategies = [
                RetrievalStrategy.INTERNAL_ONLY,
                RetrievalStrategy.WEB_ONLY,
                RetrievalStrategy.INTERNAL_PLUS_WEB,
                RetrievalStrategy.NO_RETRIEVAL
            ]
            
            if strategy in valid_strategies:
                return strategy
            else:
                # Fallback: se análise indica que pode responder direto
                if analysis.get("can_answer_directly"):
                    return RetrievalStrategy.NO_RETRIEVAL
                else:
                    return RetrievalStrategy.INTERNAL_ONLY
                    
        except Exception as e:
            # Fallback em caso de erro
            return RetrievalStrategy.INTERNAL_ONLY
```

**💡 POR QUE ESTE MÓDULO É EXCELENTE:**

```
Antes (sistema atual):
"Qual o preço do PETR4?"
→ Busca no RAG interno (não tem preço atual)
→ Não encontra
→ Fallback para web search
→ DESPERDIÇOU tempo + tokens

Depois (com RetrievalPlanner):
"Qual o preço do PETR4?"
→ RetrievalPlanner: WEB_ONLY
→ Vai direto pra web
→ EFICIENTE

Economia estimada: 30-40% de buscas desnecessárias
```

---

### 4.5 📁 `services/self_correction.py`

**ARQUIVO:** ✨ NOVO (criar do zero)

**LOCALIZAÇÃO:** `services/self_correction.py`

```python
"""
Self-Correction Layer - Valida respostas antes de enviar.

Esta é outra ideia EXCELENTE do Plano B.
Adiciona uma camada de safety que pega erros antes do usuário ver.
"""

from typing import Dict, Optional
from openai import AsyncOpenAI


class SelfCorrection:
    """
    Valida se a resposta gerada responde adequadamente à pergunta.
    
    ✅ Usa gpt-4o-mini (task de validação simples)
    ✅ Temperature = 0.1 (validação precisa consistência)
    """
    
    def __init__(self, openai_client: AsyncOpenAI):
        self.client = openai_client
    
    async def validate_response(
        self,
        original_question: str,
        generated_response: str,
        context_used: str = ""
    ) -> Dict:
        """
        Valida se resposta está adequada.
        
        Args:
            original_question: Pergunta do assessor
            generated_response: Resposta gerada pelo GPT-4o
            context_used: Contexto RAG usado (opcional)
        
        Returns:
            {
                "is_valid": bool,
                "reason": str,  # se inválido
                "suggestion": str  # como corrigir
            }
        
        Exemplos de INVALID:
        - Resposta não relacionada à pergunta
        - Resposta vaga quando pergunta era específica
        - Resposta inventou dados não presentes no contexto
        - Resposta em tom inadequado
        """
        
        system_prompt = """Você valida se uma resposta gerada responde adequadamente à pergunta do usuário.

Marque como INVALID se:
- Resposta não responde a pergunta
- Resposta é vaga quando pergunta era específica
- Resposta menciona dados numéricos não presentes no contexto
- Resposta está em tom inadequado (muito formal, muito casual)
- Resposta inventou informações

Marque como VALID se:
- Resposta responde diretamente a pergunta
- Informações batem com o contexto fornecido
- Tom está adequado (profissional mas próximo)
- Se não tinha informação, admitiu claramente

Retorne JSON:
{
  "is_valid": true/false,
  "reason": "motivo se inválido",
  "suggestion": "como corrigir"
}"""
        
        user_prompt = f"""PERGUNTA DO ASSESSOR:
{original_question}

CONTEXTO DISPONÍVEL:
{context_used or "(Nenhum contexto RAG)"}

RESPOSTA GERADA:
{generated_response}

Validação:"""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            import json
            validation = json.loads(response.choices[0].message.content)
            return validation
            
        except Exception as e:
            # Em caso de erro, assume válido (fail-safe)
            return {
                "is_valid": True,
                "reason": "",
                "suggestion": ""
            }
```

**💡 BENEFÍCIO REAL:**

```
Cenário sem Self-Correction:
Assessor: "Qual o DY do BTLG11?"
Bot: "BTLG11 é um ótimo fundo de lajes corporativas..."
     (não respondeu o DY, só descreveu o fundo)
     
Cenário com Self-Correction:
Bot gera: "BTLG11 é um ótimo fundo..."
→ Self-Correction: INVALID - "não respondeu o DY"
→ Regenera: "O DY do BTLG11 está em 0,85% a.m."
→ Envia versão corrigida

Taxa de erro estimada: -60% (6 em cada 10 erros são pegos)
```

---

### 4.6 📁 `services/incremental_summarizer.py`

**ARQUIVO:** ✨ NOVO (criar do zero)

**LOCALIZAÇÃO:** `services/incremental_summarizer.py`

```python
"""
Resumo Incremental para conversas longas.

Resumo a cada 15 mensagens evita explodir token count.
"""

from typing import List, Dict
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from database.models.conversation import Conversation
from datetime import datetime


class IncrementalSummarizer:
    """
    Resume conversas incrementalmente.
    
    ✅ Usa gpt-4o-mini (resumo não precisa GPT-4o)
    ✅ Executa a cada 15 mensagens
    """
    
    def __init__(self, openai_client: AsyncOpenAI, db_session: Session):
        self.client = openai_client
        self.db = db_session
    
    async def check_and_summarize(
        self,
        conversation_id: str,
        messages: List[Dict]
    ) -> bool:
        """
        Verifica se precisa resumir e executa se necessário.
        
        Returns:
            True se resumiu, False se não
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return False
        
        # Verificar se atingiu 15 mensagens desde último resumo
        count_since_last = conversation.message_count_since_summary or 0
        
        if count_since_last >= 15:
            # Executar resumo
            summary = await self._generate_summary(messages[-15:])
            
            # Salvar resumo
            conversation.incremental_summary = summary
            conversation.last_summary_at = datetime.now()
            conversation.message_count_since_summary = 0
            
            self.db.commit()
            return True
        
        else:
            # Incrementar contador
            conversation.message_count_since_summary = count_since_last + 1
            self.db.commit()
            return False
    
    async def _generate_summary(self, messages: List[Dict]) -> str:
        """Gera resumo das últimas 15 mensagens"""
        
        # Formatar mensagens
        formatted = []
        for msg in messages:
            sender = "Assessor" if msg.get("sender_type") == "user" else "Stevan"
            text = msg.get("text", "")
            formatted.append(f"{sender}: {text}")
        
        messages_text = "\n".join(formatted)
        
        system_prompt = """Resume as últimas 15 mensagens da conversa.

Foque em:
- Tópicos discutidos
- Produtos/ativos mencionados
- Perguntas principais e respostas
- Documentos enviados
- Decisões tomadas

Seja conciso (máximo 5 linhas)."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": messages_text}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception:
            return f"Resumo de {len(messages)} mensagens (erro ao gerar)"
    
    def get_summary_for_context(self, conversation_id: str) -> str:
        """
        Retorna resumo para incluir no contexto.
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation and conversation.incremental_summary:
            return f"[RESUMO DA CONVERSA ANTERIOR]\n{conversation.incremental_summary}\n"
        
        return ""
```

---

## 5. NOVOS COMPONENTES

### 5.1 ✨ Tabela de Novos Arquivos

| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `services/conversation_state_manager.py` | ✨ NOVO | Gerencia estado semântico |
| `services/conversational_analyzer.py` | ✨ NOVO | Análise contextual (GPT-4o) |
| `services/retrieval_planner.py` | ✨ NOVO | Decide estratégia de busca |
| `services/self_correction.py` | ✨ NOVO | Valida respostas |
| `services/incremental_summarizer.py` | ✨ NOVO | Resume conversas longas |

---

### 5.2 🔄 Arquivos a Modificar

| Arquivo | Modificações |
|---------|--------------|
| `database/models/conversation.py` | Adicionar campos de estado |
| `services/openai_agent.py` | Integrar function calling + novo contexto |
| `services/retrieval.py` | Adicionar conversational boost |
| `api/endpoints/whatsapp_webhook.py` | Novo pipeline de processamento |

---

## 6. MIGRAÇÕES DE BANCO DE DADOS

### 6.1 Migration Script

**ARQUIVO:** Criar `database/migrations/add_conversation_state_fields.py`

```python
"""
Migration: Adiciona campos de conversation state

Gerado em: 2026-03-16
Aplica em: tabela conversations
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


def upgrade():
    """Adiciona novos campos"""
    
    # Campos de conversation state
    op.add_column('conversations', 
        sa.Column('current_topic', sa.String(200), nullable=True))
    
    op.add_column('conversations',
        sa.Column('topic_started_at', sa.DateTime(), nullable=True))
    
    op.add_column('conversations',
        sa.Column('implicit_context', JSONB(), nullable=False, server_default='{}'))
    
    op.add_column('conversations',
        sa.Column('conversation_mode', sa.String(50), nullable=False, server_default='question_answering'))
    
    op.add_column('conversations',
        sa.Column('pending_clarification', sa.String(255), nullable=True))
    
    # Campos de resumo incremental
    op.add_column('conversations',
        sa.Column('incremental_summary', sa.Text(), nullable=True))
    
    op.add_column('conversations',
        sa.Column('last_summary_at', sa.DateTime(), nullable=True))
    
    op.add_column('conversations',
        sa.Column('message_count_since_summary', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    """Remove campos"""
    
    op.drop_column('conversations', 'message_count_since_summary')
    op.drop_column('conversations', 'last_summary_at')
    op.drop_column('conversations', 'incremental_summary')
    op.drop_column('conversations', 'pending_clarification')
    op.drop_column('conversations', 'conversation_mode')
    op.drop_column('conversations', 'implicit_context')
    op.drop_column('conversations', 'topic_started_at')
    op.drop_column('conversations', 'current_topic')
```

**🔴 PERGUNTE AO USUÁRIO:**

```
ANTES de rodar a migration:

1. O projeto usa Alembic para migrations?
2. Se sim, qual o comando para gerar migration?
   alembic revision -m "add conversation state fields"
   
3. Se não, devo criar SQL direto?
   
4. Há ambiente de staging para testar antes de produção?

AGUARDAR CONFIRMAÇÃO
```

---

## 7. PLANO DE IMPLEMENTAÇÃO FASEADO

### FASE 1 — Preparação (Semana 1) 🟢

**Objetivo:** Criar infraestrutura sem quebrar sistema atual

**Tarefas:**

1. **Migration de banco**
   ```bash
   # Criar migration
   alembic revision -m "add conversation state fields"
   
   # Aplicar em DEV
   alembic upgrade head
   ```

2. **Criar novos módulos** (sem integrar ainda)
   - [x] `services/conversation_state_manager.py`
   - [x] `services/conversational_analyzer.py`
   - [x] `services/retrieval_planner.py`
   - [x] `services/self_correction.py`
   - [x] `services/incremental_summarizer.py`

3. **Testes unitários** (isolados)
   ```python
   # Testar cada módulo separadamente
   pytest tests/test_conversation_state_manager.py
   pytest tests/test_conversational_analyzer.py
   # etc
   ```

**Critério de Sucesso:**
- ✅ Migration aplicada sem erros
- ✅ Módulos criados e testados isoladamente
- ✅ Sistema atual continua funcionando

---

### FASE 2 — Feature Flag + A/B Test (Semana 2) 🟡

**Objetivo:** Rodar novo pipeline em paralelo com antigo

**Tarefas:**

1. **Adicionar feature flag**
   
   **Arquivo:** `core/config.py`
   ```python
   # Adicionar ao config existente
   
   # Feature flags
   ENABLE_HYBRID_PIPELINE = os.getenv("ENABLE_HYBRID_PIPELINE", "false") == "true"
   HYBRID_PIPELINE_PERCENTAGE = int(os.getenv("HYBRID_PIPELINE_PCT", "0"))
   ```

2. **Modificar webhook para roteamento**
   
   **Arquivo:** `api/endpoints/whatsapp_webhook.py`
   ```python
   import random
   from core.config import ENABLE_HYBRID_PIPELINE, HYBRID_PIPELINE_PERCENTAGE
   
   async def process_incoming_message(...):
       # Decisão de roteamento
       use_hybrid = (
           ENABLE_HYBRID_PIPELINE 
           and random.randint(1, 100) <= HYBRID_PIPELINE_PERCENTAGE
       )
       
       if use_hybrid:
           # 🔴 PERGUNTE AO USUÁRIO: qual nome dar a essa função?
           await process_with_hybrid_pipeline(...)
       else:
           await process_with_legacy_pipeline(...)
   ```

3. **Implementar pipeline híbrido**
   
   **Arquivo:** `api/endpoints/whatsapp_webhook.py`
   ```python
   async def process_with_hybrid_pipeline(
       message: str,
       conversation_id: str,
       # ... outros params
   ):
       """
       Novo pipeline híbrido.
       
       ⚠️ REPLIT: Siga exatamente esta ordem:
       1. Carregar ConversationState
       2. ConversationalAnalyzer
       3. ConversationStateManager.update()
       4. Verificar mudança de tópico
       5. RetrievalPlanner
       6. Executar busca (RAG/Web/Ambos)
       7. Response Generator
       8. Self-Correction
       9. Enviar
       10. IncrementalSummarizer
       """
       
       # 1. Carregar estado
       state_manager = ConversationStateManager(db_session)
       conv_state = state_manager.get_or_create_state(conversation_id)
       
       # 2. Análise conversacional
       analyzer = ConversationalAnalyzer(openai_client)
       analysis = await analyzer.analyze_message(
           message=message,
           conversation_history=conversation_history,
           current_state=conv_state
       )
       
       # 3. Atualizar estado
       conv_state = state_manager.update_with_analysis(
           state=conv_state,
           analysis=analysis,
           message=message
       )
       
       # 4. Verificar mudança de tópico
       if analysis["topic_change_detected"]:
           new_topic = analysis["new_topic"]
           
           if state_manager.should_confirm_topic_change(
               state=conv_state,
               new_topic=new_topic,
               message=message
           ):
               # Pedir confirmação
               response_text = (
                   f"Mudando de {conv_state.current_topic} pra {new_topic}, "
                   f"ou quer comparar os dois?"
               )
               await send_whatsapp_message(phone, response_text)
               return
       
       # 5. Planejar retrieval
       planner = RetrievalPlanner(openai_client)
       retrieval_strategy = await planner.plan_retrieval(
           message=message,
           analysis=analysis,
           current_topic=conv_state.current_topic
       )
       
       # 6. Executar busca
       context = ""
       if retrieval_strategy == "INTERNAL_ONLY":
           rag_results = await rag_search(analysis["suggested_rag_query"])
           context = format_rag_results(rag_results)
       
       elif retrieval_strategy == "WEB_ONLY":
           web_results = await web_search(analysis["suggested_rag_query"])
           context = format_web_results(web_results)
       
       elif retrieval_strategy == "INTERNAL_PLUS_WEB":
           rag_results = await rag_search(analysis["suggested_rag_query"])
           web_results = await web_search(analysis["suggested_rag_query"])
           context = format_combined_results(rag_results, web_results)
       
       # 7. Gerar resposta
       agent = OpenAIAgent(openai_client)
       response = await agent.generate_response_hybrid(
           message=message,
           conversation_id=conversation_id,
           conversation_state=conv_state,
           analysis=analysis,
           context=context
       )
       
       # 8. Self-correction
       corrector = SelfCorrection(openai_client)
       validation = await corrector.validate_response(
           original_question=message,
           generated_response=response["text"],
           context_used=context
       )
       
       if not validation["is_valid"]:
           # Regenerar com feedback
           response = await agent.regenerate_with_feedback(
               original_response=response,
               feedback=validation["suggestion"]
           )
       
       # 9. Enviar
       if response["text"]:
           await send_whatsapp_message(phone, response["text"])
       
       # Executar function calls
       for action in response.get("actions", []):
           await execute_action(action)
       
       # 10. Resumo incremental
       summarizer = IncrementalSummarizer(openai_client, db_session)
       await summarizer.check_and_summarize(
           conversation_id=conversation_id,
           messages=conversation_history
       )
       
       # Salvar estado
       state_manager.save_state(conversation_id, conv_state)
   ```

4. **Logging extensivo**
   ```python
   import logging
   
   logger.info("hybrid_pipeline_decision", extra={
       "conversation_id": conversation_id,
       "use_hybrid": use_hybrid,
       "percentage": HYBRID_PIPELINE_PERCENTAGE
   })
   
   logger.info("conversational_analysis", extra={
       "analysis": analysis,
       "state_before": conv_state.to_dict()
   })
   ```

5. **Deploy gradual**
   ```bash
   # Começar com 10%
   export ENABLE_HYBRID_PIPELINE=true
   export HYBRID_PIPELINE_PCT=10
   
   # Monitorar por 2 dias
   # Se OK, aumentar para 25%
   # Se OK, aumentar para 50%
   ```

**🔴 PERGUNTE AO USUÁRIO a cada incremento:**

```
Métricas após 2 dias com 10% no novo pipeline:

- Latência média: X segundos (antes: Y)
- Escalações: X% (antes: Y%)
- Erros: X (antes: Y)
- Feedback positivo: X% (antes: Y%)

CONTINUAR para 25% ou ROLLBACK?
```

---

### FASE 3 — Function Calling (Semana 3) 🟡

**Objetivo:** Substituir marcadores por function calling

**Tarefas:**

1. **Modificar openai_agent.py**
   
   **Localizar:** Método `generate_response`
   
   **Adicionar:**
   ```python
   def _get_function_definitions(self) -> List[Dict]:
       """Define funções disponíveis"""
       return [
           {
               "type": "function",
               "function": {
                   "name": "send_document",
                   "description": "Envia PDF/imagem ao assessor",
                   "parameters": {
                       "type": "object",
                       "properties": {
                           "filename": {"type": "string"},
                           "mention_in_text": {"type": "boolean"}
                       },
                       "required": ["filename"]
                   }
               }
           },
           # ... outras funções
       ]
   ```

2. **Manter compatibilidade temporária**
   ```python
   # Processar AMBOS durante 1 semana:
   # - Function calls (novo)
   # - Marcadores [SEND_PDF] (antigo)
   ```

**Critério de Sucesso:**
- ✅ Function calling funcionando
- ✅ Sem quebra em envio de documentos
- ✅ Respostas mais naturais

---

### FASE 4 — Rollout 100% (Semana 4) 🟢

**Objetivo:** Novo pipeline vira padrão

**Tarefas:**

1. **Aumentar para 100%**
   ```bash
   export HYBRID_PIPELINE_PCT=100
   ```

2. **Monitorar 3 dias intensivamente**

3. **Remover código legacy**
   ```python
   # Após 1 semana de 100% sem problemas:
   # - Remover process_with_legacy_pipeline()
   # - Remover query_rewriter antigo (se não mais usado)
   ```

4. **Atualizar documentação**

---

## 8. TESTES E VALIDAÇÃO

### 8.1 Casos de Teste Prioritários

**TESTE 1: Continuação Implícita**
```
Assessor: "me fala do BTLG11"
Bot: "BTLG11 é um FII..."
    [current_topic = "BTLG11"]

Assessor: "e o dividend yield?"

✅ Esperado:
- analysis["is_implicit_continuation"] = true
- analysis["suggested_rag_query"] = "dividend yield BTLG11"
- Bot responde sobre DY do BTLG11

❌ Errado:
- Bot pergunta "DY de qual ativo?"
```

**TESTE 2: Retrieval Planner**
```
Assessor: "qual o preço do PETR4 agora?"

✅ Esperado:
- retrieval_strategy = "WEB_ONLY"
- Busca apenas na web, não no RAG

❌ Errado:
- Busca no RAG interno primeiro
```

**TESTE 3: Self-Correction**
```
Assessor: "qual o DY do BTLG11?"
Bot gera: "BTLG11 é um fundo de lajes corporativas..."
    (não respondeu o DY)

✅ Esperado:
- validation["is_valid"] = false
- Bot regenera resposta
- Resposta final menciona o DY

❌ Errado:
- Envia resposta sem mencionar DY
```

---

### 8.2 Scripts de Teste

**ARQUIVO:** `tests/test_hybrid_pipeline.py`

```python
"""Testes do pipeline híbrido"""

import pytest
from services.conversational_analyzer import ConversationalAnalyzer
from services.retrieval_planner import RetrievalPlanner
from services.conversation_state_manager import ConversationState

class TestConversationalAnalyzer:
    
    @pytest.mark.asyncio
    async def test_implicit_continuation(self):
        """Testa detecção de continuação implícita"""
        
        analyzer = ConversationalAnalyzer(mock_client)
        
        state = ConversationState(
            current_topic="BTLG11",
            topic_started_at=datetime.now()
        )
        
        history = [
            {"sender_type": "user", "text": "me fala do BTLG11"},
            {"sender_type": "bot", "text": "BTLG11 é um FII..."}
        ]
        
        analysis = await analyzer.analyze_message(
            message="e o dividend yield?",
            conversation_history=history,
            current_state=state
        )
        
        assert analysis["is_implicit_continuation"] == True
        assert "BTLG11" in analysis["suggested_rag_query"]

class TestRetrievalPlanner:
    
    @pytest.mark.asyncio
    async def test_web_only_for_current_price(self):
        """Testa decisão de buscar apenas na web"""
        
        planner = RetrievalPlanner(mock_client)
        
        analysis = {"primary_intent": "question"}
        
        strategy = await planner.plan_retrieval(
            message="qual o preço do PETR4 agora?",
            analysis=analysis
        )
        
        assert strategy == "WEB_ONLY"
```

---

## 9. CHECKLIST PARA REPLIT

### 9.1 Checklist Pré-Implementação

```markdown
## ✅ ANTES DE COMEÇAR

### Verificação de Ambiente
- [ ] Clone do repositório funcionando
- [ ] Python version >= 3.10
- [ ] PostgreSQL + pgvector configurado
- [ ] Variáveis de ambiente (.env) configuradas
- [ ] OpenAI API key válida

### Compreensão do Código Atual
- [ ] Li e entendi services/openai_agent.py
- [ ] Li e entendi api/endpoints/whatsapp_webhook.py
- [ ] Identifiquei todas as dependências entre módulos
- [ ] Entendi o fluxo atual de mensagens

### Confirmações com Usuário
- [ ] Estrutura de diretórios confirmada
- [ ] Modelo de banco de dados confirmado
- [ ] Sistema de migrations confirmado (Alembic?)
- [ ] Versão do OpenAI SDK confirmada
- [ ] Sistema atual usa marcadores ou function calling?

🔴 SOMENTE PROSSIGA APÓS TODOS OS ITENS CHECADOS
```

---

### 9.2 Checklist Durante Implementação

```markdown
## 🔄 DURANTE A IMPLEMENTAÇÃO

### Fase 1 - Preparação
- [ ] Migration criada e testada em DEV
- [ ] conversation_state_manager.py criado
- [ ] conversational_analyzer.py criado
- [ ] retrieval_planner.py criado
- [ ] self_correction.py criado
- [ ] incremental_summarizer.py criado
- [ ] Testes unitários passando

### Fase 2 - Feature Flag
- [ ] Feature flag adicionada ao config
- [ ] Roteamento implementado no webhook
- [ ] Pipeline híbrido implementado
- [ ] Logging extensivo configurado
- [ ] Deploy com 10% funcionando
- [ ] Métricas coletadas por 2 dias
- [ ] 🔴 APROVAÇÃO DO USUÁRIO para 25%
- [ ] Deploy com 25% funcionando
- [ ] 🔴 APROVAÇÃO DO USUÁRIO para 50%

### Fase 3 - Function Calling
- [ ] Function definitions implementadas
- [ ] Compatibilidade com marcadores mantida
- [ ] Testes de envio de documentos passando

### Fase 4 - Rollout
- [ ] Deploy 100% autorizado pelo usuário
- [ ] Monitoramento 3 dias sem problemas
- [ ] Código legacy removido
- [ ] Documentação atualizada
```

---

### 9.3 Perguntas Críticas para o Usuário

**🔴 REPLIT: Faça estas perguntas ANTES de implementar:**

```
PERGUNTA 1 - Estrutura do Código Atual:
"Confirmei que o webhook atual está em api/endpoints/whatsapp_webhook.py.
O método principal é `process_incoming_message` ou tem outro nome?
Posso ver a assinatura completa da função?"

PERGUNTA 2 - Sistema de Migrations:
"O projeto usa Alembic para migrations?
Se sim, qual o comando para criar nova migration?
Se não, devo criar SQL direto ou há outro sistema?"

PERGUNTA 3 - OpenAI SDK:
"Qual versão do OpenAI SDK está instalada?
Posso verificar em requirements.txt se é openai>=1.0.0?
O código atual usa AsyncOpenAI ou OpenAI síncrono?"

PERGUNTA 4 - Marcadores vs Function Calling:
"O sistema atual usa marcadores tipo [SEND_PDF:arquivo.pdf]
ou já usa function calling nativo do OpenAI?
Posso ver um exemplo de resposta gerada pelo bot?"

PERGUNTA 5 - Teste em Ambiente:
"Existe ambiente de staging/dev para testar antes de produção?
Ou testo direto em produção com feature flag?"

PERGUNTA 6 - Aprovação de Fases:
"Devo aguardar sua aprovação antes de aumentar % do
novo pipeline (10% → 25% → 50% → 100%)?
Como você quer que eu reporte as métricas?"
```

---

### 9.4 Template de Report para Usuário

**REPLIT: Use este template ao reportar cada fase:**

```markdown
## 📊 REPORT - FASE [N]

### Status da Implementação
- ✅ Completado: [lista de tarefas]
- ⚠️  Em andamento: [lista]
- ❌ Bloqueado: [lista + motivo]

### Métricas (se aplicável)
| Métrica | Antes | Depois | Variação |
|---------|-------|--------|----------|
| Latência média | X s | Y s | +/- Z% |
| Taxa de escalação | X% | Y% | +/- Z% |
| Erros | X | Y | +/- Z |
| Context retention | X% | Y% | +/- Z% |

### Próximos Passos
1. [Próxima tarefa]
2. [Próxima tarefa]

### Decisões Necessárias do Usuário
🔴 AGUARDANDO:
- [ ] Aprovação para aumentar % do pipeline?
- [ ] Confirmar configuração X?
- [ ] Outro...

### Observações
[Qualquer nota relevante, problema encontrado, etc]
```

---

## 10. RESUMO EXECUTIVO

### 10.1 O que Este Plano Faz

Este plano híbrido integra as **melhores ideias de dois planos de evolução**:

**Do Plano A (STEVAN_IMPROVEMENTS_SPEC.md):**
✅ GPT-4o como orquestrador central (menos perda de contexto)
✅ Function calling nativo (mais moderno)
✅ ConversationState flexível com contexto implícito
✅ Conversational boost no RAG

**Do Plano B (Stevan 2.0):**
✅ Retrieval Planner (decide onde buscar - economiza tokens)
✅ Self-Correction Layer (pega erros antes do usuário)
✅ Resumo Incremental (conversas longas)
✅ Uso estratégico de GPT-4o-mini (reduz custos)

**Resultado:**
🎯 Mais naturalidade + mais eficiência + menor custo

---

### 10.2 Benefícios Esperados

| Métrica | Baseline Atual | Meta Híbrida | Melhoria |
|---------|----------------|--------------|----------|
| **Context Retention** | ~40% | >85% | +112% |
| **Clarificações Desnecessárias** | ~35% | <15% | -57% |
| **Turnos até Resolução** | ~5 | <3 | -40% |
| **Frustração** | baseline | -60% | -60% |
| **Custo por Conversa** | $X | $Y (menor) | -30% |
| **Precisão de Busca** | baseline | +40% | +40% |

---

### 10.3 Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Latência aumentar | Média | Alto | Feature flag + rollback rápido |
| Bugs em produção | Baixa | Alto | A/B test gradual (10%→25%→50%) |
| Custo explodir | Baixa | Médio | Monitoring + alerts + uso de mini |
| Schema migration falhar | Baixa | Alto | Testar em DEV primeiro |

---

## 11. GLOSSÁRIO TÉCNICO

| Termo | Definição |
|-------|-----------|
| **ConversationState** | Estado semântico da conversa (tópico ativo, contexto implícito) |
| **Conversational Analyzer** | Módulo que analisa mensagem em contexto (GPT-4o) |
| **Retrieval Planner** | Decide ONDE buscar (interno/web/ambos) |
| **Self-Correction** | Valida resposta antes de enviar |
| **Incremental Summarizer** | Resume conversas a cada 15 mensagens |
| **Function Calling** | Recurso nativo do OpenAI para executar funções |
| **Conversational Boost** | Boost no RAG scoring para docs em contexto |
| **Implicit Continuation** | Mensagem continua tópico anterior sem mencioná-lo |

---

## FIM DO DOCUMENTO

**Versão:** 3.0 Híbrida  
**Última Atualização:** Março 2026  
**Próxima Revisão:** Após Fase 2 de implementação

---

**🔴 REPLIT: LEMBRE-SE**

1. **SEMPRE** pergunte ao usuário antes de decisões críticas
2. **SEMPRE** teste em DEV antes de produção
3. **SEMPRE** use feature flags para rollout gradual
4. **SEMPRE** reporte métricas ao usuário
5. **NUNCA** implemente tudo de uma vez
6. **NUNCA** assuma estrutura do código - verifique primeiro
7. **NUNCA** pule testes unitários
8. **NUNCA** faça deploy 100% sem A/B test
