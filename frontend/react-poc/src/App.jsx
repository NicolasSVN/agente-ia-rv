import { useState, useMemo, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { SearchBar } from './components/SearchBar';
import { FilterSelect } from './components/FilterSelect';
import { ProductCard } from './components/ProductCard';
import { ProductDrawer } from './components/ProductDrawer';
import { ProductCardSkeleton } from './components/SkeletonLoader';
import { Button } from './components/Button';
import { mockProducts, categories, statuses, allTickers } from './data/mockProducts';

function App() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [tickerFilter, setTickerFilter] = useState('');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setProducts(mockProducts);
      setLoading(false);
    }, 1200);
    return () => clearTimeout(timer);
  }, []);

  const filteredProducts = useMemo(() => {
    return products.filter((product) => {
      const matchesSearch = search === '' ||
        product.name.toLowerCase().includes(search.toLowerCase()) ||
        product.tickers.some(t => t.toLowerCase().includes(search.toLowerCase()));

      const matchesCategory = categoryFilter === '' ||
        product.category.toLowerCase().replace(/\s+/g, '-') === categoryFilter;

      const matchesStatus = statusFilter === '' ||
        product.status === statusFilter;

      const matchesTicker = tickerFilter === '' ||
        product.tickers.includes(tickerFilter);

      return matchesSearch && matchesCategory && matchesStatus && matchesTicker;
    });
  }, [products, search, categoryFilter, statusFilter, tickerFilter]);

  const handleProductClick = (product) => {
    setSelectedProduct(product);
    setDrawerOpen(true);
  };

  const handleProductUpdate = (productId, updates) => {
    setProducts((prev) =>
      prev.map((p) =>
        p.id === productId
          ? { ...p, ...updates, updatedAt: new Date().toISOString() }
          : p
      )
    );
    if (selectedProduct?.id === productId) {
      setSelectedProduct((prev) => ({ ...prev, ...updates }));
    }
  };

  const clearFilters = () => {
    setSearch('');
    setCategoryFilter('');
    setStatusFilter('');
    setTickerFilter('');
  };

  const hasActiveFilters = search || categoryFilter || statusFilter || tickerFilter;

  const tickerOptions = allTickers.map(t => ({ value: t, label: t }));

  return (
    <div className="min-h-screen bg-background">
      <header className="bg-card border-b border-border sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-xl font-bold text-foreground">Base de Conhecimento</h1>
              <p className="text-sm text-muted">UX Test - React + Tailwind</p>
            </div>
            <Button>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Novo Produto
            </Button>
          </div>

          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 max-w-md">
              <SearchBar
                value={search}
                onChange={setSearch}
                placeholder="Buscar por nome ou ticker..."
              />
            </div>
            <div className="flex flex-wrap gap-3">
              <FilterSelect
                label="Categoria"
                value={categoryFilter}
                onChange={setCategoryFilter}
                options={categories}
                placeholder="Todas"
              />
              <FilterSelect
                label="Status"
                value={statusFilter}
                onChange={setStatusFilter}
                options={statuses}
                placeholder="Todos"
              />
              <FilterSelect
                label="Ticker"
                value={tickerFilter}
                onChange={setTickerFilter}
                options={tickerOptions}
                placeholder="Todos"
              />
              {hasActiveFilters && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex items-end"
                >
                  <Button variant="ghost" size="sm" onClick={clearFilters}>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    Limpar filtros
                  </Button>
                </motion.div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <p className="text-sm text-muted">
            {loading ? (
              'Carregando produtos...'
            ) : (
              <>
                <span className="font-medium text-foreground">{filteredProducts.length}</span>
                {' '}produto{filteredProducts.length !== 1 ? 's' : ''} encontrado{filteredProducts.length !== 1 ? 's' : ''}
              </>
            )}
          </p>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <ProductCardSkeleton key={i} />
            ))}
          </div>
        ) : filteredProducts.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-16"
          >
            <svg className="w-16 h-16 text-border mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-lg font-medium text-foreground mb-2">Nenhum produto encontrado</h3>
            <p className="text-muted mb-4">Tente ajustar os filtros ou a busca</p>
            <Button variant="secondary" onClick={clearFilters}>Limpar filtros</Button>
          </motion.div>
        ) : (
          <motion.div
            layout
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            <AnimatePresence mode="popLayout">
              {filteredProducts.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onClick={handleProductClick}
                />
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </main>

      <ProductDrawer
        product={selectedProduct}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onUpdate={handleProductUpdate}
      />
    </div>
  );
}

export default App;
