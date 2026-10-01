import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // In dev, forward API calls to the FastAPI backend so cookies are same-origin.
      '/api': 'http://localhost:8000',
    },
  },
})
