import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function FilterBar({ filters, onFilterChange, filterOptions }) {
  const [showMore, setShowMore] = useState(false);
  const [showCustomDates, setShowCustomDates] = useState(filters.period === 'custom');

  useEffect(() => {
    setShowCustomDates(filters.period === 'custom');
  }, [filters.period]);

  const periods = [
    { value: '7d', label: '7 dias' },
    { value: '30d', label: '30 dias' },
    { value: '90d', label: '90 dias' },
    { value: '365d', label: '1 ano' },
  ];

  const handlePeriodChange = (value) => {
    if (value === 'custom') {
      setShowCustomDates(true);
      onFilterChange({ ...filters, period: value });
    } else {
      setShowCustomDates(false);
      onFilterChange({ ...filters, period: value, start_date: null, end_date: null });
    }
  };

  const hasActiveFilters = filters.macro_area || filters.unidade || filters.broker || filters.equipe;

  return (
    <div className="bg-white rounded-xl border border-border p-5 shadow-card mb-6">
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-1">
          <span className="text-sm font-medium text-foreground mr-2">Período:</span>
          <div className="flex items-center bg-gray-100 rounded-lg p-1">
            {periods.map((p) => (
              <button
                key={p.value}
                onClick={() => handlePeriodChange(p.value)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                  filters.period === p.value && !showCustomDates
                    ? 'bg-primary text-white shadow-sm'
                    : 'text-muted hover:text-foreground'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className="h-6 w-px bg-border" />

        <button
          onClick={() => handlePeriodChange('custom')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all border ${
            showCustomDates
              ? 'bg-primary text-white border-primary'
              : 'bg-white text-muted border-border hover:border-primary hover:text-primary'
          }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          Personalizado
        </button>

        <AnimatePresence>
          {showCustomDates && (
            <>
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="flex items-center gap-2"
              >
                <input
                  type="date"
                  value={filters.start_date || ''}
                  onChange={(e) => onFilterChange({ ...filters, start_date: e.target.value })}
                  className="px-3 py-1.5 bg-white border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
                <span className="text-muted">até</span>
                <input
                  type="date"
                  value={filters.end_date || ''}
                  onChange={(e) => onFilterChange({ ...filters, end_date: e.target.value })}
                  className="px-3 py-1.5 bg-white border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </motion.div>
            </>
          )}
        </AnimatePresence>

        <div className="flex-1" />

        <button
          onClick={() => setShowMore(!showMore)}
          className={`flex items-center gap-2 px-4 py-2 border rounded-lg text-sm font-medium transition-colors ${
            showMore || hasActiveFilters
              ? 'bg-primary text-white border-primary'
              : 'bg-white text-muted border-border hover:bg-gray-50'
          }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Mais Filtros
          {hasActiveFilters && (
            <span className="w-2 h-2 bg-white rounded-full" />
          )}
          <svg className={`w-4 h-4 transition-transform ${showMore ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      <AnimatePresence>
        {showMore && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 pt-4 border-t border-border overflow-hidden"
          >
            <div className="flex flex-wrap gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-muted uppercase">Macro Área</label>
                <select
                  value={filters.macro_area || ''}
                  onChange={(e) => onFilterChange({ ...filters, macro_area: e.target.value || null })}
                  className="px-3 py-2.5 bg-white border border-border rounded-lg text-sm min-w-[160px] focus:outline-none focus:ring-2 focus:ring-primary/20"
                >
                  <option value="">Todas</option>
                  {filterOptions?.macro_areas?.map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-muted uppercase">Unidade</label>
                <select
                  value={filters.unidade || ''}
                  onChange={(e) => onFilterChange({ ...filters, unidade: e.target.value || null })}
                  className="px-3 py-2.5 bg-white border border-border rounded-lg text-sm min-w-[160px] focus:outline-none focus:ring-2 focus:ring-primary/20"
                >
                  <option value="">Todas</option>
                  {filterOptions?.unidades?.map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-muted uppercase">Broker</label>
                <select
                  value={filters.broker || ''}
                  onChange={(e) => onFilterChange({ ...filters, broker: e.target.value || null })}
                  className="px-3 py-2.5 bg-white border border-border rounded-lg text-sm min-w-[160px] focus:outline-none focus:ring-2 focus:ring-primary/20"
                >
                  <option value="">Todos</option>
                  {filterOptions?.brokers?.map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-muted uppercase">Equipe</label>
                <select
                  value={filters.equipe || ''}
                  onChange={(e) => onFilterChange({ ...filters, equipe: e.target.value || null })}
                  className="px-3 py-2.5 bg-white border border-border rounded-lg text-sm min-w-[160px] focus:outline-none focus:ring-2 focus:ring-primary/20"
                >
                  <option value="">Todas</option>
                  {filterOptions?.equipes?.map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              </div>

              {hasActiveFilters && (
                <button
                  onClick={() => onFilterChange({
                    ...filters,
                    macro_area: null,
                    unidade: null,
                    broker: null,
                    equipe: null
                  })}
                  className="self-end px-3 py-2.5 text-sm text-danger hover:bg-danger/10 rounded-lg transition-colors"
                >
                  Limpar filtros
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
