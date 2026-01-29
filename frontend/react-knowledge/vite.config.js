import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/base-conhecimento/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
  server: {
    port: 5174,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})
