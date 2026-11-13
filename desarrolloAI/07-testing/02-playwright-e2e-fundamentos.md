# 07.2 · Playwright E2E: fundamentos

## Objetivos

- Instalar Playwright Test y entender su configuración.
- Escribir tests E2E robustos: localizadores, aserciones web-first, fixtures.
- Organizar con Page Object Model, autenticación reutilizable y mocking de red.
- Depurar con UI mode, trace viewer y codegen.
- Ejecutar en CI. Conocer las variantes para Python y .NET.

> **Nota terminológica:** la herramienta se llama **Playwright** (de Microsoft). Sirve para pruebas **end-to-end (E2E)** en Chromium, Firefox y WebKit.

---

## 1. Instalación (TypeScript, recomendado)

```bash
npm init playwright@latest
# Responde: TypeScript, carpeta tests/, workflow de GitHub Actions: sí, instalar navegadores: sí
```

Genera:
```
playwright.config.ts
tests/example.spec.ts
.github/workflows/playwright.yml
```

Comandos básicos:
```bash
npx playwright test                    # todos los tests, headless, en paralelo
npx playwright test --ui               # UI mode (ideal para desarrollar)
npx playwright test --headed           # ver el navegador
npx playwright test tareas.spec.ts     # un archivo
npx playwright test -g "crear tarea"   # por nombre
npx playwright test --project=chromium
npx playwright show-report             # informe HTML
npx playwright codegen http://localhost:5173   # graba acciones y genera código
```

---

## 2. Configuración

`playwright.config.ts`
```ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './tests',
    fullyParallel: true,
    forbidOnly: !!process.env.CI,          // falla si alguien deja test.only
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,
    reporter: [['html', { open: 'never' }], ['list']],

    use: {
        baseURL: 'http://localhost:5173',
        trace: 'on-first-retry',           // traza para depurar fallos
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
        locale: 'es-CO',
        timezoneId: 'America/Bogota'
    },

    projects: [
        { name: 'setup', testMatch: /.*\.setup\.ts/ },
        { name: 'chromium', use: { ...devices['Desktop Chrome'], storageState: 'playwright/.auth/user.json' }, dependencies: ['setup'] },
        { name: 'firefox', use: { ...devices['Desktop Firefox'], storageState: 'playwright/.auth/user.json' }, dependencies: ['setup'] },
        { name: 'webkit', use: { ...devices['Desktop Safari'], storageState: 'playwright/.auth/user.json' }, dependencies: ['setup'] },
        { name: 'mobile', use: { ...devices['Pixel 7'], storageState: 'playwright/.auth/user.json' }, dependencies: ['setup'] }
    ],

    // Arranca la app antes de los tests
    webServer: {
        command: 'npm run dev',
        url: 'http://localhost:5173',
        reuseExistingServer: !process.env.CI,
        timeout: 120_000
    }
});
```

---

## 3. Tu primer test

```ts
import { test, expect } from '@playwright/test';

test('crear una tarea y verla en la lista', async ({ page }) => {
    await page.goto('/tareas');

    await page.getByLabel('Nueva tarea').fill('Comprar café');
    await page.getByRole('combobox', { name: 'Prioridad' }).selectOption('alta');
    await page.getByRole('button', { name: 'Añadir' }).click();

    const fila = page.getByRole('listitem').filter({ hasText: 'Comprar café' });
    await expect(fila).toBeVisible();
    await expect(fila.getByText('alta')).toBeVisible();
});
```

---

## 4. Localizadores (la clave de tests estables)

Prioridad recomendada (como lo percibe un usuario o una tecnología de asistencia):

| Prioridad | Localizador | Ejemplo |
|---|---|---|
| 1 | `getByRole` | `page.getByRole('button', { name: 'Guardar' })` |
| 2 | `getByLabel` | `page.getByLabel('Correo electrónico')` |
| 3 | `getByPlaceholder` | `page.getByPlaceholder('Buscar...')` |
| 4 | `getByText` | `page.getByText('Bienvenido')` |
| 5 | `getByAltText`, `getByTitle` | imágenes, tooltips |
| 6 | `getByTestId` | `page.getByTestId('fila-tarea-7')` (atributo `data-testid`) |
| ❌ | CSS/XPath frágiles | `div > ul > li:nth-child(3) > span` |

Encadenar y filtrar:
```ts
const tarea = page.getByRole('listitem').filter({ hasText: 'Comprar café' });
await tarea.getByRole('checkbox', { name: 'Completada' }).check();
await expect(page.getByRole('listitem')).toHaveCount(3);
```

> 🔑 Escribir HTML accesible (labels, roles, nombres) hace los tests más estables **y** ayuda a los agentes: Playwright MCP navega usando el árbol de accesibilidad.

---

## 5. Aserciones web-first (auto-espera)

Playwright **espera automáticamente** a que se cumplan las condiciones (hasta el timeout). Nunca uses `waitForTimeout` para "esperar a que cargue".

```ts
await expect(page).toHaveURL(/\/tareas$/);
await expect(page).toHaveTitle('Mis tareas');
await expect(locator).toBeVisible();
await expect(locator).toHaveText('Completada');
await expect(locator).toContainText('café');
await expect(locator).toHaveValue('Comprar café');
await expect(locator).toBeEnabled();
await expect(locator).toHaveCount(5);
await expect(locator).toHaveAttribute('aria-checked', 'true');
await expect(page).toHaveScreenshot('lista.png');   // regresión visual
await expect(locator).toMatchAriaSnapshot(`
  - list:
    - listitem: Comprar café
`);
```

❌ Anti-patrón:
```ts
expect(await locator.isVisible()).toBe(true);   // no espera
await page.waitForTimeout(3000);                // lento y frágil
```

---

## 6. Page Object Model (POM)

`tests/pages/TareasPage.ts`
```ts
import { type Locator, type Page, expect } from '@playwright/test';

export class TareasPage {
    readonly entrada: Locator;
    readonly prioridad: Locator;
    readonly botonAnadir: Locator;
    readonly items: Locator;

    constructor(private readonly page: Page) {
        this.entrada = page.getByLabel('Nueva tarea');
        this.prioridad = page.getByRole('combobox', { name: 'Prioridad' });
        this.botonAnadir = page.getByRole('button', { name: 'Añadir' });
        this.items = page.getByRole('listitem');
    }

    async abrir() { await this.page.goto('/tareas'); }

    async crear(titulo: string, prioridad: 'alta' | 'media' | 'baja' = 'media') {
        await this.entrada.fill(titulo);
        await this.prioridad.selectOption(prioridad);
        await this.botonAnadir.click();
    }

    tarea(titulo: string) { return this.items.filter({ hasText: titulo }); }

    async completar(titulo: string) {
        await this.tarea(titulo).getByRole('checkbox', { name: 'Completada' }).check();
    }

    async esperarTareas(n: number) { await expect(this.items).toHaveCount(n); }
}
```

### Fixtures personalizadas
`tests/fixtures.ts`
```ts
import { test as base } from '@playwright/test';
import { TareasPage } from './pages/TareasPage';

export const test = base.extend<{ tareasPage: TareasPage }>({
    tareasPage: async ({ page }, use) => {
        const tp = new TareasPage(page);
        await tp.abrir();
        await use(tp);
    }
});
export { expect } from '@playwright/test';
```

`tests/tareas.spec.ts`
```ts
import { test, expect } from './fixtures';

test.describe('Gestión de tareas', () => {
    test('crear y completar una tarea', async ({ tareasPage }) => {
        await tareasPage.crear('Escribir tests E2E', 'alta');
        await expect(tareasPage.tarea('Escribir tests E2E')).toBeVisible();

        await tareasPage.completar('Escribir tests E2E');
        await expect(tareasPage.tarea('Escribir tests E2E')).toHaveClass(/completada/);
    });

    test('no permite crear tareas vacías', async ({ tareasPage, page }) => {
        await tareasPage.crear('');
        await expect(page.getByRole('alert')).toHaveText('El título es obligatorio');
    });
});
```

---

## 7. Autenticación reutilizable

`tests/auth.setup.ts`
```ts
import { test as setup, expect } from '@playwright/test';

const archivo = 'playwright/.auth/user.json';

setup('autenticar', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Correo').fill(process.env.E2E_USER!);
    await page.getByLabel('Contraseña').fill(process.env.E2E_PASS!);
    await page.getByRole('button', { name: 'Entrar' }).click();
    await expect(page).toHaveURL('/tareas');
    await page.context().storageState({ path: archivo });
});
```
Añade `playwright/.auth/` a `.gitignore`. El proyecto `setup` del config se ejecuta antes y los demás reutilizan la sesión.

---

## 8. Red: mocks y API testing

```ts
test('muestra mensaje si la API falla', async ({ page }) => {
    await page.route('**/api/tareas', route =>
        route.fulfill({ status: 500, json: { error: 'boom' } }));
    await page.goto('/tareas');
    await expect(page.getByRole('alert')).toContainText('No se pudieron cargar');
});

test('API: crear tarea', async ({ request }) => {
    const r = await request.post('/api/tareas', { data: { titulo: 'API', prioridad: 'baja' } });
    expect(r.ok()).toBeTruthy();
    expect(await r.json()).toMatchObject({ titulo: 'API' });
});
```
Patrón útil: **preparar datos por API** (rápido) y **verificar por UI**.

---

## 9. Depuración

| Herramienta | Uso |
|---|---|
| `npx playwright test --ui` | Ver cada paso, DOM, red, consola; *watch mode* |
| `npx playwright test --debug` | Inspector paso a paso |
| `await page.pause()` | Pausar en un punto |
| Trace viewer | `npx playwright show-trace test-results/.../trace.zip` |
| Codegen | Grabar acciones y obtener localizadores |
| Extensión VS Code | Ejecutar/depurar tests, "Pick locator", grabar |

---

## 10. CI con GitHub Actions

`.github/workflows/playwright.yml`
```yaml
name: E2E
on: [push, pull_request]
jobs:
  e2e:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test
        env:
          E2E_USER: ${{ secrets.E2E_USER }}
          E2E_PASS: ${{ secrets.E2E_PASS }}
      - uses: actions/upload-artifact@v4
        if: ${{ !cancelled() }}
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 14
```
Para suites grandes: `--shard=1/4` en una matriz de jobs.

---

## 11. Playwright en Python y .NET

**Python (pytest-playwright)**
```bash
uv add --dev pytest-playwright
uv run playwright install
```
```python
import re
from playwright.sync_api import Page, expect

def test_crear_tarea(page: Page):
    page.goto("http://localhost:5173/tareas")
    page.get_by_label("Nueva tarea").fill("Desde Python")
    page.get_by_role("button", name="Añadir").click()
    expect(page.get_by_role("listitem").filter(has_text="Desde Python")).to_be_visible()
```
```bash
uv run pytest --browser chromium --headed
```

**.NET (Microsoft.Playwright con NUnit/MSTest/xUnit)**
```bash
dotnet new nunit -n Tareas.E2E
cd Tareas.E2E
dotnet add package Microsoft.Playwright.NUnit
dotnet build
pwsh bin/Debug/net10.0/playwright.ps1 install
```
```csharp
using Microsoft.Playwright.NUnit;
using static Microsoft.Playwright.Assertions;

public class TareasTests : PageTest
{
    [Test]
    public async Task CrearTarea()
    {
        await Page.GotoAsync("http://localhost:5173/tareas");
        await Page.GetByLabel("Nueva tarea").FillAsync("Desde C#");
        await Page.GetByRole(AriaRole.Button, new() { Name = "Añadir" }).ClickAsync();
        await Expect(Page.GetByRole(AriaRole.Listitem).Filter(new() { HasText = "Desde C#" })).ToBeVisibleAsync();
    }
}
```

> Los *Playwright Test Agents* (07.3) solo generan tests para **Playwright Test (TS/JS)**.

---

## Errores comunes

- Selectores CSS frágiles en lugar de `getByRole`/`getByLabel`.
- `waitForTimeout` y aserciones sin `await expect(...)`.
- Tests dependientes entre sí (comparten datos/orden).
- No aislar datos de test (cada test debería crear lo que necesita).
- Commitear `playwright/.auth/` con sesiones válidas.

## Ejercicios

1. Inicializa Playwright en tu proyecto y escribe 3 tests del flujo principal con POM y fixtures.
2. Añade autenticación reutilizable con un proyecto `setup`.
3. Escribe un test que simule un error 500 con `page.route`.
4. Configura el workflow de CI y comprueba que sube el informe como artefacto.
   - ✅ Éxito: el pipeline pasa en Chromium, Firefox y WebKit.

## Checklist

- [ ] Uso localizadores accesibles y aserciones web-first.
- [ ] Organizo con POM y fixtures.
- [ ] Reutilizo autenticación y mockeo red.
- [ ] Depuro con UI mode y trace viewer.
- [ ] Tengo E2E en CI.

---

⬅️ [07.1](01-pruebas-unitarias-con-ia.md) · ➡️ [07.3 · Playwright con IA](03-playwright-con-ia-mcp-y-test-agents.md)
