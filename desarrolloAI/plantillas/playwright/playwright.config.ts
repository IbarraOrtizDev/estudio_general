import { defineConfig, devices } from '@playwright/test';

const AUTH = 'playwright/.auth/user.json';

export default defineConfig({
    testDir: './tests',
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,
    reporter: [['html', { open: 'never' }], ['list']],
    use: {
        baseURL: process.env.BASE_URL ?? 'http://localhost:5173',
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
        locale: 'es-CO',
        timezoneId: 'America/Bogota'
    },
    projects: [
        { name: 'setup', testMatch: /.*\.setup\.ts/ },
        { name: 'chromium', use: { ...devices['Desktop Chrome'], storageState: AUTH }, dependencies: ['setup'] },
        { name: 'firefox', use: { ...devices['Desktop Firefox'], storageState: AUTH }, dependencies: ['setup'] },
        { name: 'webkit', use: { ...devices['Desktop Safari'], storageState: AUTH }, dependencies: ['setup'] }
    ],
    webServer: {
        command: 'npm run dev',
        url: 'http://localhost:5173',
        reuseExistingServer: !process.env.CI,
        timeout: 120_000
    }
});
