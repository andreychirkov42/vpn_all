import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    // Разрешаем хосты туннеля (cloudflared) — иначе Vite отдаёт "host not allowed".
    allowedHosts: ['.trycloudflare.com'],
    // Проксируем запросы фронта к BFF — один origin, без CORS, работает и через туннель.
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
