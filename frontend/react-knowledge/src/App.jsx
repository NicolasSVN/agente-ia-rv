import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { ToastProvider } from './components/Toast';
import { Dashboard } from './pages/Dashboard';
import { SmartUpload } from './pages/SmartUpload';
import { ProductDetail } from './pages/ProductDetail';
import { ReviewQueue } from './pages/ReviewQueue';
import { Documents } from './pages/Documents';
import { LayoutDashboard, Upload, ClipboardCheck, FileText } from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Produtos' },
  { to: '/upload', icon: Upload, label: 'Upload Inteligente' },
  { to: '/review', icon: ClipboardCheck, label: 'Fila de Revisão' },
  { to: '/documents', icon: FileText, label: 'Documentos' },
];

function SubNav() {
  return (
    <div className="flex gap-2 mb-6 pb-4 border-b border-border">
      {navItems.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === '/'}
          className={({ isActive }) => `
            flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors
            ${isActive 
              ? 'bg-primary text-white' 
              : 'bg-card border border-border text-muted hover:bg-border/50 hover:text-foreground'}
          `}
        >
          <item.icon className="w-4 h-4" />
          <span>{item.label}</span>
        </NavLink>
      ))}
    </div>
  );
}

function Layout({ children }) {
  return (
    <div className="page-container">
      <SubNav />
      {children}
    </div>
  );
}

function App() {
  return (
    <BrowserRouter basename="/base-conhecimento">
      <ToastProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<SmartUpload />} />
            <Route path="/product/:id" element={<ProductDetail />} />
            <Route path="/review" element={<ReviewQueue />} />
            <Route path="/documents" element={<Documents />} />
          </Routes>
        </Layout>
      </ToastProvider>
    </BrowserRouter>
  );
}

export default App;
