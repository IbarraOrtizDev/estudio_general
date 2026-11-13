import { test, expect } from '@playwright/test';

// Test semilla para los Playwright Test Agents (planner/generator).
// Deja la app en el estado desde el que se explorará.
test('seed', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('main')).toBeVisible();
});
