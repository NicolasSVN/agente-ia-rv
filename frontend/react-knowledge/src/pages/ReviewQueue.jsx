import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ClipboardCheck, Check, X, Edit, AlertTriangle, RefreshCw, Table2, Search, FileText, Maximize2 } from 'lucide-react';
import { reviewAPI } from '../services/api';
import { Button } from '../components/Button';
import { Modal } from '../components/Modal';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { useToast } from '../components/Toast';

const API_BASE = '/api/products';

function convertTableToTopics(content) {
  if (!content) return null;
  
  try {
    let parsed = content;
    if (typeof content === 'string') {
      parsed = JSON.parse(content);
    }
    
    if (parsed && parsed.headers && Array.isArray(parsed.headers) && parsed.rows && Array.isArray(parsed.rows)) {
      const topics = [];
      const headers = parsed.headers;
      
      parsed.rows.forEach((row, rowIdx) => {
        const rowTopics = [];
        row.forEach((cell, cellIdx) => {
          if (cell && cell.toString().trim()) {
            const header = headers[cellIdx] || `Campo ${cellIdx + 1}`;
            rowTopics.push(`${header}: ${cell}`);
          }
        });
        if (rowTopics.length > 0) {
          topics.push(rowTopics.join(' | '));
        }
      });
      
      return topics.join('\n');
    }
  } catch (e) {
  }
  return null;
}

function TopicsPreview({ content, maxLines = 4 }) {
  const lines = content.split('\n').slice(0, maxLines);
  const hasMore = content.split('\n').length > maxLines;
  
  return (
    <div className="space-y-1">
      {lines.map((line, i) => (
        <div key={i} className="flex items-start gap-2 text-sm text-muted">
          <span className="text-primary mt-0.5">•</span>
          <span className="line-clamp-1">{line}</span>
        </div>
      ))}
      {hasMore && (
        <p className="text-xs text-muted/70 italic pl-4">
          + {content.split('\n').length - maxLines} itens adicionais...
        </p>
      )}
    </div>
  );
}

function ContentPreview({ content, blockType }) {
  const topicsContent = useMemo(() => {
    if (blockType === 'tabela' || blockType === 'table') {
      return convertTableToTopics(content);
    }
    return null;
  }, [content, blockType]);

  if (topicsContent) {
    return (
      <div className="mb-3">
        <div className="flex items-center gap-1.5 text-xs text-muted mb-2">
          <Table2 className="w-3.5 h-3.5" />
          <span>Dados extraídos</span>
        </div>
        <TopicsPreview content={topicsContent} maxLines={4} />
      </div>
    );
  }

  return (
    <p className="text-sm text-muted mb-3 whitespace-pre-wrap line-clamp-4">
      {content}
    </p>
  );
}

function PDFViewer({ materialId, page = 1 }) {
  const containerRef = useRef(null);
  const [showMagnifier, setShowMagnifier] = useState(false);
  const [magnifierPos, setMagnifierPos] = useState({ x: 0, y: 0 });
  const [error, setError] = useState(false);
  
  const pdfUrl = materialId ? `${API_BASE}/materials/${materialId}/pdf#page=${page}` : null;
  const magnifierSize = 150;
  const zoomLevel = 2.5;
  
  const handleMouseMove = useCallback((e) => {
    const container = containerRef.current;
    if (!container) return;
    
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setMagnifierPos({ x, y });
  }, []);
  
  if (!materialId) {
    return (
      <div className="flex items-center justify-center h-full bg-muted/5 rounded-lg border border-border">
        <div className="text-center text-muted">
          <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p className="text-sm">PDF não disponível</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 bg-muted/10 border-b border-border rounded-t-lg">
        <span className="text-xs font-medium text-muted">Documento Original</span>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-xs text-muted">
            <Search className="w-3.5 h-3.5" />
            <span>Lupa ativa</span>
          </div>
          <a
            href={`${API_BASE}/materials/${materialId}/pdf`}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1 hover:bg-muted/20 rounded transition-colors"
            title="Abrir em nova aba"
          >
            <Maximize2 className="w-4 h-4 text-muted" />
          </a>
        </div>
      </div>
      <div 
        ref={containerRef}
        className="flex-1 overflow-auto bg-muted/5 rounded-b-lg relative cursor-crosshair"
        onMouseEnter={() => setShowMagnifier(true)}
        onMouseLeave={() => setShowMagnifier(false)}
        onMouseMove={handleMouseMove}
      >
        {error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-muted">
              <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Não foi possível carregar o PDF</p>
            </div>
          </div>
        ) : (
          <>
            <iframe
              src={pdfUrl}
              className="w-full h-full border-0 pointer-events-none"
              onError={() => setError(true)}
              title="PDF Preview"
            />
            {showMagnifier && (
              <div
                className="absolute pointer-events-none border-2 border-primary rounded-full shadow-lg overflow-hidden bg-white"
                style={{
                  width: magnifierSize,
                  height: magnifierSize,
                  left: magnifierPos.x - magnifierSize / 2,
                  top: magnifierPos.y - magnifierSize / 2,
                  zIndex: 10
                }}
              >
                <iframe
                  src={pdfUrl}
                  className="border-0 pointer-events-none"
                  style={{
                    width: containerRef.current?.clientWidth || 400,
                    height: containerRef.current?.clientHeight || 600,
                    transform: `scale(${zoomLevel})`,
                    transformOrigin: `${magnifierPos.x}px ${magnifierPos.y}px`,
                    position: 'absolute',
                    left: -(magnifierPos.x * zoomLevel - magnifierSize / 2),
                    top: -(magnifierPos.y * zoomLevel - magnifierSize / 2)
                  }}
                  title="PDF Magnifier"
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export function ReviewQueue() {
  const { addToast } = useToast();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);
  const [editContent, setEditContent] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [showEditModal, setShowEditModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [processing, setProcessing] = useState(false);

  const loadItems = async () => {
    try {
      setLoading(true);
      const data = await reviewAPI.listPending();
      setItems(data.pending_items || data.items || data || []);
    } catch (err) {
      addToast('Erro ao carregar itens pendentes', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadItems();
  }, []);

  const handleApprove = async (item) => {
    setProcessing(true);
    try {
      await reviewAPI.approve(item.id);
      addToast('Item aprovado com sucesso!', 'success');
      setItems((prev) => prev.filter((i) => i.id !== item.id));
    } catch (err) {
      addToast(`Erro: ${err.message}`, 'error');
    }
    setProcessing(false);
  };

  const handleEdit = async () => {
    if (!editContent.trim()) {
      addToast('Conteúdo não pode estar vazio', 'warning');
      return;
    }

    setProcessing(true);
    try {
      await reviewAPI.edit(selectedItem.id, { content: editContent });
      addToast('Item editado e aprovado!', 'success');
      setItems((prev) => prev.filter((i) => i.id !== selectedItem.id));
      setShowEditModal(false);
      setSelectedItem(null);
    } catch (err) {
      addToast(`Erro: ${err.message}`, 'error');
    }
    setProcessing(false);
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      addToast('Motivo da rejeição é obrigatório', 'warning');
      return;
    }

    setProcessing(true);
    try {
      await reviewAPI.reject(selectedItem.id, { reason: rejectReason });
      addToast('Item rejeitado', 'success');
      setItems((prev) => prev.filter((i) => i.id !== selectedItem.id));
      setShowRejectModal(false);
      setSelectedItem(null);
      setRejectReason('');
    } catch (err) {
      addToast(`Erro: ${err.message}`, 'error');
    }
    setProcessing(false);
  };

  const openEditModal = (item) => {
    setSelectedItem(item);
    const content = item.extracted_content || item.content || '';
    
    if (item.block_type === 'tabela' || item.block_type === 'table') {
      const topicsContent = convertTableToTopics(content);
      setEditContent(topicsContent || content);
    } else {
      setEditContent(content);
    }
    
    setShowEditModal(true);
  };

  const openRejectModal = (item) => {
    setSelectedItem(item);
    setShowRejectModal(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Fila de Revisão</h1>
          <p className="text-muted">
            Itens que requerem revisão manual antes de serem publicados
          </p>
        </div>
        <Button variant="secondary" onClick={loadItems} disabled={loading}>
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Atualizar
        </Button>
      </div>

      {loading ? (
        <div className="py-20">
          <LoadingSpinner size="lg" />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={ClipboardCheck}
          title="Nenhum item pendente"
          description="Todos os itens foram revisados. Volte mais tarde para verificar novos itens."
        />
      ) : (
        <>
          <p className="text-sm text-muted">
            {items.length} item{items.length !== 1 ? 's' : ''} aguardando revisão
          </p>

          <div className="space-y-4">
            <AnimatePresence>
              {items.map((item) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -100 }}
                  className="bg-card rounded-card border border-warning/30 p-5 shadow-card"
                >
                  <div className="flex items-start gap-4">
                    <div className="p-2 bg-warning/10 rounded-full">
                      <AlertTriangle className="w-5 h-5 text-warning" />
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs px-2 py-0.5 bg-muted/10 text-muted rounded font-medium">
                          {item.block_type || 'texto'}
                        </span>
                        {item.product_name && (
                          <span className="text-xs text-primary font-medium">
                            {item.product_name}
                          </span>
                        )}
                      </div>

                      {(item.block_title || item.title) && (
                        <h3 className="font-medium text-foreground mb-2">{item.block_title || item.title}</h3>
                      )}

                      <ContentPreview 
                        content={item.extracted_content || item.content} 
                        blockType={item.block_type}
                      />

                      {(item.risk_reason || item.reason) && (
                        <div className="flex items-center gap-2 text-sm text-warning mb-3">
                          <AlertTriangle className="w-4 h-4" />
                          Motivo: {item.risk_reason || item.reason}
                        </div>
                      )}

                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="success"
                          onClick={() => handleApprove(item)}
                          disabled={processing}
                        >
                          <Check className="w-4 h-4" />
                          Aprovar
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => openEditModal(item)}
                          disabled={processing}
                        >
                          <Edit className="w-4 h-4" />
                          Editar e Aprovar
                        </Button>
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() => openRejectModal(item)}
                          disabled={processing}
                        >
                          <X className="w-4 h-4" />
                          Rejeitar
                        </Button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </>
      )}

      <Modal
        open={showEditModal}
        onClose={() => setShowEditModal(false)}
        title={
          <div className="flex items-center gap-3">
            <span>Editar e Aprovar</span>
            {selectedItem && (
              <>
                <span className="text-xs px-2 py-0.5 bg-muted/10 text-muted rounded">
                  {selectedItem.block_type || 'texto'}
                </span>
                {selectedItem.product_name && (
                  <span className="text-xs text-primary font-medium">
                    {selectedItem.product_name}
                  </span>
                )}
                {selectedItem.source_page && (
                  <span className="text-xs text-muted">
                    Página {selectedItem.source_page}
                  </span>
                )}
              </>
            )}
          </div>
        }
        size="xl"
      >
        <div className="flex gap-4 h-[70vh]">
          <div className="w-1/2 flex flex-col">
            <PDFViewer 
              materialId={selectedItem?.material_id} 
              page={selectedItem?.source_page || 1}
            />
          </div>
          
          <div className="w-1/2 flex flex-col">
            <div className="flex items-center justify-between px-3 py-2 bg-muted/10 border-b border-border rounded-t-lg">
              <span className="text-xs font-medium text-muted">Conteúdo Extraído</span>
              {selectedItem?.block_type === 'tabela' && (
                <span className="text-xs text-muted">Convertido em tópicos</span>
              )}
            </div>
            
            <div className="flex-1 overflow-auto p-3 bg-card border border-t-0 border-border rounded-b-lg">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full h-full px-3 py-2 bg-transparent border-0
                           text-foreground text-sm resize-none focus:outline-none"
                placeholder="Conteúdo do bloco..."
              />
            </div>
            
            {selectedItem?.risk_reason && (
              <div className="flex items-center gap-2 text-sm text-warning mt-3 px-1">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>Motivo: {selectedItem.risk_reason}</span>
              </div>
            )}
            
            <div className="flex gap-3 mt-4">
              <Button
                variant="secondary"
                onClick={() => setShowEditModal(false)}
                className="flex-1"
              >
                Cancelar
              </Button>
              <Button
                variant="success"
                onClick={handleEdit}
                loading={processing}
                className="flex-1"
              >
                Salvar e Aprovar
              </Button>
            </div>
          </div>
        </div>
      </Modal>

      <Modal
        open={showRejectModal}
        onClose={() => setShowRejectModal(false)}
        title="Rejeitar Item"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-sm text-muted">
            Informe o motivo da rejeição:
          </p>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={4}
            placeholder="Ex: Informação desatualizada, dados incorretos..."
            className="w-full px-3 py-2 bg-card border border-border rounded-input
                       text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
          <div className="flex gap-3">
            <Button
              variant="secondary"
              onClick={() => setShowRejectModal(false)}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button
              variant="danger"
              onClick={handleReject}
              loading={processing}
              className="flex-1"
            >
              Confirmar Rejeição
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
