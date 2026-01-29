import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, X, CheckCircle, Loader } from 'lucide-react';

export function FileUpload({ 
  onFileSelect, 
  accept = { 'application/pdf': ['.pdf'] },
  maxSize = 50 * 1024 * 1024,
  uploading = false,
  uploadProgress = 0,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState(null);

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    setError(null);
    
    if (rejectedFiles.length > 0) {
      const err = rejectedFiles[0].errors[0];
      if (err.code === 'file-too-large') {
        setError(`Arquivo muito grande. Máximo: ${Math.round(maxSize / 1024 / 1024)}MB`);
      } else if (err.code === 'file-invalid-type') {
        setError('Tipo de arquivo não suportado. Use PDF.');
      } else {
        setError(err.message);
      }
      return;
    }

    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setSelectedFile(file);
      onFileSelect?.(file);
    }
  }, [onFileSelect, maxSize]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxSize,
    multiple: false,
  });

  const clearFile = (e) => {
    e.stopPropagation();
    setSelectedFile(null);
    onFileSelect?.(null);
  };

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-card p-8 text-center cursor-pointer
          transition-colors
          ${isDragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'}
          ${error ? 'border-danger bg-danger/5' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <AnimatePresence mode="wait">
          {uploading ? (
            <motion.div
              key="uploading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-3"
            >
              <Loader className="w-10 h-10 text-primary animate-spin" />
              <p className="text-sm font-medium text-foreground">Processando documento...</p>
              <div className="w-full max-w-xs h-2 bg-border rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${uploadProgress}%` }}
                  className="h-full bg-primary rounded-full"
                />
              </div>
              <p className="text-xs text-muted">A IA está extraindo blocos semânticos</p>
            </motion.div>
          ) : selectedFile ? (
            <motion.div
              key="selected"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center justify-center gap-3"
            >
              <FileText className="w-8 h-8 text-primary" />
              <div className="text-left">
                <p className="text-sm font-medium text-foreground">{selectedFile.name}</p>
                <p className="text-xs text-muted">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <button
                onClick={clearFile}
                className="p-1 rounded-full hover:bg-border text-muted hover:text-danger"
              >
                <X className="w-5 h-5" />
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-3"
            >
              <Upload className={`w-10 h-10 ${isDragActive ? 'text-primary' : 'text-muted'}`} />
              <div>
                <p className="text-sm font-medium text-foreground">
                  {isDragActive ? 'Solte o arquivo aqui' : 'Arraste um PDF ou clique para selecionar'}
                </p>
                <p className="text-xs text-muted mt-1">
                  Máximo {Math.round(maxSize / 1024 / 1024)}MB
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {error && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm text-danger"
        >
          {error}
        </motion.p>
      )}
    </div>
  );
}
