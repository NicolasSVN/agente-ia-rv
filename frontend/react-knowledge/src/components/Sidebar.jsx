import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  LayoutDashboard, 
  Upload, 
  ClipboardCheck, 
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useState } from 'react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Produtos' },
  { to: '/upload', icon: Upload, label: 'Upload Inteligente' },
  { to: '/review', icon: ClipboardCheck, label: 'Fila de Revisão' },
  { to: '/documents', icon: FileText, label: 'Documentos' },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.aside
      animate={{ width: collapsed ? 64 : 240 }}
      className="fixed left-0 top-0 h-screen bg-card border-r border-border z-40 flex flex-col"
    >
      <div className="p-4 border-b border-border flex items-center justify-between">
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <h1 className="font-bold text-foreground">Base de</h1>
            <p className="text-sm text-primary font-semibold">Conhecimento</p>
          </motion.div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 rounded-btn hover:bg-border text-muted hover:text-foreground transition-colors"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      <nav className="flex-1 p-2 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `
              flex items-center gap-3 px-3 py-2.5 rounded-btn font-medium
              transition-colors
              ${isActive 
                ? 'bg-primary/10 text-primary' 
                : 'text-muted hover:bg-border/50 hover:text-foreground'}
            `}
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                {item.label}
              </motion.span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="p-2 border-t border-border">
        <button
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-btn font-medium
                     text-muted hover:bg-border/50 hover:text-foreground transition-colors"
        >
          <Settings className="w-5 h-5 flex-shrink-0" />
          {!collapsed && <span>Configurações</span>}
        </button>
      </div>
    </motion.aside>
  );
}
