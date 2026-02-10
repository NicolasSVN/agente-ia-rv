import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, CheckCircle, ArrowRight, Sparkles, Info, AlertCircle, RotateCcw, Clock, Trash2, X, Loader, Files, List } from 'lucide-react';
import { materialsAPI, productsAPI } from '../services/api';
import { Button } from '../components/Button';
import { ProductAutocomplete } from '../components/ProductAutocomplete';
import { MaterialCategories } from '../components/MaterialCategories';
import { StructuredTags } from '../components/StructuredTags';
import { useToast } from '../components/Toast';
import { useDropzone } from 'react-dropzone';

export function SmartUpload() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { addToast } = useToast();
  const logRef = useRef(null);
  
  const [step, setStep] = useState(1);
  const [files, setFiles] = useState([]);
  const [materialCategories, setMaterialCategories] = useState([]);
  const [validFrom, setValidFrom] = useState('');
  const [validUntil, setValidUntil] = useState('');
  const [tags, setTags] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadComplete, setUploadComplete] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [hasError, setHasError] = useState(false);
  const [resumableInfo, setResumableInfo] = useState(null);
  const [resumableMaterialId, setResumableMaterialId] = useState(null);
  const [pendingMaterials, setPendingMaterials] = useState([]);
  const [loadingPending, setLoadingPending] = useState(true);

  const [queueItems, setQueueItems] = useState([]);
  const [showQueue, setShowQueue] = useState(false);
  const [batchMode, setBatchMode] = useState(false);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  useEffect(() => {
    const productId = searchParams.get('product');
    if (productId) {
      productsAPI.get(productId).then((product) => {
        setSelectedProduct(product);
      }).catch(() => {});
    }
  }, [searchParams]);

  useEffect(() => {
    loadPendingMaterials();
    loadQueueStatus();
  }, []);

  useEffect(() => {
    if (showQueue || batchMode) {
      connectToQueueStream();
    }
    return () => {
      eventSourceRef.current = null;
    };
  }, [showQueue, batchMode]);

  const loadQueueStatus = async () => {
    try {
      const response = await fetch('/api/products/upload-queue/status', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (response.ok) {
        const data = await response.json();
        setQueueItems([...(data.active || []), ...(data.history || []).slice(0, 10)]);
        if (data.active && data.active.length > 0) {
          setShowQueue(true);
        }
      }
    } catch (err) {
      console.error('Erro ao carregar fila:', err);
    }
  };

  const connectToQueueStream = () => {
    if (eventSourceRef.current) return;
    eventSourceRef.current = true;

    const pollQueue = async () => {
      while (eventSourceRef.current) {
        await loadQueueStatus();
        await new Promise(r => setTimeout(r, 3000));
      }
    };
    pollQueue();
  };

  const loadPendingMaterials = async () => {
    setLoadingPending(true);
    try {
      const response = await fetch('/api/products/materials/pending', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (response.ok) {
        const data = await response.json();
        setPendingMaterials(data.pending_materials || []);
      }
    } catch (err) {
      console.error('Erro ao carregar materiais pendentes:', err);
    } finally {
      setLoadingPending(false);
    }
  };

  const handleResumeFromList = async (materialId) => {
    setResumableMaterialId(materialId);
    setStep(3);
    setLogs([]);
    setHasError(false);
    setUploadComplete(false);
    setUploading(true);
    setUploadProgress(0);
    setBatchMode(false);
    
    addLog('Retomando processamento...', 'info');
    
    try {
      const response = await fetch(`/api/products/materials/${materialId}/resume-upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const text = decoder.decode(value, { stream: true });
        const lines = text.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6));
              
              if (event.type === 'progress') {
                setUploadProgress(event.percent);
                setCurrentPage(event.current || 0);
                setTotalPages(event.total || 0);
              } else if (event.type === 'log') {
                addLog(event.message, event.log_type || 'info');
              } else if (event.type === 'complete') {
                setUploadComplete(true);
                setUploadProgress(100);
                setUploading(false);
                setStats(event.stats);
                addLog(event.message, 'success');
                addToast('Documento processado com sucesso!', 'success');
                loadPendingMaterials();
              } else if (event.type === 'error') {
                setHasError(true);
                setUploading(false);
                addLog(event.message, 'error');
                addToast(event.message, 'error');
              }
            } catch (e) {}
          }
        }
      }
    } catch (err) {
      addLog(`Erro: ${err.message}`, 'error');
      addToast(`Erro: ${err.message}`, 'error');
      setHasError(true);
      setUploading(false);
    }
  };

  const handleDiscardPending = async (materialId, productId) => {
    if (!confirm('Deseja descartar este upload? O arquivo e os blocos serão removidos.')) return;
    
    try {
      const response = await fetch(`/api/products/${productId}/materials/${materialId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (response.ok) {
        addToast('Upload descartado', 'success');
        loadPendingMaterials();
      } else {
        throw new Error('Falha ao descartar');
      }
    } catch (err) {
      addToast('Erro ao descartar', 'error');
    }
  };

  const addLog = (message, type = 'info') => {
    const time = new Date().toLocaleTimeString('pt-BR');
    setLogs(prev => [...prev, { time, message, type }]);
  };

  const handleResume = async () => {
    if (!resumableMaterialId) return;
    
    setUploading(true);
    setStep(3);
    setLogs([]);
    setHasError(false);
    setStats(null);
    setResumableInfo(null);
    setBatchMode(false);
    
    addLog('Retomando processamento...', 'info');
    
    try {
      const response = await fetch(`/api/products/materials/${resumableMaterialId}/resume-upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const text = decoder.decode(value, { stream: true });
        const lines = text.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6));
              
              if (event.type === 'progress') {
                setUploadProgress(event.percent);
                setCurrentPage(event.current || 0);
                setTotalPages(event.total || 0);
              } else if (event.type === 'log') {
                addLog(event.message, event.log_type || 'info');
              } else if (event.type === 'complete') {
                setUploadComplete(true);
                setUploadProgress(100);
                setStats(event.stats);
                addLog(event.message || 'Processamento concluído!', 'success');
                addToast({ type: 'success', message: 'Documento processado com sucesso!' });
              } else if (event.type === 'error') {
                setHasError(true);
                addLog(event.message, 'error');
                if (event.resumable) {
                  setResumableInfo({ jobId: event.job_id });
                }
              }
            } catch (e) {}
          }
        }
      }
    } catch (err) {
      setHasError(true);
      addLog(`Erro: ${err.message}`, 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleUploadWithProduct = async () => {
    setUploading(true);
    setStep(3);
    setLogs([]);
    setHasError(false);
    setStats(null);
    setBatchMode(false);

    const file = files[0];

    try {
      const materialData = {
        material_type: materialCategories[0] || 'outro',
        material_categories: materialCategories,
        name: file.name.replace('.pdf', ''),
        tags: tags,
        valid_from: validFrom || null,
        valid_until: validUntil || null,
      };

      addLog('Iniciando upload para produto selecionado...', 'info');
      
      let progress = 0;
      const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        setUploadProgress(Math.round(progress));
        addLog(`Processando... ${Math.round(progress)}%`, 'info');
      }, 1500);

      const result = await materialsAPI.create(selectedProduct.id, materialData);
      const materialId = result.material_id || result.id;
      addLog(`Material criado (ID: ${materialId}), enviando PDF...`, 'info');
      
      await materialsAPI.uploadPDF(selectedProduct.id, materialId, file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadComplete(true);
      setUploading(false);
      setStats({ blocks_created: 0, auto_approved: 0, pending_review: 0, products_matched: [selectedProduct.ticker || selectedProduct.name] });
      addLog('Documento processado com sucesso!', 'success');
      addToast('Documento processado com sucesso!', 'success');
    } catch (err) {
      addLog(`Erro: ${err.message}`, 'error');
      addToast(`Erro: ${err.message}`, 'error');
      setHasError(true);
      setUploading(false);
    }
  };

  const handleUploadStreaming = async () => {
    const file = files[0];
    setUploading(true);
    setStep(3);
    setLogs([]);
    setHasError(false);
    setStats(null);
    setBatchMode(false);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('material_type', materialCategories[0] || 'outro');
      formData.append('material_categories', JSON.stringify(materialCategories));
      formData.append('name', file.name.replace('.pdf', ''));
      formData.append('tags', JSON.stringify(tags));
      if (validFrom) formData.append('valid_from', validFrom);
      if (validUntil) formData.append('valid_until', validUntil);

      addLog('Iniciando upload do arquivo...', 'info');

      const response = await fetch('/api/products/smart-upload-stream', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const eventBlock of events) {
          const lines = eventBlock.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const event = JSON.parse(line.slice(6));
                
                if (event.type === 'start') {
                  addLog(event.message, 'info');
                } else if (event.type === 'progress') {
                  setCurrentPage(event.current);
                  setTotalPages(event.total);
                  setUploadProgress(event.percent);
                } else if (event.type === 'log') {
                  addLog(event.message, event.log_type || 'info');
                } else if (event.type === 'complete') {
                  setUploadProgress(100);
                  setUploadComplete(true);
                  setUploading(false);
                  setStats(event.stats);
                  addLog(event.message, 'success');
                  addToast('Documento processado com sucesso!', 'success');
                } else if (event.type === 'error') {
                  setHasError(true);
                  setUploading(false);
                  addLog(event.message, 'error');
                  addToast(event.message, 'error');
                  if (event.resumable && event.job_id) {
                    setResumableInfo({ jobId: event.job_id });
                  }
                } else if (event.type === 'start' && event.material_id) {
                  setResumableMaterialId(event.material_id);
                }
              } catch (e) {
              }
            }
          }
        }
      }
    } catch (err) {
      addLog(`Erro: ${err.message}`, 'error');
      addToast(`Erro: ${err.message}`, 'error');
      setHasError(true);
      setUploading(false);
    }
  };

  const handleBatchUpload = async () => {
    if (files.length === 0 || materialCategories.length === 0) {
      addToast('Selecione pelo menos um arquivo e uma categoria', 'warning');
      return;
    }

    setBatchMode(true);
    setStep(3);
    setShowQueue(true);

    try {
      const formData = new FormData();
      for (const file of files) {
        formData.append('files', file);
      }
      formData.append('material_type', materialCategories[0] || 'outro');
      formData.append('material_categories', JSON.stringify(materialCategories));
      formData.append('tags', JSON.stringify(tags));
      if (validFrom) formData.append('valid_from', validFrom);
      if (validUntil) formData.append('valid_until', validUntil);

      const response = await fetch('/api/products/batch-upload', {
        method: 'POST',
        body: formData,
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });

      if (!response.ok) throw new Error(`Erro ${response.status}`);

      const data = await response.json();
      addToast(`${data.total_queued} arquivo(s) adicionado(s) à fila de processamento`, 'success');
      
      loadQueueStatus();
    } catch (err) {
      addToast(`Erro ao enviar arquivos: ${err.message}`, 'error');
      setBatchMode(false);
    }
  };

  const handleUpload = async () => {
    if (!files.length || materialCategories.length === 0) {
      addToast('Selecione um arquivo e pelo menos uma categoria', 'warning');
      return;
    }

    if (files.length > 1) {
      await handleBatchUpload();
      return;
    }

    if (selectedProduct) {
      await handleUploadWithProduct();
    } else {
      await handleUploadStreaming();
    }
  };

  const getLogColor = (type) => {
    switch (type) {
      case 'success': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      case 'error': return 'text-red-400';
      default: return 'text-slate-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'processing': return <Loader className="w-4 h-4 text-primary animate-spin" />;
      case 'failed': return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'queued': return <Clock className="w-4 h-4 text-amber-500" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'completed': return 'Concluído';
      case 'processing': return 'Processando';
      case 'failed': return 'Falhou';
      case 'queued': return 'Na fila';
      default: return status;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-50 text-green-700 border-green-200';
      case 'processing': return 'bg-primary/5 text-primary border-primary/20';
      case 'failed': return 'bg-red-50 text-red-700 border-red-200';
      case 'queued': return 'bg-amber-50 text-amber-700 border-amber-200';
      default: return 'bg-gray-50 text-gray-600 border-gray-200';
    }
  };

  const onDrop = useCallback((acceptedFiles) => {
    const pdfFiles = acceptedFiles.filter(f => f.name.toLowerCase().endsWith('.pdf'));
    if (pdfFiles.length === 0) {
      addToast('Apenas arquivos PDF são aceitos', 'warning');
      return;
    }
    setFiles(prev => [...prev, ...pdfFiles]);
  }, [addToast]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxSize: 50 * 1024 * 1024,
    multiple: true,
  });

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const renderPendingSection = () => {
    if (loadingPending || pendingMaterials.length === 0) return null;
    
    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl"
      >
        <div className="flex items-center gap-2 mb-3">
          <Clock className="w-5 h-5 text-amber-600" />
          <h3 className="font-semibold text-amber-800">Uploads Pendentes</h3>
          <span className="text-xs px-2 py-0.5 bg-amber-200 text-amber-800 rounded-full">
            {pendingMaterials.length}
          </span>
        </div>
        <p className="text-sm text-amber-700 mb-3">
          Estes arquivos tiveram o processamento interrompido. Você pode retomar de onde parou.
        </p>
        <div className="space-y-2">
          {pendingMaterials.map((material) => (
            <div 
              key={material.id}
              className="flex items-center justify-between p-3 bg-white rounded-lg border border-amber-100"
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <FileText className="w-5 h-5 text-amber-600 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="font-medium text-slate-800 truncate">{material.name}</p>
                  <p className="text-xs text-slate-500">
                    {material.product_name && (
                      <span className="text-primary font-medium">{material.product_ticker || material.product_name}</span>
                    )}
                    {material.job_info?.processed_pages !== null && (
                      <span className="ml-2">
                        {material.job_info.processed_pages}/{material.job_info.total_pages || '?'} páginas
                      </span>
                    )}
                    {material.blocks_count > 0 && (
                      <span className="ml-2 text-green-600">{material.blocks_count} blocos</span>
                    )}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {material.can_resume ? (
                  <Button 
                    size="sm"
                    onClick={() => handleResumeFromList(material.id)}
                    className="bg-amber-600 hover:bg-amber-700"
                  >
                    <RotateCcw className="w-4 h-4" />
                    Retomar
                  </Button>
                ) : (
                  <span className="text-xs text-slate-400 mr-2">Requer re-upload</span>
                )}
                <button
                  onClick={() => handleDiscardPending(material.id, material.product_id)}
                  className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded"
                  title="Descartar"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    );
  };

  const renderQueueMonitor = () => {
    const activeItems = queueItems.filter(i => i.status === 'processing' || i.status === 'queued');
    const doneItems = queueItems.filter(i => i.status === 'completed' || i.status === 'failed');

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-foreground flex items-center gap-2">
            <List className="w-5 h-5 text-primary" />
            Fila de Processamento
          </h3>
          <button
            onClick={() => loadQueueStatus()}
            className="text-xs text-primary hover:underline"
          >
            Atualizar
          </button>
        </div>

        {activeItems.length > 0 && (
          <div className="space-y-2">
            {activeItems.map((item) => (
              <div key={item.upload_id} className={`p-4 rounded-lg border ${getStatusColor(item.status)}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    {getStatusIcon(item.status)}
                    <span className="font-medium text-sm truncate">{item.filename}</span>
                  </div>
                  <span className="text-xs font-medium ml-2 flex-shrink-0">{getStatusLabel(item.status)}</span>
                </div>
                {item.status === 'processing' && (
                  <>
                    <div className="h-2 bg-white/50 rounded-full overflow-hidden mb-1">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${item.progress}%` }}
                        className="h-full bg-primary rounded-full transition-all"
                      />
                    </div>
                    <div className="flex justify-between text-xs opacity-75">
                      <span>Página {item.current_page}/{item.total_pages}</span>
                      <span>{item.progress}%</span>
                    </div>
                    {item.product_name && (
                      <p className="text-xs mt-1">
                        Produto: <span className="font-medium">{item.product_ticker || item.product_name}</span>
                      </p>
                    )}
                  </>
                )}
                {item.status === 'queued' && (
                  <p className="text-xs opacity-75">Aguardando na fila...</p>
                )}
              </div>
            ))}
          </div>
        )}

        {activeItems.length === 0 && batchMode && (
          <div className="text-center py-8">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
            <p className="font-medium text-foreground">Todos os arquivos foram processados!</p>
            <p className="text-sm text-muted mt-1">Veja os resultados abaixo</p>
          </div>
        )}

        {doneItems.length > 0 && (
          <div className="mt-4">
            <h4 className="text-sm font-medium text-muted mb-2">Histórico recente</h4>
            <div className="space-y-1">
              {doneItems.slice(0, 10).map((item) => (
                <div key={item.upload_id} className="flex items-center gap-2 p-2 rounded hover:bg-gray-50 text-sm">
                  {getStatusIcon(item.status)}
                  <span className="flex-1 truncate">{item.filename}</span>
                  {item.product_ticker && (
                    <span className="text-xs text-primary font-medium">{item.product_ticker}</span>
                  )}
                  {item.stats && (
                    <span className="text-xs text-muted">{item.stats.blocks_created} blocos</span>
                  )}
                  {item.error && (
                    <span className="text-xs text-red-500 truncate max-w-[150px]" title={item.error}>{item.error}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex gap-3 justify-center pt-4">
          <Button variant="secondary" onClick={() => {
            setStep(1);
            setFiles([]);
            setMaterialCategories([]);
            setTags([]);
            setSelectedProduct(null);
            setUploadComplete(false);
            setUploadProgress(0);
            setLogs([]);
            setStats(null);
            setCurrentPage(0);
            setTotalPages(0);
            setBatchMode(false);
            setShowQueue(false);
          }}>
            Novos Uploads
          </Button>
          <Button onClick={() => navigate('/review')}>
            Ver Fila de Revisão
          </Button>
        </div>
      </div>
    );
  };

  const renderStep1 = () => (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="space-y-6"
    >
      {renderPendingSection()}

      <div className="text-center mb-8">
        <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
          <Upload className="w-8 h-8 text-primary" />
        </div>
        <h2 className="text-xl font-semibold text-foreground">Upload Inteligente</h2>
        <p className="text-muted mt-2">
          Envie um ou mais PDFs e a IA extrairá automaticamente os blocos de conhecimento
        </p>
      </div>

      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'}
        `}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          {files.length > 0 ? (
            <Files className="w-10 h-10 text-primary" />
          ) : (
            <Upload className={`w-10 h-10 ${isDragActive ? 'text-primary' : 'text-muted'}`} />
          )}
          <div>
            <p className="text-sm font-medium text-foreground">
              {isDragActive ? 'Solte os arquivos aqui' : 'Arraste PDFs ou clique para selecionar'}
            </p>
            <p className="text-xs text-muted mt-1">
              Múltiplos arquivos aceitos — Máximo 50MB cada
            </p>
          </div>
        </div>
      </div>

      {files.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-2"
        >
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-foreground">
              {files.length} arquivo{files.length > 1 ? 's' : ''} selecionado{files.length > 1 ? 's' : ''}
            </span>
            <button
              onClick={() => setFiles([])}
              className="text-xs text-red-500 hover:underline"
            >
              Limpar todos
            </button>
          </div>
          <div className="max-h-48 overflow-y-auto space-y-1 border border-border rounded-lg p-2">
            {files.map((f, i) => (
              <div key={i} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg group">
                <FileText className="w-4 h-4 text-primary flex-shrink-0" />
                <span className="text-sm flex-1 truncate">{f.name}</span>
                <span className="text-xs text-muted">{(f.size / 1024 / 1024).toFixed(1)}MB</span>
                <button
                  onClick={() => removeFile(i)}
                  className="p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
          <div className="flex justify-end">
            <Button onClick={() => setStep(2)}>
              Continuar
              <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );

  const renderStep2 = () => (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="space-y-6"
    >
      <div className="flex items-center gap-3 p-4 bg-primary/5 rounded-xl border border-primary/20">
        {files.length === 1 ? (
          <FileText className="w-6 h-6 text-primary" />
        ) : (
          <Files className="w-6 h-6 text-primary" />
        )}
        <div className="flex-1">
          {files.length === 1 ? (
            <>
              <p className="font-medium text-foreground">{files[0]?.name}</p>
              <p className="text-sm text-muted">{(files[0]?.size / 1024 / 1024).toFixed(2)} MB</p>
            </>
          ) : (
            <>
              <p className="font-medium text-foreground">{files.length} arquivos selecionados</p>
              <p className="text-sm text-muted">
                {(files.reduce((s, f) => s + f.size, 0) / 1024 / 1024).toFixed(1)} MB total
              </p>
            </>
          )}
        </div>
        <button
          onClick={() => { setFiles([]); setStep(1); }}
          className="text-sm text-primary hover:underline"
        >
          Trocar
        </button>
      </div>

      <MaterialCategories 
        value={materialCategories} 
        onChange={setMaterialCategories} 
      />

      {files.length === 1 && (
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Produto Relacionado (opcional)
          </label>
          <ProductAutocomplete
            value={selectedProduct}
            onChange={setSelectedProduct}
            placeholder="Digite para buscar um produto..."
          />
          <div className="flex items-start gap-2 mt-2 p-3 bg-blue-50 rounded-xl border border-blue-200">
            <Info className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-blue-700">
              Se não selecionar um produto, a IA identificará automaticamente os produtos mencionados em cada página do documento.
            </p>
          </div>
        </div>
      )}

      {files.length > 1 && (
        <div className="flex items-start gap-2 p-3 bg-blue-50 rounded-xl border border-blue-200">
          <Info className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-blue-700">
            Os {files.length} arquivos serão processados sequencialmente (um de cada vez) para evitar sobrecarga.
            A IA identificará automaticamente os produtos de cada documento. Você pode acompanhar o progresso em tempo real.
          </p>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          Período de Validade (opcional)
        </label>
        <div className="grid grid-cols-2 gap-3">
          <div className="relative">
            <input
              type="date"
              value={validFrom}
              onChange={(e) => setValidFrom(e.target.value)}
              className="w-full px-4 py-3 bg-card border border-border rounded-lg
                         text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
            <span className="absolute -top-2 left-3 px-1 bg-card text-xs text-muted">Início</span>
          </div>
          <div className="relative">
            <input
              type="date"
              value={validUntil}
              onChange={(e) => setValidUntil(e.target.value)}
              min={validFrom || undefined}
              className="w-full px-4 py-3 bg-card border border-border rounded-lg
                         text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
            <span className="absolute -top-2 left-3 px-1 bg-card text-xs text-muted">Fim</span>
          </div>
        </div>
        <p className="text-xs text-muted mt-2">
          Após a data fim, o documento não será mais consultado pelo agente
        </p>
      </div>

      <StructuredTags 
        value={tags} 
        onChange={setTags} 
      />

      <div className="flex gap-3 pt-4">
        <Button variant="secondary" onClick={() => setStep(1)} className="flex-1">
          Voltar
        </Button>
        <Button 
          onClick={handleUpload} 
          disabled={materialCategories.length === 0}
          className="flex-1"
        >
          <Sparkles className="w-4 h-4" />
          {files.length > 1 ? `Processar ${files.length} Arquivos` : 'Processar Automaticamente'}
        </Button>
      </div>
    </motion.div>
  );

  const renderStep3 = () => {
    if (batchMode) {
      return (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="space-y-4"
        >
          {renderQueueMonitor()}
        </motion.div>
      );
    }

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="space-y-6"
      >
        {!uploadComplete ? (
          <>
            <div className="bg-card border border-border rounded-xl p-6">
              <div className="flex justify-between items-center mb-4">
                <h4 className="font-semibold text-foreground flex items-center gap-2">
                  {hasError ? (
                    <AlertCircle className="w-5 h-5 text-red-500" />
                  ) : (
                    <Sparkles className="w-5 h-5 text-primary animate-pulse" />
                  )}
                  {hasError ? 'Erro no processamento' : 'Processando documento...'}
                </h4>
                <span className="text-2xl font-bold text-primary">{uploadProgress}%</span>
              </div>
              
              <div className="h-3 bg-border rounded-full overflow-hidden mb-4">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${uploadProgress}%` }}
                  className={`h-full rounded-full transition-all ${hasError ? 'bg-red-500' : 'bg-gradient-to-r from-primary to-indigo-400'}`}
                />
              </div>
              
              <div className="flex justify-between text-sm text-muted mb-4">
                <span>{currentPage} de {totalPages} páginas</span>
                <span>
                  {stats ? (
                    <>Blocos: <span className="text-green-600 font-semibold">{stats.blocks_created}</span></>
                  ) : 'Aguardando...'}
                </span>
              </div>

              <div 
                ref={logRef}
                className="bg-slate-800 text-slate-300 rounded-lg p-4 font-mono text-xs max-h-48 overflow-y-auto"
                style={{ display: logs.length > 0 ? 'block' : 'none' }}
              >
                {logs.map((log, i) => (
                  <div key={i} className={`mb-1 ${getLogColor(log.type)}`}>
                    [{log.time}] {log.message}
                  </div>
                ))}
              </div>
            </div>

            {hasError && (
              <div className="space-y-4">
                {resumableInfo && resumableMaterialId && (
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <RotateCcw className="w-5 h-5 text-amber-600" />
                      <span className="font-medium text-amber-800">Processamento pode ser retomado</span>
                    </div>
                    <p className="text-sm text-amber-700 mb-3">
                      O arquivo PDF foi salvo e você pode retomar o processamento de onde parou.
                    </p>
                    <Button 
                      onClick={handleResume}
                      className="bg-amber-600 hover:bg-amber-700"
                    >
                      <RotateCcw className="w-4 h-4" />
                      Retomar Processamento
                    </Button>
                  </div>
                )}
                <div className="flex gap-3 justify-center">
                  <Button variant="secondary" onClick={() => {
                    setStep(2);
                    setUploading(false);
                    setUploadProgress(0);
                    setLogs([]);
                    setHasError(false);
                    setResumableInfo(null);
                  }}>
                    Tentar Novamente
                  </Button>
                </div>
              </div>
            )}
          </>
        ) : (
          <>
            <div className="text-center py-4">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6"
              >
                <CheckCircle className="w-10 h-10 text-green-600" />
              </motion.div>
              <h2 className="text-xl font-semibold text-foreground mb-2">
                Documento processado!
              </h2>
              <p className="text-muted mb-4">
                {selectedProduct 
                  ? 'Os blocos foram extraídos e estão prontos para revisão'
                  : 'Os blocos foram extraídos e vinculados automaticamente aos produtos identificados'}
              </p>
            </div>

            {stats && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-blue-600">{stats.blocks_created}</div>
                  <div className="text-xs text-blue-700">Blocos Criados</div>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-green-600">{stats.auto_approved}</div>
                  <div className="text-xs text-green-700">Auto-Aprovados</div>
                </div>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-yellow-600">{stats.pending_review}</div>
                  <div className="text-xs text-yellow-700">Para Revisão</div>
                </div>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-purple-600">{stats.products_matched?.length || 0}</div>
                  <div className="text-xs text-purple-700">Produtos</div>
                </div>
              </div>
            )}

            <div 
              ref={logRef}
              className="bg-slate-800 text-slate-300 rounded-lg p-4 font-mono text-xs max-h-36 overflow-y-auto mb-6"
            >
              {logs.map((log, i) => (
                <div key={i} className={`mb-1 ${getLogColor(log.type)}`}>
                  [{log.time}] {log.message}
                </div>
              ))}
            </div>

            <div className="flex gap-3 justify-center">
              <Button variant="secondary" onClick={() => {
                setStep(1);
                setFiles([]);
                setMaterialCategories([]);
                setTags([]);
                setSelectedProduct(null);
                setUploadComplete(false);
                setUploadProgress(0);
                setLogs([]);
                setStats(null);
                setCurrentPage(0);
                setTotalPages(0);
              }}>
                Novo Upload
              </Button>
              {selectedProduct ? (
                <Button onClick={() => navigate(`/product/${selectedProduct.id}`)}>
                  Ver Produto
                </Button>
              ) : (
                <Button onClick={() => navigate('/review')}>
                  Ver Fila de Revisão
                </Button>
              )}
            </div>
          </>
        )}
      </motion.div>
    );
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center gap-4 mb-8">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                            ${step >= s ? 'bg-primary text-white' : 'bg-border text-muted'}`}>
              {s}
            </div>
            {s < 3 && (
              <div className={`w-16 h-0.5 ml-2 ${step > s ? 'bg-primary' : 'bg-border'}`} />
            )}
          </div>
        ))}
      </div>

      <div className="bg-card rounded-xl border border-border p-8 shadow-sm">
        <AnimatePresence mode="wait">
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}
        </AnimatePresence>
      </div>
    </div>
  );
}
