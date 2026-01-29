import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Filter, RefreshCw, Package } from 'lucide-react';
import { productsAPI } from '../services/api';
import { ProductCard } from '../components/ProductCard';
import { SearchInput } from '../components/SearchInput';
import { Button } from '../components/Button';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { Modal } from '../components/Modal';
import { useToast } from '../components/Toast';

export function Dashboard() {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [showNewModal, setShowNewModal] = useState(false);
  const [newProduct, setNewProduct] = useState({ name: '', ticker: '', category: '' });
  const [creating, setCreating] = useState(false);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const data = await productsAPI.list();
      setProducts(data.products || data);
    } catch (err) {
      addToast('Erro ao carregar produtos', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await productsAPI.getCategories();
      setCategories(data.categories || []);
    } catch (err) {
      console.error('Erro ao carregar categorias:', err);
    }
  };

  useEffect(() => {
    loadProducts();
    loadCategories();
  }, []);

  const filteredProducts = useMemo(() => {
    return products.filter((product) => {
      const matchesSearch = search === '' ||
        product.name?.toLowerCase().includes(search.toLowerCase()) ||
        product.ticker?.toLowerCase().includes(search.toLowerCase());
      
      const matchesCategory = selectedCategory === '' ||
        product.category === selectedCategory;

      return matchesSearch && matchesCategory;
    });
  }, [products, search, selectedCategory]);

  const handleCreateProduct = async (e) => {
    e.preventDefault();
    if (!newProduct.name.trim()) {
      addToast('Nome do produto é obrigatório', 'warning');
      return;
    }

    setCreating(true);
    try {
      const created = await productsAPI.create(newProduct);
      addToast('Produto criado com sucesso!', 'success');
      setShowNewModal(false);
      setNewProduct({ name: '', ticker: '', category: '' });
      navigate(`/product/${created.id}`);
    } catch (err) {
      addToast(`Erro: ${err.message}`, 'error');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Produtos</h1>
          <p className="text-muted">Gerencie a base de conhecimento dos produtos</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={loadProducts} disabled={loading}>
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
          <Button onClick={() => setShowNewModal(true)}>
            <Plus className="w-4 h-4" />
            Novo Produto
          </Button>
        </div>
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Buscar por nome ou ticker..."
          />
        </div>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-4 py-2 bg-card border border-border rounded-input text-foreground
                     focus:outline-none focus:ring-2 focus:ring-primary/20"
        >
          <option value="">Todas categorias</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="py-20">
          <LoadingSpinner size="lg" />
        </div>
      ) : filteredProducts.length === 0 ? (
        <EmptyState
          icon={Package}
          title="Nenhum produto encontrado"
          description={search || selectedCategory
            ? "Tente ajustar os filtros de busca"
            : "Comece criando um novo produto para sua base de conhecimento"
          }
          action={() => setShowNewModal(true)}
          actionLabel="Criar Produto"
        />
      ) : (
        <>
          <p className="text-sm text-muted">
            {filteredProducts.length} produto{filteredProducts.length !== 1 ? 's' : ''} encontrado{filteredProducts.length !== 1 ? 's' : ''}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <AnimatePresence>
              {filteredProducts.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onClick={(p) => navigate(`/product/${p.id}`)}
                />
              ))}
            </AnimatePresence>
          </div>
        </>
      )}

      <Modal
        open={showNewModal}
        onClose={() => setShowNewModal(false)}
        title="Novo Produto"
      >
        <form onSubmit={handleCreateProduct} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              Nome do Produto *
            </label>
            <input
              type="text"
              value={newProduct.name}
              onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
              placeholder="Ex: Fundo XPTO"
              className="w-full px-3 py-2 bg-card border border-border rounded-input
                        text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              Ticker
            </label>
            <input
              type="text"
              value={newProduct.ticker}
              onChange={(e) => setNewProduct({ ...newProduct, ticker: e.target.value.toUpperCase() })}
              placeholder="Ex: XPTO11"
              className="w-full px-3 py-2 bg-card border border-border rounded-input
                        text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              Categoria
            </label>
            <select
              value={newProduct.category}
              onChange={(e) => setNewProduct({ ...newProduct, category: e.target.value })}
              className="w-full px-3 py-2 bg-card border border-border rounded-input
                        text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="">Selecione...</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowNewModal(false)}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              loading={creating}
              className="flex-1"
            >
              Criar Produto
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
