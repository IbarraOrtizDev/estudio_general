import { test as setup, expect } from '@playwright/test';

const archivo = 'playwright/.auth/user.json';

setup('autenticar', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Correo').fill(process.env.E2E_USER!);
    await page.getByLabel('Contraseña').fill(process.env.E2E_PASS!);
    await page.getByRole('button', { name: 'Entrar' }).click();
    await expect(page).toHaveURL(/\/(tareas|inicio)/);
    await page.context().storageState({ path: archivo });
});
