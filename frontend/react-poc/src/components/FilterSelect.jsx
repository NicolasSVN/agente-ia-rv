import * as Select from '@radix-ui/react-select';
import { motion, AnimatePresence } from 'framer-motion';

export function FilterSelect({ label, value, onChange, options, placeholder = 'Todos' }) {
  return (
    <div className="flex flex-col gap-1">
      {label && <span className="text-xs font-medium text-muted">{label}</span>}
      <Select.Root value={value} onValueChange={onChange}>
        <Select.Trigger className="inline-flex items-center justify-between gap-2 px-3 py-2 bg-card border border-border rounded-input text-sm text-foreground hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20 min-w-[140px]">
          <Select.Value placeholder={placeholder} />
          <Select.Icon>
            <svg className="w-4 h-4 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </Select.Icon>
        </Select.Trigger>

        <Select.Portal>
          <Select.Content className="bg-card border border-border rounded-card shadow-modal overflow-hidden z-50">
            <Select.Viewport className="p-1">
              <Select.Item
                value=""
                className="px-3 py-2 text-sm text-muted outline-none cursor-pointer hover:bg-background rounded"
              >
                <Select.ItemText>{placeholder}</Select.ItemText>
              </Select.Item>
              {options.map((option) => (
                <Select.Item
                  key={option.value}
                  value={option.value}
                  className="px-3 py-2 text-sm text-foreground outline-none cursor-pointer hover:bg-background rounded data-[highlighted]:bg-background"
                >
                  <Select.ItemText>{option.label}</Select.ItemText>
                </Select.Item>
              ))}
            </Select.Viewport>
          </Select.Content>
        </Select.Portal>
      </Select.Root>
    </div>
  );
}
