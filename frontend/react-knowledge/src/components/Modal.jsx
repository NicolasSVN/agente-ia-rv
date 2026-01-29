import * as Dialog from '@radix-ui/react-dialog';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

export function Modal({ open, onClose, title, children, size = 'md' }) {
  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
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
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                className={`fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                           w-[calc(100%-2rem)] ${sizeClasses[size]} bg-card rounded-card 
                           shadow-modal z-50 max-h-[90vh] flex flex-col`}
              >
                <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                  <Dialog.Title className="font-semibold text-lg text-foreground">
                    {title}
                  </Dialog.Title>
                  <Dialog.Close asChild>
                    <button className="p-2 rounded-full hover:bg-border text-muted hover:text-foreground transition-colors">
                      <X className="w-5 h-5" />
                    </button>
                  </Dialog.Close>
                </div>
                <div className="flex-1 overflow-y-auto p-6">
                  {children}
                </div>
              </motion.div>
            </Dialog.Content>
          </Dialog.Portal>
        )}
      </AnimatePresence>
    </Dialog.Root>
  );
}
