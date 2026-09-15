import { defineConfig } from '@playwright/test'
export default defineConfig({
  timeout: 60000,
  testDir: './tests/browser',
  workers: 1,
  use: { baseURL: 'http://127.0.0.1:5173', headless: true },
  webServer: { command: 'npm run dev -- --port 5173', url: 'http://127.0.0.1:5173', reuseExistingServer: false },
})
