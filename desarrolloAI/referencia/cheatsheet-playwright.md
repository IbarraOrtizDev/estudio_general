# Cheatsheet · Playwright

## CLI
```bash
npm init playwright@latest
npx playwright install [--with-deps]
npx playwright test                       # todo
npx playwright test --ui                  # UI mode
npx playwright test --headed --project=chromium
npx playwright test archivo.spec.ts -g "nombre"
npx playwright test --debug
npx playwright test --shard=1/4
npx playwright show-report
npx playwright show-trace trace.zip
npx playwright codegen http://localhost:5173
npx playwright init-agents --loop=claude|opencode|vscode
```

## Localizadores (por prioridad)
```ts
page.getByRole('button', { name: 'Guardar' })
page.getByLabel('Correo')
page.getByPlaceholder('Buscar')
page.getByText('Bienvenido')
page.getByTestId('fila-7')
locator.filter({ hasText: 'café' }).getByRole('checkbox')
locator.first() / .nth(2) / .last()
```

## Acciones
```ts
await page.goto('/ruta');
await loc.click(); await loc.dblclick();
await loc.fill('texto'); await loc.press('Enter');
await loc.check(); await loc.uncheck();
await loc.selectOption('alta');
await loc.setInputFiles('archivo.pdf');
await loc.hover();
```

## Aserciones web-first
```ts
await expect(page).toHaveURL(/tareas/);
await expect(page).toHaveTitle('...');
await expect(loc).toBeVisible() / .toBeHidden() / .toBeEnabled() / .toBeChecked();
await expect(loc).toHaveText('...') / .toContainText('...') / .toHaveValue('...');
await expect(loc).toHaveCount(3);
await expect(loc).toHaveAttribute('aria-checked', 'true');
await expect(page).toHaveScreenshot();
await expect(loc).toMatchAriaSnapshot(`- list: ...`);
```

## Red y API
```ts
await page.route('**/api/x', r => r.fulfill({ status: 500, json: {} }));
const res = await request.post('/api/tareas', { data: { ... } });
```

## Estructura recomendada
```
e2e/
├── playwright.config.ts
├── tests/
│   ├── auth.setup.ts
│   ├── fixtures.ts
│   ├── pages/TareasPage.ts
│   ├── seed.spec.ts
│   └── tareas.spec.ts
└── specs/            ← planes del planner
```

## Playwright MCP
```bash
claude mcp add playwright -- npx -y @playwright/mcp@latest [--isolated --headless --browser firefox]
```
Tools: `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_take_screenshot`, `browser_console_messages`…

## Test Agents
planner → `specs/*.md` · generator → `tests/*.spec.ts` · healer → repara tests (¡revisar diffs!). Regenerar tras actualizar Playwright.

## Python / .NET
```python
page.get_by_role("button", name="Añadir").click()
expect(page.get_by_text("Hola")).to_be_visible()
```
```csharp
await Page.GetByRole(AriaRole.Button, new() { Name = "Añadir" }).ClickAsync();
await Expect(Page.GetByText("Hola")).ToBeVisibleAsync();
```

## Anti-patrones
❌ `waitForTimeout` · ❌ `expect(await loc.isVisible()).toBe(true)` · ❌ selectores CSS/XPath frágiles · ❌ tests dependientes entre sí · ❌ commitear `playwright/.auth/`
