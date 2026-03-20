import { useState } from "react";
import { AlertTriangle, XCircle, X, ChevronDown, ChevronUp, ExternalLink, Bot, User, Clock, Wifi, WifiOff, Search, Filter, MessageCircle } from "lucide-react";

function ConversationListItem({ name, phone, time, preview, unread, active }: {
  name: string; phone: string; time: string; preview: string; unread?: number; active?: boolean;
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
        {unread && unread > 0 && (
          <div className="w-5 h-5 rounded-full bg-[#4F46E5] text-white text-xs flex items-center justify-center flex-shrink-0">
            {unread}
          </div>
        )}
      </div>
    </div>
  );
}

export function SystemBanner() {
  const [expanded, setExpanded] = useState(false);
  const [dismissed, setDismissed] = useState(false);

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
          <ConversationListItem name="Nicolas Oliveira Garcia" phone="+55 11 94703-3973" time="06:53" preview="Bom dia, não entendi, é uma estrutura?" unread={1} active />
          <ConversationListItem name="Carlos Mendes" phone="+55 21 99887-6543" time="06:45" preview="Obrigado pela análise!" />
          <ConversationListItem name="Fernanda Lima" phone="+55 11 98765-4321" time="06:30" preview="Pode me enviar o relatório?" />
          <ConversationListItem name="Roberto Santos" phone="+55 31 97654-3210" time="Ontem" preview="Entendi, vou verificar com o cliente." />
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        {!dismissed && (
          <div className="border-b border-red-200">
            <div className="bg-red-50 px-4 py-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center">
                    <XCircle className="w-5 h-5 text-red-500" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-red-800">OpenAI: créditos esgotados</p>
                    <p className="text-xs text-red-600 mt-0.5">Bot não está respondendo mensagens · Desde 08:39</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setExpanded(!expanded)}
                    className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-red-700 bg-red-100 hover:bg-red-200 rounded-lg transition-colors"
                  >
                    {expanded ? "Menos" : "Detalhes"}
                    {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>
                  <button
                    onClick={() => setDismissed(true)}
                    className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-100 rounded-lg transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
              {expanded && (
                <div className="mt-3 pt-3 border-t border-red-200 space-y-2">
                  <div className="bg-white rounded-lg p-3 border border-red-200">
                    <div className="flex items-center gap-2 mb-2">
                      <Clock className="w-3.5 h-3.5 text-gray-400" />
                      <span className="text-xs text-gray-500">20/03/2026 08:39:12</span>
                    </div>
                    <p className="text-xs text-gray-700 font-mono">
                      Error 429: You exceeded your current quota. Please check your plan and billing details.
                    </p>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-red-600">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>3 mensagens afetadas nas últimas 2 horas</span>
                  </div>
                  <div className="flex gap-2">
                    <a href="https://platform.openai.com/account/billing" target="_blank" rel="noopener"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-700 bg-white border border-red-200 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      Verificar billing OpenAI
                    </a>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

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
              <p className="text-sm py-2 whitespace-pre-wrap break-words">A ideia é que você permaneça posicionado em PETR4 e continue capturando ganhos...</p>
            </div>
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
              <Bot className="w-4 h-4 text-[#4F46E5]" />
            </div>
          </div>

          <div className="flex items-start gap-2.5 mb-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              <User className="w-4 h-4 text-gray-500" />
            </div>
            <div>
              <div className="flex flex-col w-full max-w-[320px] leading-relaxed p-4 border border-gray-200 bg-gray-50 rounded-e-xl rounded-es-xl">
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-sm font-semibold text-gray-900">Nicolas Oliveira Garcia</span>
                  <span className="text-sm text-gray-500">06:53</span>
                </div>
                <p className="text-sm py-2 text-gray-900">Bom dia, não entendi, é uma estrutura?</p>
              </div>
              <div className="mt-1.5 flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-red-50 border border-red-200 text-red-600">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span className="text-xs font-medium">Bot não respondeu — erro de quota OpenAI</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
