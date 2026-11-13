# 08 · Proyecto integrador: "TaskFlow" de principio a fin

## Objetivo

Construir una aplicación real aplicando **todo** lo aprendido: instrucciones, flujos, Claude Code/OpenCode, skills, subagentes, hooks, MCP (servidor y cliente), OpenSpec, pruebas unitarias y E2E con Playwright, y CI.

Tiempo estimado: 10–20 horas.

---

## 1. Qué vas a construir

**TaskFlow**: gestor de tareas con:
- **API** REST (elige: ASP.NET Core, FastAPI o Node/Express-Hono).
- **Web** SPA (React + Vite recomendado).
- **Servidor MCP** que expone la gestión de tareas a agentes (elige Python, Node o C#; idealmente reutilizando la API).
- **Suite de pruebas**: unitarias, componentes en navegador, integración y E2E.
- **CI** en GitHub Actions.

```
taskflow/
├── AGENTS.md
├── CLAUDE.md                 (opcional: @AGENTS.md + extras)
├── .claude/{settings.json, skills/, agents/, hooks/}
├── .opencode/{agents/, commands/}
├── opencode.json
├── .mcp.json
├── openspec/{config.yaml, specs/, changes/}
├── api/                      (backend + tests)
├── web/                      (frontend + tests unitarios/componentes)
├── mcp/                      (servidor MCP + tests)
├── e2e/                      (Playwright: tests/, specs/, seed.spec.ts)
└── .github/workflows/ci.yml
```

---

## 2. Fases y entregables

### Fase 0 · Preparación (módulos 01–02)
1. Crea el repo y la estructura base (puedes pedírselo al agente en plan mode).
2. Escribe `AGENTS.md` con la plantilla de [`plantillas/AGENTS.md`](../plantillas/AGENTS.md): stack, comandos, convenciones, reglas de testing y prohibiciones.
3. Configura permisos (`.claude/settings.json` y `opencode.json`) con mínimo privilegio.

**Entregable:** commit `chore: estructura inicial e instrucciones de agente`.

### Fase 1 · Extensibilidad (módulos 03–04)
1. Skill `crear-endpoint` (convenciones del backend).
2. Subagentes `code-reviewer` y `test-writer` (en Claude Code y OpenCode).
3. Hooks: formateo tras edición, protección de `.env`, tests verdes en `Stop`.
4. Comando `/fix-issue`.

**Entregable:** las extensiones funcionando; demuestra cada una en una sesión.

### Fase 2 · Primera feature con OpenSpec (módulo 06)
1. `openspec init` (Claude Code + OpenCode).
2. `/opsx:propose crud-tareas` → revisa y ajusta propuesta, specs (con escenarios WHEN/THEN), diseño y tareas.
3. `/opsx:apply` con TDD: tests primero para cada escenario.
4. `code-reviewer` revisa; corrige hallazgos.
5. `/opsx:archive`.

**Entregable:** CRUD de tareas en API + web, con tests unitarios e integración; spec archivada.

### Fase 3 · Servidor MCP (módulo 05)
1. `/opsx:propose servidor-mcp` para el servidor MCP (tools: `agregar_tarea`, `listar_tareas`, `completar_tarea`, `buscar_tareas`; resource `tareas://pendientes`; prompt `planificar_dia`).
2. Implementa con el SDK v2 de tu lenguaje. El servidor debe llamar a **tu API** (no a un archivo JSON).
3. Tests de integración con un cliente MCP real.
4. Regístralo en `.mcp.json` y `opencode.json` y úsalo desde ambos agentes.
5. **Bonus:** versión Streamable HTTP + agente propio (05.5) que planifica tu día.

**Entregable:** el agente gestiona tareas por lenguaje natural vía MCP.

### Fase 4 · Pruebas en navegador (módulo 07)
1. Vitest Browser Mode para 2–3 componentes clave.
2. Playwright: config con `webServer`, proyectos Chromium/Firefox/WebKit, auth setup, POM.
3. `npx playwright init-agents --loop=claude` (o `opencode`); planner a partir de las specs OpenSpec; generator para crear la suite; revisa todo.
4. Introduce un cambio de UI intencionado y uno con bug; evalúa al healer.
5. Usa Playwright MCP para verificar visualmente una pantalla nueva.

**Entregable:** suite E2E estable (≥ 8 tests) y plan en `e2e/specs/`.

### Fase 5 · CI y cierre
1. Workflow que ejecute: lint, tests unitarios (3 lenguajes si aplica), tests MCP, E2E con informe como artefacto.
2. (Opcional) revisión automática de PRs con la GitHub Action de Claude Code u OpenCode.
3. Feature final en paralelo: dos cambios OpenSpec en dos **worktrees** con dos sesiones de agente, integrados por PR.

**Entregable:** pipeline en verde y README del proyecto.

---

## 3. Ejemplo de workflow de CI

`.github/workflows/ci.yml`
```yaml
name: CI
on: [push, pull_request]

jobs:
  api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with: { dotnet-version: '10.0.x' }
      - run: dotnet test api --collect:"XPlat Code Coverage"

  mcp:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv run --directory mcp pytest -q

  web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22 }
      - run: npm ci --prefix web
      - run: npx --prefix web playwright install --with-deps chromium firefox
      - run: npm run --prefix web lint
      - run: npm run --prefix web test   # Vitest (incluye browser mode)

  e2e:
    runs-on: ubuntu-latest
    needs: [api, web]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22 }
      - uses: actions/setup-dotnet@v4
        with: { dotnet-version: '10.0.x' }
      - run: npm ci --prefix e2e
      - run: npx --prefix e2e playwright install --with-deps
      - run: npm --prefix e2e exec playwright test
      - uses: actions/upload-artifact@v4
        if: ${{ !cancelled() }}
        with: { name: playwright-report, path: e2e/playwright-report/ }
```
Adapta los comandos al stack que elijas.

---

## 4. Rúbrica de evaluación

| Criterio | Básico (1) | Bueno (2) | Excelente (3) |
|---|---|---|---|
| Instrucciones | `AGENTS.md` generado sin editar | Conciso, con comandos y reglas | + skills que descargan contexto, sin contradicciones |
| Flujo | Prompts sueltos | Plan antes de código | OpenSpec en todas las features + revisión humana documentada |
| Extensiones | Ninguna | Skill + subagente | Skill + subagentes + hooks + comandos en ambas herramientas |
| MCP | No funciona | Servidor stdio funcional | stdio + HTTP + tests + agente propio |
| Unit tests | Pocos, tautológicos | Cubren bordes y errores | + mutation testing + browser mode |
| E2E | Selectores frágiles | POM, localizadores accesibles | + Test Agents con revisión crítica + CI multi-navegador |
| Seguridad | Permisos amplios | Mínimo privilegio | + hooks de protección + sin secretos + MCP evaluados |
| CI | — | Tests en CI | Pipeline completo con artefactos |

**Objetivo:** ≥ 18 puntos de 24.

---

## 5. Retrospectiva (escríbela al terminar)

1. ¿Qué tareas delegaste con más éxito? ¿Cuáles no?
2. ¿Qué reglas añadiste a `AGENTS.md` durante el proyecto y por qué?
3. ¿Cuántas veces el agente intentó "trampas" en los tests? ¿Cómo lo detectaste?
4. Claude Code vs OpenCode: ¿cuándo preferiste cada uno?
5. ¿Qué convertirías en skill, subagente o plugin para tu próximo proyecto?

Guarda la retrospectiva en `docs/retrospectiva.md`: es tu conocimiento destilado.

---

⬅️ [07.3](../07-testing/03-playwright-con-ia-mcp-y-test-agents.md) · ➡️ [09.1 · Aislamiento serio](../09-avanzado/01-aislamiento-sandbox-devcontainers-docker.md) · 🏠 [Índice](../README.md)
