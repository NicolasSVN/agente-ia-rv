import { useState, useEffect, useRef, useCallback } from 'react';
import { Search, Plus, User, Bot, Send, Phone, UserCheck, Loader2, MessageCircle } from 'lucide-react';

const API_BASE = '/api';

function formatPhone(phone) {
  if (!phone) return '-';
  if (phone.length === 13) {
    return `+${phone.slice(0,2)} (${phone.slice(2,4)}) ${phone.slice(4,9)}-${phone.slice(9)}`;
  }
  return phone;
}

function formatTimeAgo(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now - date;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return 'Agora';
  if (minutes < 60) return `${minutes}min`;
  if (hours < 24) return `${hours}h`;
  if (days < 7) return `${days}d`;
  return date.toLocaleDateString('pt-BR');
}

function StatusBadge({ status }) {
  const styles = {
    bot_active: 'bg-green-100 text-green-800',
    human_takeover: 'bg-amber-100 text-amber-800',
    closed: 'bg-gray-100 text-gray-600',
  };
  const labels = {
    bot_active: 'Bot',
    human_takeover: 'Humano',
    closed: 'Encerrada',
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100'}`}>
      {labels[status] || status}
    </span>
  );
}

function ChatBubble({ message, isLast }) {
  const isOutbound = message.direction === 'outbound';
  const senderLabels = { bot: 'Agente IA', human: 'Operador', contact: '' };
  const time = new Date(message.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  const content = message.body || message.transcription || '[Mídia]';

  if (isOutbound) {
    return (
      <div className="flex justify-end gap-2 mb-3">
        <div className={`max-w-[70%] rounded-2xl rounded-br px-4 py-3 ${
          message.sender_type === 'bot' ? 'bg-indigo-500' : 'bg-emerald-500'
        } text-white`}>
          {senderLabels[message.sender_type] && (
            <div className="text-xs font-semibold mb-1 opacity-90">{senderLabels[message.sender_type]}</div>
          )}
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
          <div className="text-xs mt-1 opacity-70 text-right">{time}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start gap-2 mb-3">
      <div className="w-8 h-8 rounded-full bg-primary-light flex items-center justify-center text-primary text-sm font-semibold flex-shrink-0">
        <User className="w-4 h-4" />
      </div>
      <div className="max-w-[70%] rounded-2xl rounded-bl px-4 py-3 bg-white border border-border">
        <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">{content}</p>
        <div className="text-xs mt-1 text-muted">{time}</div>
      </div>
    </div>
  );
}

function ConversationItem({ conversation, isActive, onClick }) {
  const displayName = conversation.assessor_name || conversation.contact_name || 'Desconhecido';
  return (
    <div
      onClick={onClick}
      className={`relative p-4 border-b border-border cursor-pointer transition-colors ${
        isActive ? 'bg-primary-light border-l-4 border-l-primary' : 'hover:bg-background'
      }`}
    >
      <div className="flex justify-between items-start mb-1">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-foreground text-sm">{displayName}</span>
          <StatusBadge status={conversation.status} />
        </div>
        <span className="text-xs text-muted">{formatTimeAgo(conversation.last_message_at)}</span>
      </div>
      <div className="text-xs text-muted mb-1">{formatPhone(conversation.phone)}</div>
      <div className="text-sm text-muted truncate">{conversation.last_message_preview || 'Sem mensagens'}</div>
      {conversation.unread_count > 0 && (
        <span className="absolute top-3 right-3 bg-red-500 text-white text-xs px-2 py-0.5 rounded-full font-semibold">
          {conversation.unread_count}
        </span>
      )}
    </div>
  );
}

function NewConversationModal({ isOpen, onClose, onSubmit, isLoading }) {
  const [phone, setPhone] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = () => {
    const phoneClean = phone.replace(/\D/g, '');
    if (!phoneClean || phoneClean.length < 10) {
      alert('Número de telefone inválido');
      return;
    }
    if (!message.trim()) {
      alert('Digite uma mensagem');
      return;
    }
    onSubmit({ phone: phoneClean, message: message.trim() });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-md mx-4 shadow-xl" onClick={e => e.stopPropagation()}>
        <div className="p-5 border-b border-border flex justify-between items-center">
          <h3 className="font-semibold text-lg text-foreground">Nova Conversa</h3>
          <button onClick={onClose} className="text-muted hover:text-foreground text-2xl">&times;</button>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Número de Telefone</label>
            <input
              type="text"
              value={phone}
              onChange={e => setPhone(e.target.value)}
              placeholder="Ex: 5511999999999"
              className="w-full px-4 py-3 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
            />
            <p className="text-xs text-muted mt-1">Formato: código do país + DDD + número</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Mensagem Inicial</label>
            <textarea
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder="Digite a mensagem..."
              rows={4}
              className="w-full px-4 py-3 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none resize-none"
            />
          </div>
        </div>
        <div className="p-5 border-t border-border flex gap-3 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-muted hover:text-foreground font-medium">
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="px-5 py-2 bg-primary text-white rounded-lg font-medium hover:bg-primary-dark disabled:opacity-50 flex items-center gap-2"
          >
            {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
            Enviar Mensagem
          </button>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [showNewModal, setShowNewModal] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const messagesEndRef = useRef(null);
  const eventSourceRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConversations = useCallback(async () => {
    try {
      let url = `${API_BASE}/conversations/?limit=100`;
      if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
      if (statusFilter) url += `&status=${statusFilter}`;
      const res = await fetch(url, { credentials: 'include' });
      if (res.status === 401) {
        window.location.href = '/login';
        return;
      }
      const data = await res.json();
      setConversations(data);
    } catch (err) {
      console.error('Erro ao carregar conversas:', err);
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, statusFilter]);

  const fetchMessages = async (conversationId) => {
    try {
      await fetch(`${API_BASE}/conversations/${conversationId}/sync-messages`, {
        method: 'POST',
        credentials: 'include',
      });
      const res = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, { credentials: 'include' });
      const data = await res.json();
      setMessages(data);
      setTimeout(scrollToBottom, 100);
    } catch (err) {
      console.error('Erro ao carregar mensagens:', err);
    }
  };

  const selectConversation = async (conv) => {
    setCurrentConversation(conv);
    setMessages([]);
    await fetchMessages(conv.id);
  };

  const sendMessage = async () => {
    if (!messageInput.trim() || !currentConversation) return;
    setIsSending(true);
    try {
      const res = await fetch(`${API_BASE}/conversations/${currentConversation.id}/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ message: messageInput.trim() }),
      });
      if (!res.ok) throw new Error('Erro ao enviar');
      setMessageInput('');
      await fetchMessages(currentConversation.id);
      await fetchConversations();
    } catch (err) {
      alert('Erro ao enviar mensagem');
    } finally {
      setIsSending(false);
    }
  };

  const toggleTakeover = async () => {
    if (!currentConversation) return;
    const action = currentConversation.status === 'human_takeover' ? 'release' : 'takeover';
    try {
      const res = await fetch(`${API_BASE}/conversations/${currentConversation.id}/takeover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ action }),
      });
      const result = await res.json();
      setCurrentConversation(prev => ({ ...prev, status: result.status }));
      await fetchConversations();
    } catch (err) {
      alert('Erro ao alterar status');
    }
  };

  const startNewConversation = async ({ phone, message }) => {
    setIsCreating(true);
    try {
      const res = await fetch(`${API_BASE}/conversations/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ phone, message }),
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.detail || 'Erro');
      setShowNewModal(false);
      await fetchConversations();
      if (result.conversation_id) {
        const conv = conversations.find(c => c.id === result.conversation_id);
        if (conv) selectConversation(conv);
      }
    } catch (err) {
      alert('Erro: ' + err.message);
    } finally {
      setIsCreating(false);
    }
  };

  useEffect(() => {
    const syncAndLoad = async () => {
      try {
        await fetch(`${API_BASE}/conversations/sync`, { method: 'POST', credentials: 'include' });
      } catch {}
      fetchConversations();
    };
    syncAndLoad();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => fetchConversations(), 300);
    return () => clearTimeout(timer);
  }, [searchQuery, statusFilter, fetchConversations]);

  useEffect(() => {
    const connectSSE = () => {
      if (eventSourceRef.current) eventSourceRef.current.close();
      const es = new EventSource(`${API_BASE}/conversations/stream`);
      es.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'new_message' || data.type === 'conversation_updated') {
            await fetchConversations();
            if (currentConversation && data.data?.conversation_id === currentConversation.id) {
              await fetchMessages(currentConversation.id);
            }
          }
        } catch {}
      };
      es.onerror = () => {
        es.close();
        setTimeout(connectSSE, 5000);
      };
      eventSourceRef.current = es;
    };
    connectSSE();
    return () => eventSourceRef.current?.close();
  }, [currentConversation]);

  return (
    <div className="py-4">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Conversas</h1>
          <p className="text-muted">Visualize e gerencie todas as conversas do agente</p>
        </div>
        <button
          onClick={() => setShowNewModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg font-medium hover:bg-primary-dark"
        >
          <Plus className="w-4 h-4" />
          Nova Conversa
        </button>
      </div>

      <div className="grid grid-cols-[380px_1fr] gap-6" style={{ height: 'calc(100vh - 200px)' }}>
        <div className="bg-white rounded-2xl border border-border flex flex-col overflow-hidden">
          <div className="p-4 border-b border-border">
            <div className="relative mb-3">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Buscar por número ou nome..."
                className="w-full pl-10 pr-4 py-2.5 border border-border rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
              />
            </div>
            <div className="flex gap-2">
              {[{ value: '', label: 'Todas' }, { value: 'bot_active', label: 'Bot' }, { value: 'human_takeover', label: 'Humano' }].map(f => (
                <button
                  key={f.value}
                  onClick={() => setStatusFilter(f.value)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                    statusFilter === f.value
                      ? 'bg-primary text-white border-primary'
                      : 'bg-white text-muted border-border hover:bg-background'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto scrollbar-thin">
            {isLoading ? (
              <div className="flex justify-center p-10">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : conversations.length === 0 ? (
              <div className="p-10 text-center text-muted">Nenhuma conversa encontrada</div>
            ) : (
              conversations.map(conv => (
                <ConversationItem
                  key={conv.id}
                  conversation={conv}
                  isActive={currentConversation?.id === conv.id}
                  onClick={() => selectConversation(conv)}
                />
              ))
            )}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-border flex flex-col overflow-hidden">
          {!currentConversation ? (
            <div className="flex-1 flex flex-col items-center justify-center text-muted">
              <MessageCircle className="w-16 h-16 mb-4 opacity-30" />
              <h3 className="text-lg font-semibold text-foreground mb-2">Selecione uma conversa</h3>
              <p>Clique em uma conversa à esquerda para visualizar o histórico</p>
            </div>
          ) : (
            <>
              <div className="p-4 border-b border-border flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-primary-light flex items-center justify-center text-primary font-semibold text-lg">
                    {(currentConversation.assessor_name || currentConversation.contact_name || '?').charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground">
                      {currentConversation.assessor_name || currentConversation.contact_name || 'Desconhecido'}
                    </h3>
                    <p className="text-sm text-muted">{formatPhone(currentConversation.phone)}</p>
                  </div>
                </div>
                <button
                  onClick={toggleTakeover}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                    currentConversation.status === 'human_takeover'
                      ? 'bg-green-100 text-green-800 hover:bg-green-200'
                      : 'bg-amber-100 text-amber-800 hover:bg-amber-200'
                  }`}
                >
                  {currentConversation.status === 'human_takeover' ? (
                    <>
                      <Bot className="w-4 h-4" />
                      Devolver ao Agente
                    </>
                  ) : (
                    <>
                      <UserCheck className="w-4 h-4" />
                      Assumir Conversa
                    </>
                  )}
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-4 bg-background scrollbar-thin">
                {messages.length === 0 ? (
                  <div className="text-center text-muted py-10">Nenhuma mensagem ainda</div>
                ) : (
                  <>
                    {messages.map((msg, idx) => (
                      <ChatBubble key={msg.id} message={msg} isLast={idx === messages.length - 1} />
                    ))}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              <div className="p-4 border-t border-border flex gap-3">
                <input
                  type="text"
                  value={messageInput}
                  onChange={e => setMessageInput(e.target.value)}
                  onKeyPress={e => e.key === 'Enter' && sendMessage()}
                  placeholder="Digite sua mensagem..."
                  className="flex-1 px-4 py-3 border border-border rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                />
                <button
                  onClick={sendMessage}
                  disabled={isSending || !messageInput.trim()}
                  className="px-5 py-3 bg-primary text-white rounded-xl font-medium hover:bg-primary-dark disabled:opacity-50 flex items-center gap-2"
                >
                  {isSending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  Enviar
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      <NewConversationModal
        isOpen={showNewModal}
        onClose={() => setShowNewModal(false)}
        onSubmit={startNewConversation}
        isLoading={isCreating}
      />
    </div>
  );
}

export default App;
