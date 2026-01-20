"""
Agente de IA usando a API da OpenAI.
Gera respostas contextualizadas para perguntas dos usuários.
"""
from openai import OpenAI
from typing import List, Optional, Tuple
from core.config import get_settings
from services.vector_store import get_vector_store

settings = get_settings()


class OpenAIAgent:
    """Agente de IA para gerar respostas usando GPT."""
    
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Prompt do sistema que define o comportamento do agente
        self.system_prompt = """Você é um assistente virtual especializado em assessoria financeira.
Seu papel é ajudar clientes com dúvidas sobre investimentos, produtos financeiros e serviços.

REGRAS IMPORTANTES:
1. Responda sempre de forma educada e profissional.
2. Use o contexto fornecido para basear suas respostas.
3. Se a informação não estiver disponível no contexto, seja honesto e diga que não tem essa informação.
4. Quando não puder ajudar adequadamente, pergunte se o cliente deseja abrir um chamado para falar com um assessor.
5. Mantenha as respostas concisas e objetivas, adequadas para WhatsApp.
6. Nunca invente informações sobre produtos, taxas ou valores.

Para abrir um chamado, o usuário deve responder "SIM" ou "sim" quando perguntado."""
    
    def _build_context(self, documents: List[dict]) -> str:
        """Constrói o contexto a partir dos documentos encontrados."""
        if not documents:
            return "Nenhum contexto relevante encontrado na base de conhecimento."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            title = doc.get('metadata', {}).get('title', f'Documento {i}')
            content = doc.get('content', '')
            context_parts.append(f"[{title}]\n{content}")
        
        return "\n\n---\n\n".join(context_parts)
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[dict]] = None
    ) -> Tuple[str, bool, List[dict]]:
        """
        Gera uma resposta para a mensagem do usuário.
        
        Args:
            user_message: Mensagem do usuário
            conversation_history: Histórico da conversa (opcional)
            
        Returns:
            Tuple contendo:
            - response: Resposta gerada
            - should_create_ticket: Se deve criar um chamado
            - context_documents: Documentos usados como contexto
        """
        if not self.client:
            return (
                "Desculpe, o serviço de IA não está configurado no momento. "
                "Deseja abrir um chamado para falar com um assessor?",
                False,
                []
            )
        
        # Verifica se o usuário quer criar um chamado
        if user_message.lower().strip() in ['sim', 'yes', 's', 'quero', 'pode ser']:
            return (
                "Perfeito! Estou abrindo um chamado para você. "
                "Um de nossos assessores entrará em contato em breve. "
                "Obrigado pela paciência!",
                True,
                []
            )
        
        # Busca contexto relevante na base de conhecimento
        vs = get_vector_store()
        context_documents = vs.search(user_message, n_results=3) if vs else []
        context = self._build_context(context_documents)
        
        # Prepara as mensagens para a API
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Adiciona histórico se existir
        if conversation_history:
            messages.extend(conversation_history[-6:])  # Últimas 6 mensagens
        
        # Adiciona contexto e mensagem atual
        messages.append({
            "role": "user",
            "content": f"""CONTEXTO DA BASE DE CONHECIMENTO:
{context}

---

PERGUNTA DO CLIENTE:
{user_message}

Responda de forma clara e objetiva. Se não encontrar a informação no contexto, 
pergunte se o cliente deseja abrir um chamado."""
        })
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Modelo mais recente e eficiente
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Detecta se a IA sugeriu abrir um chamado
            suggest_ticket = any(phrase in ai_response.lower() for phrase in [
                "abrir um chamado",
                "falar com um assessor",
                "deseja abrir",
                "quer abrir"
            ])
            
            return ai_response, False, context_documents
            
        except Exception as e:
            return (
                f"Desculpe, ocorreu um erro ao processar sua mensagem. "
                "Deseja abrir um chamado para falar com um assessor?",
                False,
                []
            )
    
    def is_available(self) -> bool:
        """Verifica se o agente está configurado e disponível."""
        return self.client is not None


# Instância global do agente
openai_agent = OpenAIAgent()
