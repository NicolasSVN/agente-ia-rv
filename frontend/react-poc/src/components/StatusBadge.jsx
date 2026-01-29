import { motion } from 'framer-motion';

const statusConfig = {
  ativo: {
    bg: 'bg-success-light',
    text: 'text-success',
    dot: 'bg-success',
    label: 'Ativo',
  },
  expirando: {
    bg: 'bg-warning-light',
    text: 'text-warning',
    dot: 'bg-warning',
    label: 'Expirando',
  },
  expirado: {
    bg: 'bg-danger-light',
    text: 'text-danger',
    dot: 'bg-danger',
    label: 'Expirado',
  },
  rascunho: {
    bg: 'bg-gray-100',
    text: 'text-muted',
    dot: 'bg-muted',
    label: 'Rascunho',
  },
};

export function StatusBadge({ status, size = 'md' }) {
  const config = statusConfig[status] || statusConfig.rascunho;
  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1';

  return (
    <motion.span
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${config.bg} ${config.text} ${sizeClasses}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </motion.span>
  );
}
