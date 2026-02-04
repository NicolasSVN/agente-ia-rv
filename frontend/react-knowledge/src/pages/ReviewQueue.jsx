import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ClipboardCheck, Check, X, Edit, AlertTriangle, RefreshCw, Table2, ZoomIn, ZoomOut, FileText, Maximize2 } from 'lucide-react';
import { reviewAPI } from '../services/api';
import { Button } from '../components/Button';
import { Modal } from '../components/Modal';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { useToast } from '../components/Toast';

const API_BASE = '/api/products';

function parseTableContent(content) {
  if (!content) return null;
  
  try {
    let parsed = content;
    if (typeof content === 'string') {
      parsed = JSON.parse(content);
    }
    
    if (parsed && parsed.headers && Array.isArray(parsed.headers) && parsed.rows && Array.isArray(parsed.rows)) {
      return parsed;
    }
  } catch (e) {
  }
  return null;
}

function TablePreview({ data, maxRows = 3 }) {
  const headers = data.headers || [];
  const rows = data.rows || [];
  const displayRows = rows.slice(0, maxRows);
  const hasMore = rows.length > maxRows;
  
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-xs border-collapse">
        <thead>
          <tr className="bg-muted/10">
            {headers.map((h, i) => (
              <th key={i} className="px-2 py-1.5 text-left font-medium text-foreground border border-border/50 whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayRows.map((row, rowIdx) => (
            <tr key={rowIdx} className={rowIdx % 2 === 0 ? 'bg-card' : 'bg-muted/5'}>
              {row.map((cell, cellIdx) => (
                <td key={cellIdx} className="px-2 py-1 text-muted border border-border/50 whitespace-nowrap max-w-[200px] truncate">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {hasMore && (
        <p className="text-xs text-muted mt-1 italic">
          + {rows.length - maxRows} linhas adicionais...
        </p>
      )}
    </div>
  );
}

function ContentPreview({ content, blockType }) {
  const tableData = useMemo(() => {
    if (blockType === 'tabela' || blockType === 'table') {
      return parseTableContent(content);
    }
    return null;
  }, [content, blockType]);

  if (tableData) {
    return (
      <div className="mb-3">
        <div className="flex items-center gap-1.5 text-xs text-muted mb-2">
          <Table2 className="w-3.5 h-3.5" />
          <span>{tableData.headers?.length || 0} colunas · {tableData.rows?.length || 0} linhas</span>
        </div>
        <TablePreview data={tableData} maxRows={3} />
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
  const [zoom, setZoom] = useState(100);
  const [error, setError] = useState(false);
  
  const pdfUrl = materialId ? `${API_BASE}/materials/${materialId}/pdf#page=${page}` : null;
  
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
        <div className="flex items-center gap-1">
          <button
            onClick={() => setZoom(Math.max(50, zoom - 25))}
            className="p-1 hover:bg-muted/20 rounded transition-colors"
            title="Diminuir zoom"
          >
            <ZoomOut className="w-4 h-4 text-muted" />
          </button>
          <span className="text-xs text-muted px-2 min-w-[3rem] text-center">{zoom}%</span>
          <button
            onClick={() => setZoom(Math.min(200, zoom + 25))}
            className="p-1 hover:bg-muted/20 rounded transition-colors"
            title="Aumentar zoom"
          >
            <ZoomIn className="w-4 h-4 text-muted" />
          </button>
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1 hover:bg-muted/20 rounded transition-colors ml-2"
            title="Abrir em nova aba"
          >
            <Maximize2 className="w-4 h-4 text-muted" />
          </a>
        </div>
      </div>
      <div className="flex-1 overflow-auto bg-muted/5 rounded-b-lg">
        {error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-muted">
              <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Não foi possível carregar o PDF</p>
            </div>
          </div>
        ) : (
          <iframe
            src={pdfUrl}
            className="w-full h-full border-0"
            style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top left', width: `${10000 / zoom}%`, height: `${10000 / zoom}%` }}
            onError={() => setError(true)}
            title="PDF Preview"
          />
        )}
      </div>
    </div>
  );
}

function TableEditor({ data, onChange }) {
  const [tableData, setTableData] = useState(data);
  
  const updateCell = (rowIdx, cellIdx, value) => {
    const newRows = [...tableData.rows];
    newRows[rowIdx] = [...newRows[rowIdx]];
    newRows[rowIdx][cellIdx] = value;
    const updated = { ...tableData, rows: newRows };
    setTableData(updated);
    onChange(JSON.stringify(updated));
  };
  
  const updateHeader = (idx, value) => {
    const newHeaders = [...tableData.headers];
    newHeaders[idx] = value;
    const updated = { ...tableData, headers: newHeaders };
    setTableData(updated);
    onChange(JSON.stringify(updated));
  };
  
  return (
    <div className="overflow-auto max-h-[400px]">
      <table className="min-w-full text-xs border-collapse">
        <thead className="sticky top-0 bg-card">
          <tr>
            {tableData.headers.map((h, i) => (
              <th key={i} className="px-2 py-1.5 border border-border/50">
                <input
                  type="text"
                  value={h}
                  onChange={(e) => updateHeader(i, e.target.value)}
                  className="w-full px-1 py-0.5 bg-muted/10 border-0 rounded text-foreground font-medium focus:outline-none focus:ring-1 focus:ring-primary/30"
                />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tableData.rows.map((row, rowIdx) => (
            <tr key={rowIdx} className={rowIdx % 2 === 0 ? 'bg-card' : 'bg-muted/5'}>
              {row.map((cell, cellIdx) => (
                <td key={cellIdx} className="px-1 py-0.5 border border-border/50">
                  <input
                    type="text"
                    value={cell}
                    onChange={(e) => updateCell(rowIdx, cellIdx, e.target.value)}
                    className="w-full px-1 py-0.5 bg-transparent border-0 text-muted focus:outline-none focus:ring-1 focus:ring-primary/30 rounded"
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ReviewQueue() {
  const { addToast } = useToast();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);
  const [editContent, setEditContent] = useState('');
  const [editTableData, setEditTableData] = useState(null);
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
    setEditContent(content);
    
    if (item.block_type === 'tabela' || item.block_type === 'table') {
      const tableData = parseTableContent(content);
      setEditTableData(tableData);
    } else {
      setEditTableData(null);
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
              {selectedItem?.block_type === 'tabela' && editTableData && (
                <span className="text-xs text-muted">
                  {editTableData.headers?.length || 0} colunas · {editTableData.rows?.length || 0} linhas
                </span>
              )}
            </div>
            
            <div className="flex-1 overflow-auto p-3 bg-card border border-t-0 border-border rounded-b-lg">
              {selectedItem?.block_type === 'tabela' && editTableData ? (
                <TableEditor 
                  data={editTableData} 
                  onChange={(newContent) => setEditContent(newContent)}
                />
              ) : (
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="w-full h-full px-3 py-2 bg-transparent border-0
                             text-foreground text-sm resize-none focus:outline-none"
                  placeholder="Conteúdo do bloco..."
                />
              )}
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
