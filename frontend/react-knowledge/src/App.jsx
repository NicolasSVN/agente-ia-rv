import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { ToastProvider } from './components/Toast';
import { Dashboard } from './pages/Dashboard';
import { SmartUpload } from './pages/SmartUpload';
import { ProductDetail } from './pages/ProductDetail';
import { ReviewQueue } from './pages/ReviewQueue';
import { Documents } from './pages/Documents';

function Layout({ children }) {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="ml-64 p-8">
        {children}
      </main>
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
