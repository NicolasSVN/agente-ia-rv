import { motion } from 'framer-motion';
import { FileQuestion } from 'lucide-react';
import { Button } from './Button';

export function EmptyState({ 
  icon: Icon = FileQuestion, 
  title, 
  description, 
  action,
  actionLabel,
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-16 text-center"
    >
      <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-primary" />
      </div>
      <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
      <p className="text-muted text-sm max-w-md mb-6">{description}</p>
      {action && (
        <Button onClick={action} variant="primary">
          {actionLabel}
        </Button>
      )}
    </motion.div>
  );
}
