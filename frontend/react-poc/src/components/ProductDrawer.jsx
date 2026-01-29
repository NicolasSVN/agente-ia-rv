import * as Dialog from '@radix-ui/react-dialog';
import { motion, AnimatePresence } from 'framer-motion';
import { StatusBadge } from './StatusBadge';
import { InlineEditField } from './InlineEditField';

export function ProductDrawer({ product, open, onClose, onUpdate }) {
  if (!product) return null;

  const handleFieldSave = async (field, value) => {
    await new Promise((resolve) => setTimeout(resolve, 800));
    onUpdate(product.id, { [field]: value });
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Dialog.Root open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <AnimatePresence>
        {open && (
          <Dialog.Portal forceMount>
            <Dialog.Overlay asChild>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/40 z-40"
              />
            </Dialog.Overlay>
            <Dialog.Content asChild>
              <motion.div
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '100%' }}
                transition={{ type: 'spring', damping: 30, stiffness: 300 }}
                className="fixed top-0 right-0 h-full w-full max-w-lg bg-card shadow-modal z-50
                           flex flex-col overflow-hidden"
              >
                <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-background">
                  <div>
                    <Dialog.Title className="font-semibold text-lg text-foreground">
                      {product.name}
                    </Dialog.Title>
                    <p className="text-sm text-muted">{product.category}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={product.status} />
                    <Dialog.Close asChild>
                      <button
                        className="p-2 rounded-full hover:bg-border text-muted hover:text-foreground transition-colors"
                        aria-label="Fechar"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </Dialog.Close>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  <section>
                    <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                      <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Resumo
                    </h3>
                    <div className="bg-background rounded-card p-4 space-y-3">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted">Última atualização</span>
                        <span className="text-foreground">{formatDate(product.updatedAt)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted">Confiança</span>
                        <span className={`font-medium ${
                          product.confidence >= 80 ? 'text-success' :
                          product.confidence >= 50 ? 'text-warning' : 'text-danger'
                        }`}>
                          {product.confidence}%
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-1.5 pt-2">
                        {product.tickers.map((ticker) => (
                          <span
                            key={ticker}
                            className="px-2 py-0.5 bg-primary/10 text-primary text-xs font-medium rounded"
                          >
                            {ticker}
                          </span>
                        ))}
                      </div>
                    </div>
                  </section>

                  <section>
                    <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                      <svg className="w-4 h-4 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Taxa Principal
                    </h3>
                    <div className="bg-background rounded-card p-4">
                      <InlineEditField
                        label="Taxa de Administração"
                        value={product.rate || ''}
                        onSave={(value) => handleFieldSave('rate', value)}
                        placeholder="Ex: 1.0% a.a."
                      />
                    </div>
                  </section>

                  <section>
                    <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                      <svg className="w-4 h-4 text-info" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      One-Page
                    </h3>
                    <div className="bg-background rounded-card p-4">
                      <InlineEditField
                        label="Descrição do Produto"
                        value={product.onePage || ''}
                        onSave={(value) => handleFieldSave('onePage', value)}
                        multiline
                        placeholder="Descrição resumida do produto para uso comercial..."
                      />
                    </div>
                  </section>

                  <section>
                    <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                      <svg className="w-4 h-4 text-svn-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      Script WhatsApp
                    </h3>
                    <div className="bg-background rounded-card p-4">
                      <InlineEditField
                        label="Mensagem para Clientes"
                        value={product.whatsappScript || ''}
                        onSave={(value) => handleFieldSave('whatsappScript', value)}
                        multiline
                        placeholder="Olá! Gostaria de apresentar o produto..."
                      />
                    </div>
                  </section>

                  <section>
                    <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                      <svg className="w-4 h-4 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                      </svg>
                      Materiais Anexos
                    </h3>
                    <div className="bg-background rounded-card p-4">
                      {product.materials && product.materials.length > 0 ? (
                        <ul className="space-y-2">
                          {product.materials.map((material, idx) => (
                            <li key={idx} className="flex items-center gap-2 text-sm">
                              <svg className="w-4 h-4 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                              </svg>
                              <span className="text-foreground">{material.name}</span>
                              <span className={`text-xs px-1.5 py-0.5 rounded ${
                                material.status === 'atualizado' ? 'bg-success-light text-success' :
                                material.status === 'pendente' ? 'bg-warning-light text-warning' :
                                'bg-danger-light text-danger'
                              }`}>
                                {material.status}
                              </span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-sm text-muted italic">Nenhum material anexado</p>
                      )}
                    </div>
                  </section>
                </div>
              </motion.div>
            </Dialog.Content>
          </Dialog.Portal>
        )}
      </AnimatePresence>
    </Dialog.Root>
  );
}
