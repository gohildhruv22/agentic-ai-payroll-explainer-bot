/**
 * Vite config: React plugin, dev server on 5173, proxies /api → FastAPI (default port 8001).
 * Set VITE_DEV_API_PROXY or VITE_BACKEND_URL in frontend/.env to change the backend URL.
 */
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backend =
    env.VITE_DEV_API_PROXY ||
    env.VITE_BACKEND_URL ||
    'http://127.0.0.1:8001'

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: backend,
          changeOrigin: true,
        },
      },
    },
  }
})
