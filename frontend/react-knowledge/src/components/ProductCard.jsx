import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FileText, Calendar, MoreVertical, RefreshCw, Trash2 } from 'lucide-react';
import { StatusBadge } from './StatusBadge';

function getProductStatus(product) {
  if (product.status === 'archived') return 'archived';
  
  const now = new Date();
  
  const allExpired = product.materials?.length > 0 && product.materials.every(m => {
    if (m.valid_until) {
      const validUntil = new Date(m.valid_until);
      return validUntil < now;
    }
    return false;
  });
  
  if (allExpired) return 'expirado';
  
  const someExpiring = product.materials?.some(m => {
    if (m.valid_until) {
      const validUntil = new Date(m.valid_until);
      const daysUntil = (validUntil - now) / (1000 * 60 * 60 * 24);
      return daysUntil > 0 && daysUntil <= 30;
    }
    return false;
  });
  
  if (someExpiring) return 'expirando';
  return 'ativo';
}

export function ProductCard({ product, onClick, onReindex, onDelete }) {
  const status = getProductStatus(product);
  const materialsCount = product.materials_count ?? product.materials?.length ?? 0;
  const blocksCount = product.blocks_count ?? product.materials?.reduce((acc, m) => acc + (m.blocks?.length || 0), 0) ?? 0;
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    if (!menuOpen) return;
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [menuOpen]);

  const handleMenuClick = (e) => {
    e.stopPropagation();
    setMenuOpen((prev) => !prev);
  };

  const handleReindex = (e) => {
    e.stopPropagation();
    setMenuOpen(false);
    onReindex?.(product);
  };

  const handleDelete = (e) => {
    e.stopPropagation();
    setMenuOpen(false);
    onDelete?.(product);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2, boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)' }}
      onClick={() => onClick(product)}
      className="bg-card rounded-card border border-border p-5 shadow-card cursor-pointer"
    >
      <div className="flex justify-between items-start mb-3">
        <h3 className="font-semibold text-foreground text-lg flex-1 mr-2">{product.name}</h3>
        <div className="flex items-center gap-2 flex-shrink-0">
          <StatusBadge status={status} />
          {(onReindex || onDelete) && (
            <div className="relative" ref={menuRef}>
              <button
                onClick={handleMenuClick}
                className="p-1 rounded-md text-muted hover:text-foreground hover:bg-gray-100 transition-colors"
                title="Opções"
              >
                <MoreVertical className="w-4 h-4" />
              </button>
              {menuOpen && (
                <div
                  onClick={(e) => e.stopPropagation()}
                  className="absolute right-0 top-full mt-1 w-40 bg-white border border-border rounded-lg shadow-md z-50 py-1"
                >
                  {onReindex && (
                    <button
                      onClick={handleReindex}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-gray-50 transition-colors"
                    >
                      <RefreshCw className="w-4 h-4 text-muted" />
                      Reindexar
                    </button>
                  )}
                  {onDelete && (
                    <button
                      onClick={handleDelete}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                      Deletar
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      <p className="text-sm text-muted mb-3">{product.category || 'Sem categoria'}</p>
      
      {product.ticker && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs font-medium rounded">
            {product.ticker}
          </span>
        </div>
      )}
      
      <div className="flex items-center gap-4 text-sm text-muted">
        <div className="flex items-center gap-1.5">
          <FileText className="w-4 h-4" />
          <span>{materialsCount} materiais</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Calendar className="w-4 h-4" />
          <span>{blocksCount} blocos</span>
        </div>
      </div>
      
      {product.description && (
        <p className="text-sm text-muted mt-3 line-clamp-2">{product.description}</p>
      )}
    </motion.div>
  );
}
