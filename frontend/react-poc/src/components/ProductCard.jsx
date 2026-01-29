import { motion } from 'framer-motion';
import { StatusBadge } from './StatusBadge';

export function ProductCard({ product, onClick }) {
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      whileHover={{ y: -4, boxShadow: '0 4px 12px rgba(0, 0, 0, 0.12)' }}
      onClick={() => onClick(product)}
      className="bg-card rounded-card border border-border p-5 shadow-card cursor-pointer
                 transition-colors group relative overflow-hidden"
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-foreground text-base group-hover:text-primary transition-colors">
          {product.name}
        </h3>
        <StatusBadge status={product.status} size="sm" />
      </div>

      <p className="text-sm text-muted mb-3">{product.category}</p>

      <div className="flex flex-wrap gap-1.5 mb-4">
        {product.tickers.slice(0, 4).map((ticker) => (
          <span
            key={ticker}
            className="px-2 py-0.5 bg-primary/10 text-primary text-xs font-medium rounded"
          >
            {ticker}
          </span>
        ))}
        {product.tickers.length > 4 && (
          <span className="px-2 py-0.5 bg-border text-muted text-xs font-medium rounded">
            +{product.tickers.length - 4}
          </span>
        )}
      </div>

      <div className="flex items-center gap-2 mb-3">
        <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${product.confidence}%` }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className={`h-full rounded-full ${
              product.confidence >= 80
                ? 'bg-success'
                : product.confidence >= 50
                ? 'bg-warning'
                : 'bg-danger'
            }`}
          />
        </div>
        <span className="text-xs text-muted font-medium">{product.confidence}%</span>
      </div>

      <div className="flex justify-between items-center pt-3 border-t border-border">
        <span className="text-xs text-muted">
          Atualizado em {formatDate(product.updatedAt)}
        </span>
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          className="opacity-0 group-hover:opacity-100 p-1.5 rounded-full hover:bg-primary/10 text-primary transition-all"
          onClick={(e) => {
            e.stopPropagation();
            onClick(product);
          }}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </motion.button>
      </div>

      <div className="absolute inset-x-0 bottom-0 h-0.5 bg-primary scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
    </motion.div>
  );
}
