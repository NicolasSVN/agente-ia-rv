import { motion } from 'framer-motion';

const statusConfig = {
  ativo: { bg: 'bg-success/10', text: 'text-success', dot: 'bg-success', label: 'Ativo' },
  published: { bg: 'bg-success/10', text: 'text-success', dot: 'bg-success', label: 'Publicado' },
  draft: { bg: 'bg-muted/10', text: 'text-muted', dot: 'bg-muted', label: 'Rascunho' },
  expirando: { bg: 'bg-warning/10', text: 'text-warning', dot: 'bg-warning', label: 'Expirando' },
  expirado: { bg: 'bg-danger/10', text: 'text-danger', dot: 'bg-danger', label: 'Expirado' },
  archived: { bg: 'bg-muted/10', text: 'text-muted', dot: 'bg-muted', label: 'Arquivado' },
  pending_review: { bg: 'bg-warning/10', text: 'text-warning', dot: 'bg-warning', label: 'Pendente' },
  approved: { bg: 'bg-success/10', text: 'text-success', dot: 'bg-success', label: 'Aprovado' },
  rejected: { bg: 'bg-danger/10', text: 'text-danger', dot: 'bg-danger', label: 'Rejeitado' },
  processing: { bg: 'bg-info/10', text: 'text-info', dot: 'bg-info', label: 'Processando' },
};

export function StatusBadge({ status, size = 'sm' }) {
  const config = statusConfig[status] || statusConfig.draft;
  
  const sizeClasses = size === 'sm' 
    ? 'px-2 py-0.5 text-xs' 
    : 'px-3 py-1 text-sm';

  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`inline-flex items-center gap-1.5 ${sizeClasses} rounded-full font-medium ${config.bg} ${config.text}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </motion.span>
  );
}
