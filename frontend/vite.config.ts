/** Keep development and local preview API requests on the browser's own origin. */
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

const proxy = {
  '/api/': { target: 'http://127.0.0.1:8000', changeOrigin: true },
};

export default defineConfig({
  plugins: [tailwindcss(), react()],
  server: { host: '127.0.0.1', port: 5173, strictPort: true, proxy },
  preview: { host: '127.0.0.1', port: 4173, strictPort: true, proxy },
});
