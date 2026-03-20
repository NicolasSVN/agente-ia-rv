import { useState } from "react";
import { AlertTriangle, X, ChevronDown, ChevronUp, Wifi, WifiOff, Bot, User, Clock, RefreshCw, MessageCircle, Search } from "lucide-react";

function ConversationListItem({ name, time, preview, active }: {
  name: string; time: string; preview: string; active?: boolean;
}) {
  return (
    <div className={`px-4 py-3 cursor-pointer transition-colors ${active ? "bg-indigo-50 border-l-2 border-[#4F46E5]" : "hover:bg-gray-50 border-l-2 border-transparent"}`}>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gray-200 flex-shrink-0 flex items-center justify-center">
          <User className="w-5 h-5 text-gray-500" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-gray-900 truncate">{name}</span>
            <span className="text-xs text-gray-500 flex-shrink-0">{time}</span>
          </div>
          <p className="text-xs text-gray-500 truncate mt-0.5">{preview}</p>
        </div>
      </div>
    </div>
  );
}

export function WarningBanner() {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="min-h-screen bg-white flex">
      <div className="w-[340px] border-r border-gray-200 flex flex-col bg-white">
        <div className="px-4 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <MessageCircle className="w-5 h-5 text-[#4F46E5]" />
              Conversas
            </h1>
          </div>
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input type="text" placeholder="Buscar conversas..." className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#4F46E5]/20 focus:border-[#4F46E5]" />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          <ConversationListItem name="Nicolas Oliveira Garcia" time="06:53" preview="Bom dia, não entendi, é uma estrutura?" active />
          <ConversationListItem name="Carlos Mendes" time="06:45" preview="Obrigado pela análise!" />
          <ConversationListItem name="Fernanda Lima" time="06:30" preview="Pode me enviar o relatório?" />
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        <div className="border-b border-amber-200">
          <div className="bg-amber-50 px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center">
                  <WifiOff className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-amber-800">Z-API: conexão instável</p>
                  <p className="text-xs text-amber-600 mt-0.5">Algumas mensagens podem não ser entregues · Reconectando...</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-100 hover:bg-amber-200 rounded-lg transition-colors"
                >
                  {expanded ? "Menos" : "Detalhes"}
                  {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
                <button className="p-1.5 text-amber-400 hover:text-amber-600 hover:bg-amber-100 rounded-lg transition-colors">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
            {expanded && (
              <div className="mt-3 pt-3 border-t border-amber-200 space-y-2">
                <div className="bg-white rounded-lg p-3 border border-amber-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Clock className="w-3.5 h-3.5 text-gray-400" />
                    <span className="text-xs text-gray-500">20/03/2026 08:35:00</span>
                  </div>
                  <p className="text-xs text-gray-700 font-mono">
                    Z-API endpoint /chat-messages returned 500. Multi-device mode may be causing instability.
                  </p>
                </div>
                <div className="flex items-center gap-2 text-xs text-amber-700">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Tentativa de reconexão em andamento (3ª tentativa)</span>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
              <User className="w-5 h-5 text-gray-500" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-gray-900">Nicolas Oliveira Garcia</h2>
              <p className="text-xs text-gray-500">+55 (11) 94703-3973 · DGT MGF · Alysson</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border bg-indigo-50 text-[#4F46E5] border-indigo-200">
              <Bot className="w-3 h-3" />
              Bot
            </span>
            <button className="px-3 py-1.5 text-xs font-medium text-white bg-[#4F46E5] hover:bg-[#4338CA] rounded-lg transition-colors">
              Assumir Ticket
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 bg-gray-50/50">
          <div className="flex items-start gap-2.5 justify-end mb-4">
            <div className="flex flex-col w-full max-w-[320px] leading-relaxed p-4 rounded-s-xl rounded-ee-xl bg-[#4F46E5] text-white">
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-sm font-semibold">Agente IA</span>
                <span className="text-sm opacity-75">06:50</span>
              </div>
              <p className="text-sm py-2 whitespace-pre-wrap break-words">Bom dia Nicolas! Vi que você tem interesse na estrutura de proteção para PETR4. Posso explicar os detalhes da operação.</p>
            </div>
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
              <Bot className="w-4 h-4 text-[#4F46E5]" />
            </div>
          </div>

          <div className="flex items-start gap-2.5 mb-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              <User className="w-4 h-4 text-gray-500" />
            </div>
            <div className="flex flex-col w-full max-w-[320px] leading-relaxed p-4 border border-gray-200 bg-gray-50 rounded-e-xl rounded-es-xl">
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-sm font-semibold text-gray-900">Nicolas Oliveira Garcia</span>
                <span className="text-sm text-gray-500">06:53</span>
              </div>
              <p className="text-sm py-2 text-gray-900">Bom dia, não entendi, é uma estrutura?</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
