import {
  defineConfig
} from 'vite'

export default defineConfig({
  root: 'www',
  server: {
    port: 3000,
    open: true,
    host: true
  },
  build: {
    outDir: '../dist',
    emptyOutDir: true
  },
  publicDir: 'public',
  // 기존 HTML 파일을 그대로 사용
  plugins: []
})