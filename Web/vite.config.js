import { fileURLToPath, URL } from 'node:url'
import basicSsl from '@vitejs/plugin-basic-ssl'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    basicSsl(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    https: true,  // 启用 HTTPS
    host: '0.0.0.0',  // 允许外部访问
    port: 5173,
    cors: true,
    // 修复 HMR 在 HTTPS 下的问题
    hmr: {
      protocol: 'wss',  // 使用安全的 WebSocket
      host: 'localhost',
      port: 5173
    },
    // 添加代理配置
    proxy: {
      '/api': {
        target: 'https://10.250.1.63:8090',
        changeOrigin: true,
        secure: false, // 忽略证书验证
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        }
      }
    }
  }
})
