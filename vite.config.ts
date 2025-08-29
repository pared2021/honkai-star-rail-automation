import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from "vite-tsconfig-paths";
import { traeBadgePlugin } from 'vite-plugin-trae-solo-badge';
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [
          'react-dev-locator',
        ],
      },
    }),
    traeBadgePlugin({
      variant: 'dark',
      position: 'bottom-right',
      prodOnly: true,
      clickable: true,
      clickUrl: 'https://www.trae.ai/solo?showJoin=1',
      autoTheme: true,
      autoThemeTarget: '#root'
    }), 
    tsconfigPaths(),
  ],
  resolve: {
    alias: {
      'active-win': path.resolve(__dirname, 'src/utils/active-win-compat.ts'),
      'ps-list': path.resolve(__dirname, 'src/utils/ps-list-compat.ts'),
      'robotjs': path.resolve(__dirname, 'src/utils/robotjs-compat.ts'),
      'screenshot-desktop': path.resolve(__dirname, 'src/utils/screenshot-desktop-compat.ts'),
      'node-window-manager': path.resolve(__dirname, 'src/utils/node-window-manager-compat.ts'),
      'child_process': path.resolve(__dirname, 'src/utils/child-process-compat.ts'),
      'util': path.resolve(__dirname, 'src/utils/util-compat.ts'),
      'crypto': path.resolve(__dirname, 'src/utils/crypto-compat.ts'),
      'fs': path.resolve(__dirname, 'src/utils/fs-compat.ts'),
      'path': path.resolve(__dirname, 'src/utils/path-compat.ts')
    }
  },
  define: {
    global: 'globalThis',
    'process.env': {},
    'process.platform': JSON.stringify('browser'),
    'process.memoryUsage': 'undefined'
  },
  optimizeDeps: {
    exclude: ['robotjs', 'active-win', 'screenshot-desktop', 'node-window-manager', 'ps-list', 'child_process', 'util']
  },
  ssr: {
    external: ['robotjs', 'active-win', 'screenshot-desktop', 'node-window-manager', 'ps-list', 'child_process', 'util']
  },
  build: {
    rollupOptions: {
      external: ['robotjs', 'active-win', 'screenshot-desktop', 'node-window-manager', 'ps-list', 'child_process', 'util']
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        secure: false,
        configure: (proxy) => {
          proxy.on('error', (err) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (_proxyReq, req) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      }
    }
  }
})
