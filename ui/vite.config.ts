import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const backendBase = env.VITE_HEIDI_SERVER_BASE || env.HEIDI_SERVER_BASE || 'http://127.0.0.1:7777';

  return {
    plugins: [react()],
    build: {
      outDir: 'dist',
      emptyOutDir: true,
    },
    server: {
      host: '0.0.0.0',
      port: 3002,
      strictPort: true,
      allowedHosts: ['heidiai.com.au', '.heidiai.com.au', 'localhost', '127.0.0.1'],
      proxy: {
        '^/health': {
          target: backendBase,
          changeOrigin: true,
        },
        '^/agents': {
          target: backendBase,
          changeOrigin: true,
        },
        '^/run': {
          target: backendBase,
          changeOrigin: true,
        },
        '^/loop': {
          target: backendBase,
          changeOrigin: true,
        },
        '^/chat': {
          target: backendBase,
          changeOrigin: true,
        },
        '^/runs': {
          target: backendBase,
          changeOrigin: true,
        },
        '^/api': {
          target: backendBase,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
  };
});
