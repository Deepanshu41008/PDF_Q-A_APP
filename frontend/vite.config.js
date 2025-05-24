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
    allowedHosts: [
      'work-2-mlwrmwhcbesatuqv.prod-runtime.all-hands.dev',
      'work-1-mlwrmwhcbesatuqv.prod-runtime.all-hands.dev'
    ]
  }
})