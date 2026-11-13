# 07.3 · Playwright con IA: Playwright MCP y Playwright Test Agents

## Objetivos

- Dar "ojos y manos" en el navegador a tu agente con **Playwright MCP**.
- Usar los **Playwright Test Agents** (🎭 planner, 🎭 generator, 🎭 healer) con Claude Code, OpenCode y VS Code.
- Flujo completo: explorar app → plan de pruebas → tests → mantenimiento automático.
- Revisar con criterio lo que generan los agentes.

---

## 1. Tres formas de usar Playwright con agentes

| Forma | Qué es | Cuándo |
|---|---|---|
| **Playwright MCP** | Servidor MCP que expone el navegador como tools (navegar, clicar, escribir, snapshot de accesibilidad, capturas) | Verificación visual/interactiva durante el desarrollo, exploración, depuración |
| **Playwright Test Agents** | Definiciones de agentes (planner/generator/healer) + servidor MCP de testing que Playwright genera en tu repo | Crear y mantener suites de Playwright Test |
| **Agente + CLI de Playwright** | El agente ejecuta `npx playwright test`, lee trazas, corrige | Siempre (es la base) |

> Playwright también ofrece `playwright-cli`, una interfaz de línea de comandos pensada para agentes que consume menos contexto que MCP en algunas tareas. Úsala si tu flujo es principalmente de terminal.

---

## 2. Playwright MCP

### 2.1 Cómo funciona
En lugar de capturas de píxeles, usa **snapshots del árbol de accesibilidad**: el agente "ve" la página como una lista estructurada de roles, nombres y referencias. Es rápido, determinista y barato en tokens. También puede tomar capturas cuando necesitas verificación visual.

### 2.2 Instalación en clientes
```bash
# Claude Code
claude mcp add playwright -- npx -y @playwright/mcp@latest
# Windows nativo
claude mcp add playwright -- cmd /c npx -y @playwright/mcp@latest
```
```jsonc
// OpenCode
{ "mcp": { "servers": { "playwright": { "type": "local", "command": ["npx", "-y", "@playwright/mcp@latest"] } } } }
```
```json
// VS Code (.vscode/mcp.json)
{ "servers": { "playwright": { "type": "stdio", "command": "npx", "args": ["-y", "@playwright/mcp@latest"] } } }
```

### 2.3 Opciones útiles (argumentos)
| Opción | Efecto |
|---|---|
| `--browser chrome\|firefox\|webkit\|msedge` | Navegador |
| `--headless` | Sin ventana (por defecto se ve el navegador) |
| `--isolated` | Perfil temporal en memoria (no guarda sesión) |
| `--storage-state ruta.json` | Cargar sesión autenticada |
| `--viewport-size 1280x720` | Tamaño |
| `--caps vision,pdf,...` | Capacidades adicionales (coordenadas, PDF…) |
| `--allowed-origins` / `--blocked-origins` | Restringir dominios (seguridad) |

Ejecuta `npx @playwright/mcp@latest --help` para la lista actual.

### 2.4 Tools principales (nombres orientativos)
`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_fill_form`, `browser_select_option`, `browser_press_key`, `browser_wait_for`, `browser_take_screenshot`, `browser_console_messages`, `browser_network_requests`, `browser_tabs`, `browser_close`.

### 2.5 Prompts de ejemplo
```text
Usa Playwright MCP para abrir http://localhost:5173/tareas, crear una tarea
"Probar MCP" con prioridad alta, completarla y verificar que aparece tachada.
Informa de cualquier error en la consola del navegador.
```
```text
Tras implementar el formulario, ábrelo con Playwright MCP, prueba envíos vacíos,
textos de 300 caracteres y caracteres especiales. Toma capturas de cada estado
y corrige lo que no cumpla la spec.
```
```text
Explora el flujo de registro con Playwright MCP y luego escribe un test de
Playwright Test (TypeScript) que reproduzca exactamente ese flujo usando
getByRole/getByLabel. Ejecútalo hasta que pase.
```

> ⚠️ **Seguridad:** un navegador controlado por el agente puede visitar páginas con *prompt injection*. Usa `--isolated`, restringe orígenes y no lo conectes a sesiones con datos sensibles.

---

## 3. Playwright Test Agents (Playwright 1.56+)

Playwright incluye tres agentes que pueden usarse por separado o encadenados:

| Agente | Entrada | Salida |
|---|---|---|
| 🎭 **planner** | Descripción de qué probar + test semilla | Plan de pruebas en Markdown en `specs/` |
| 🎭 **generator** | Un plan Markdown | Archivos de test Playwright, verificando selectores en vivo |
| 🎭 **healer** | Tests que fallan | Depura (trazas, snapshots) y repara los tests |

```
planner ──► specs/*.md ──► generator ──► tests/*.spec.ts ──► healer (cuando fallan)
```

Internamente cada agente es un conjunto de **instrucciones + herramientas MCP** (servidor `playwright-test`), no un binario aparte.

### 3.1 Inicializar
```bash
npm init playwright@latest          # si aún no tienes Playwright
npx playwright init-agents --loop=claude     # Claude Code
npx playwright init-agents --loop=opencode   # OpenCode
npx playwright init-agents --loop=vscode     # VS Code (Copilot, requiere VS Code 1.105+)
```

Con `--loop=claude` se crean, por ejemplo:
```
.claude/agents/playwright-test-planner.md
.claude/agents/playwright-test-generator.md
.claude/agents/playwright-test-healer.md
.mcp.json                 ← servidor "playwright-test" (npx playwright run-test-mcp-server)
tests/seed.spec.ts        ← test semilla
```
Con `--loop=vscode` las definiciones van a `.github/agents/*.agent.md`.

> 🔁 **Regenera las definiciones cada vez que actualices Playwright** (vuelve a ejecutar `init-agents` en el mismo PR que sube la versión de `@playwright/test`) y commitea los archivos.

### 3.2 El test semilla (`seed.spec.ts`)
El planner ejecuta primero este test para obtener una página lista (app arrancada, usuario autenticado, datos base). Personalízalo:

```ts
import { test, expect } from './fixtures';

test('seed', async ({ page }) => {
    // Deja la app en el estado inicial desde el que el planner explorará
    await page.goto('/tareas');
    await expect(page.getByRole('heading', { name: 'Mis tareas' })).toBeVisible();
});
```

### 3.3 Flujo completo en Claude Code
```text
> Usa el agente playwright-test-planner para crear un plan de pruebas del módulo
  de tareas: creación, edición, completar, filtros por prioridad y validaciones.
  Usa tests/seed.spec.ts como semilla.
```
Resultado: `specs/tareas.md` con escenarios, pasos y resultados esperados. **Revísalo** (¿faltan casos de error? ¿datos realistas?).

```text
> Usa el agente playwright-test-generator para generar los tests de la sección
  "Filtros por prioridad" de specs/tareas.md.
```
Resultado: `tests/tareas/filtros-por-prioridad.spec.ts`, con selectores comprobados contra la app real.

```text
> Ejecuta la suite. Usa el agente playwright-test-healer para reparar los tests que fallen.
```
El healer reproduce el fallo, inspecciona la traza/snapshot y edita el test (localizador cambiado, espera faltante…) hasta que pasa, o marca el test como omitido si cree que la funcionalidad está rota.

En OpenCode el flujo es igual, invocando los agentes generados en `.opencode/`.

### 3.4 Revisar lo que hace el healer (¡crítico!)
El healer arregla **tests**, no tu aplicación. Un test puede fallar porque **la app tiene un bug**. Antes de aceptar sus cambios:

- [ ] ¿El cambio adapta el test a un cambio **intencionado** de la UI?
- [ ] ¿O está ocultando un bug (cambió el resultado esperado, relajó una aserción, añadió `skip`)?
- [ ] ¿Se mantienen los localizadores accesibles (no pasó a CSS frágil)?
- [ ] ¿Sigue verificando lo mismo que el escenario de la spec?

Regla en `AGENTS.md`: *"El healer no puede cambiar resultados esperados ni omitir tests sin mi aprobación explícita."*

---

## 4. Integración con el resto del flujo

```
OpenSpec (escenarios WHEN/THEN)
        │
        ▼
planner (plan Markdown alineado con los escenarios)
        │
        ▼
generator (tests E2E) ──► CI (Playwright) ──► fallo ──► healer ──► revisión humana
        ▲
        │
Playwright MCP (verificación interactiva mientras implementas la UI)
```

Prompt de puente OpenSpec → planner:
```text
Usa playwright-test-planner. Basa el plan en los escenarios de
openspec/changes/agregar-paginacion/specs/tareas/spec.md: un escenario de plan
por cada Scenario. Semilla: tests/seed.spec.ts.
```

---

## 5. Buenas prácticas

1. **HTML accesible**: roles y labels correctos mejoran MCP, agentes y tests.
2. **Datos de test controlados**: entorno de test con datos sembrados o mocks; no producción.
3. **Seed estable**: si el seed es inestable, todo lo demás también.
4. **Planes revisados por humanos** antes de generar.
5. **Diffs del healer revisados** como cualquier PR.
6. **Regenera agentes al actualizar Playwright.**
7. **Limita el navegador del agente** (`--isolated`, orígenes permitidos).

---

## Errores comunes

- Aceptar todo lo que genera el planner sin añadir casos negativos.
- Dejar que el healer "arregle" tests que detectaron bugs reales.
- Olvidar regenerar los agentes tras actualizar Playwright.
- Usar Playwright MCP con el perfil personal del navegador.

## Ejercicios

1. Instala Playwright MCP en Claude Code y en OpenCode. Pide a cada uno que pruebe manualmente el flujo de crear tarea y te informe de errores de consola.
2. Ejecuta `npx playwright init-agents --loop=claude`, personaliza el seed y genera un plan para tu app.
3. Genera tests de una sección del plan con el generator y ejecútalos.
4. Cambia el texto de un botón en la app, deja que el healer repare el test y **evalúa** su cambio con la checklist 3.4. Luego introduce un bug real y comprueba qué hace el healer.
   - ✅ Éxito: distingues entre reparación legítima y ocultación de un bug.

## Checklist

- [ ] Uso Playwright MCP para verificar UI durante el desarrollo.
- [ ] Inicialicé y usé planner, generator y healer.
- [ ] Reviso críticamente los cambios del healer.
- [ ] Conecto escenarios OpenSpec con planes de prueba.

---

⬅️ [07.2](02-playwright-e2e-fundamentos.md) · ➡️ [08 · Proyecto integrador](../08-proyecto-integrador/01-proyecto-integrador.md)
