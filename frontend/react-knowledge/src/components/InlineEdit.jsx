import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, X, Pencil, Loader } from 'lucide-react';

export function InlineEdit({
  value,
  onSave,
  placeholder = 'Clique para editar...',
  multiline = false,
  label,
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value || '');
  const [saving, setSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    setEditValue(value || '');
  }, [value]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      if (multiline) {
        inputRef.current.selectionStart = inputRef.current.value.length;
      }
    }
  }, [isEditing, multiline]);

  const handleSave = async () => {
    if (editValue === value) {
      setIsEditing(false);
      return;
    }

    setSaving(true);
    try {
      await onSave(editValue);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 2000);
    } catch (err) {
      setEditValue(value || '');
    }
    setSaving(false);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditValue(value || '');
    setIsEditing(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      handleCancel();
    } else if (e.key === 'Enter' && !multiline) {
      handleSave();
    } else if (e.key === 'Enter' && e.metaKey && multiline) {
      handleSave();
    }
  };

  const InputComponent = multiline ? 'textarea' : 'input';

  return (
    <div className="space-y-1">
      {label && (
        <label className="block text-sm font-medium text-muted">{label}</label>
      )}
      
      <AnimatePresence mode="wait">
        {isEditing ? (
          <motion.div
            key="editing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex gap-2"
          >
            <InputComponent
              ref={inputRef}
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              rows={multiline ? 4 : undefined}
              className={`flex-1 px-3 py-2 bg-card border border-primary rounded-input
                         text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20
                         ${multiline ? 'resize-none' : ''}`}
            />
            <div className="flex flex-col gap-1">
              <button
                onClick={handleSave}
                disabled={saving}
                className="p-2 bg-success text-white rounded-btn hover:bg-success/90 disabled:opacity-50"
              >
                {saving ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  <Check className="w-4 h-4" />
                )}
              </button>
              <button
                onClick={handleCancel}
                disabled={saving}
                className="p-2 bg-border text-muted rounded-btn hover:bg-border/80"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="display"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsEditing(true)}
            className={`group flex items-start gap-2 px-3 py-2 rounded-input cursor-pointer
                       hover:bg-border/30 transition-colors
                       ${!value ? 'italic text-muted' : 'text-foreground'}`}
          >
            <span className={`flex-1 ${multiline ? 'whitespace-pre-wrap' : ''}`}>
              {value || placeholder}
            </span>
            <AnimatePresence>
              {showSuccess ? (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                  className="text-success"
                >
                  <Check className="w-4 h-4" />
                </motion.span>
              ) : (
                <Pencil className="w-4 h-4 text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
