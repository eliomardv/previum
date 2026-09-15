import { defineConfig } from '@playwright/test'
export default defineConfig({
  timeout: 60000,
  testDir: './tests/integration', workers: 1,
  use: { baseURL: 'http://127.0.0.1:8001', headless: true },
})
