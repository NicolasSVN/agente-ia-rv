import { motion } from 'framer-motion';
import InfoTooltip from './InfoTooltip';

export default function CampaignsSummary({ totalCampaigns, assessorsReached }) {
  return (
    <div className="bg-white rounded-xl border border-border p-5 shadow-card">
      <div className="flex items-center mb-4">
        <h3 className="text-base font-semibold text-foreground">Resumo das Campanhas</h3>
        <InfoTooltip text="Totais de campanhas de comunicação ativa disparadas e assessores alcançados no período selecionado." />
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-5 border border-blue-200"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
              </svg>
            </div>
            <span className="text-sm font-medium text-blue-700">Total de Campanhas</span>
          </div>
          <p className="text-3xl font-bold text-blue-900">{totalCampaigns || 0}</p>
          <p className="text-xs text-blue-600 mt-1">Campanhas disparadas</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-5 border border-green-200"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <span className="text-sm font-medium text-green-700">Assessores Alcançados</span>
          </div>
          <p className="text-3xl font-bold text-green-900">{assessorsReached || 0}</p>
          <p className="text-xs text-green-600 mt-1">Assessores que receberam mensagens</p>
        </motion.div>
      </div>
    </div>
  );
}
