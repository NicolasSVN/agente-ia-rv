import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './Button';

export function InlineEditField({
  label,
  value,
  onSave,
  type = 'text',
  multiline = false,
  placeholder = '',
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const [status, setStatus] = useState('idle');
  const inputRef = useRef(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      if (multiline) {
        inputRef.current.setSelectionRange(editValue.length, editValue.length);
      }
    }
  }, [isEditing]);

  useEffect(() => {
    setEditValue(value);
  }, [value]);

  const handleSave = async () => {
    if (editValue === value) {
      setIsEditing(false);
      return;
    }

    setStatus('saving');
    try {
      await onSave(editValue);
      setStatus('success');
      setTimeout(() => {
        setStatus('idle');
        setIsEditing(false);
      }, 1500);
    } catch (error) {
      setStatus('error');
      setTimeout(() => setStatus('idle'), 2000);
    }
  };

  const handleCancel = () => {
    setEditValue(value);
    setIsEditing(false);
    setStatus('idle');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      handleCancel();
    }
    if (e.key === 'Enter' && !multiline) {
      handleSave();
    }
    if (e.key === 'Enter' && e.ctrlKey && multiline) {
      handleSave();
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-foreground">{label}</label>
        <AnimatePresence mode="wait">
          {status === 'success' && (
            <motion.span
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-1 text-xs text-success font-medium"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Salvo
            </motion.span>
          )}
          {status === 'error' && (
            <motion.span
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-1 text-xs text-danger font-medium"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Erro ao salvar
            </motion.span>
          )}
          {status === 'saving' && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-1 text-xs text-muted"
            >
              <svg className="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Salvando...
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence mode="wait">
        {isEditing ? (
          <motion.div
            key="editing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-2"
          >
            {multiline ? (
              <textarea
                ref={inputRef}
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                rows={4}
                className="w-full px-3 py-2 bg-card border-2 border-primary rounded-input text-foreground
                         placeholder:text-muted focus:outline-none resize-none transition-colors"
              />
            ) : (
              <input
                ref={inputRef}
                type={type}
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                className="w-full px-3 py-2 bg-card border-2 border-primary rounded-input text-foreground
                         placeholder:text-muted focus:outline-none transition-colors"
              />
            )}
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={handleSave}
                loading={status === 'saving'}
                disabled={status === 'saving'}
              >
                Salvar
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={handleCancel}
                disabled={status === 'saving'}
              >
                Cancelar
              </Button>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="display"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsEditing(true)}
            className="group cursor-pointer"
          >
            <div className="px-3 py-2 bg-background border border-transparent rounded-input
                          group-hover:border-border group-hover:bg-card transition-all">
              {multiline ? (
                <p className="text-sm text-foreground whitespace-pre-wrap min-h-[60px]">
                  {value || <span className="text-muted italic">{placeholder || 'Clique para editar'}</span>}
                </p>
              ) : (
                <span className="text-sm text-foreground">
                  {value || <span className="text-muted italic">{placeholder || 'Clique para editar'}</span>}
                </span>
              )}
            </div>
            <p className="text-xs text-muted mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
              Clique para editar {multiline && '(Ctrl+Enter para salvar)'}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
