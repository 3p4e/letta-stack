/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Built into ../frontend/suite and served by the ppdocwiz backend at "/"
// (backend/app.py). In dev, /api is proxied to a local backend on :8770.
export default defineConfig({
  plugins: [react()],
  base: '/',
  build: { outDir: '../frontend/suite', emptyOutDir: true, assetsDir: 'assets' },
  server: { proxy: { '/api': 'http://127.0.0.1:8770' } },
  test: { environment: 'node' },
});
