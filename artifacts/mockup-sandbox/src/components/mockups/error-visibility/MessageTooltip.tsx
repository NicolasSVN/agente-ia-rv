import { useState } from "react";
import { User, Bot, AlertTriangle, Clock, X, CheckCheck, MoreVertical, UserCheck } from "lucide-react";

function ChatBubble({ message, contactName, showError = false }: {
  message: { direction: string; sender_type: string; body: string; created_at: string; ai_intent?: string; ai_error?: string };
  contactName: string;
  showError?: boolean;
}) {
  const [tooltipOpen, setTooltipOpen] = useState(false);
  const isOutbound = message.direction === "outbound";
  const senderLabels: Record<string, string> = { bot: "Agente IA", human: "Operador" };
  const senderName = isOutbound ? senderLabels[message.sender_type] || "Sistema" : contactName || "Contato";
  const time = new Date(message.created_at).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  const hasError = message.ai_intent === "error_suppressed";

  if (isOutbound) {
    return (
      <div className="flex items-start gap-2.5 justify-end mb-4">
        <button className="self-center p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
          <MoreVertical className="w-5 h-5" />
        </button>
        <div className={`flex flex-col w-full max-w-[320px] leading-relaxed p-4 rounded-s-xl rounded-ee-xl ${
          message.sender_type === "bot" ? "bg-[#4F46E5] text-white" : "bg-emerald-600 text-white"
        }`}>
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-sm font-semibold">{senderName}</span>
            <span className="text-sm opacity-75">{time}</span>
          </div>
          <p className="text-sm py-2 whitespace-pre-wrap break-words">{message.body}</p>
          <div className="flex items-center gap-1.5 text-xs opacity-75">
            <CheckCheck className="w-4 h-4" />
            <span>Enviada</span>
          </div>
        </div>
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          message.sender_type === "bot" ? "bg-indigo-100" : "bg-emerald-100"
        }`}>
          {message.sender_type === "bot" ? (
            <Bot className="w-4 h-4 text-[#4F46E5]" />
          ) : (
            <UserCheck className="w-4 h-4 text-emerald-600" />
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-2.5 mb-4">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
        <User className="w-4 h-4 text-gray-500" />
      </div>
      <div className="relative">
        <div className="flex flex-col w-full max-w-[320px] leading-relaxed p-4 border border-gray-200 bg-gray-50 rounded-e-xl rounded-es-xl">
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-sm font-semibold text-gray-900">{senderName}</span>
            <span className="text-sm text-gray-500">{time}</span>
          </div>
          <p className="text-sm py-2 text-gray-900 whitespace-pre-wrap break-words">{message.body}</p>
        </div>
        {hasError && showError && (
          <div className="relative mt-1.5">
            <div
              onMouseEnter={() => setTooltipOpen(true)}
              onMouseLeave={() => setTooltipOpen(false)}
              onClick={() => setTooltipOpen(!tooltipOpen)}
              className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-red-500 hover:bg-red-50 transition-colors cursor-pointer"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span className="text-xs text-red-400">Falha no bot</span>
            </div>
            {tooltipOpen && (
              <div className="absolute left-0 top-full mt-2 z-50 w-[340px] bg-white border border-red-200 rounded-xl shadow-xl p-0 overflow-hidden">
                <div className="bg-red-50 px-4 py-2.5 border-b border-red-200 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-red-500" />
                    <span className="text-sm font-semibold text-red-700">Erro na resposta do bot</span>
                  </div>
                  <button onClick={() => setTooltipOpen(false)} className="p-1 hover:bg-red-100 rounded">
                    <X className="w-3.5 h-3.5 text-red-400" />
                  </button>
                </div>
                <div className="p-4 space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center">
                      <AlertTriangle className="w-4 h-4 text-red-500" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Tipo do erro</p>
                      <p className="text-sm text-gray-900 font-medium mt-0.5">{message.ai_error || "OpenAI — insufficient_quota"}</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center">
                      <Clock className="w-4 h-4 text-gray-500" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Horário da tentativa</p>
                      <p className="text-sm text-gray-900 font-medium mt-0.5">20/03/2026 08:39:12</p>
                    </div>
                  </div>
                  <div className="border-t border-gray-100 pt-3">
                    <p className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-1">Mensagem do erro</p>
                    <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                      <p className="text-xs text-gray-700 font-mono leading-relaxed">
                        You exceeded your current quota, please check your plan and billing details.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export function MessageTooltip() {
  const messages = [
    {
      direction: "outbound",
      sender_type: "bot",
      body: "A ideia é que você permaneça posicionado em PETR4 e continue capturando ganhos caso o cenário positivo se mantenha, mas com uma proteção montada para mitigar eventuais movimentos negativos.\n\nCliente 123456 - trocar 15mil que representa 4% do PL",
      created_at: "2026-03-20T06:50:00",
    },
    {
      direction: "inbound",
      sender_type: "contact",
      body: "Bom dia, não entendi, é uma estrutura?",
      created_at: "2026-03-20T06:53:00",
      ai_intent: "error_suppressed",
      ai_error: "OpenAI — insufficient_quota",
    },
  ];

  return (
    <div className="min-h-screen bg-white flex flex-col">
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
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-6 bg-gray-50/50">
        {messages.map((msg, i) => (
          <ChatBubble key={i} message={msg} contactName="Nicolas Oliveira Garcia" showError={true} />
        ))}
      </div>
    </div>
  );
}
