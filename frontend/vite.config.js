import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 12001,
    strictPort: true,
    cors: true,
    hmr: {
      clientPort: 12001
    },
    proxy: {
      '/api': {
        target: 'http://localhost:12000',
        changeOrigin: true,
        // Do NOT rewrite! /api/documents/... must reach backend as /api/documents/...
      },
      '/ws': {
        target: 'ws://localhost:12000',
        ws: true,
        changeOrigin: true
      }
    }
  }
})
