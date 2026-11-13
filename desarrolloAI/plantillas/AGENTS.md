# Proyecto: <NOMBRE>

> Instrucciones para agentes de IA (Claude Code, OpenCode, Codex, Copilot…).
> Mantener por debajo de ~100 líneas. Lo que aplique "a veces" va en skills.

## Resumen
<Una o dos frases: qué es y para quién.>
Stack: <p. ej. ASP.NET Core 10 · React 19 + Vite · PostgreSQL · servidor MCP en Python (mcp 2.x)>

## Comandos
- Instalar: `<pnpm install>` · `<dotnet restore>` · `<uv sync>`
- Desarrollo: `<pnpm dev>` (web :5173) · `<dotnet run --project api>` (api :5000)
- Tests unitarios: `<pnpm test>` · `<dotnet test>` · `<uv run pytest>`
- E2E: `<pnpm exec playwright test>`
- Lint/format: `<pnpm lint>` · `<dotnet format>` · `<uv run ruff check>`
- Type-check: `<pnpm typecheck>`

## Arquitectura
- `api/`: <capas y responsabilidades>
- `web/`: <estructura, gestión de estado, librerías obligatorias>
- `mcp/`: <servidor MCP y qué expone>
- Documentación de diseño: `docs/` · Specs: `openspec/specs/`

## Convenciones
- <Lenguaje>: <reglas no impuestas por el linter>
- Nombres: <convenciones>
- Commits: Conventional Commits en español (`feat:`, `fix:`, `test:`, `docs:`…)
- Ramas: `feat/<tema>`, `fix/<tema>`

## Flujo de trabajo
1. Para tareas no triviales: explora y propone un plan antes de editar.
2. Cambios grandes: usa OpenSpec (`/opsx:propose`).
3. Bugs: primero un test que reproduzca el fallo.
4. Antes de terminar: tests + lint + type-check en verde.

## Reglas de testing
- Nunca modifiques, borres ni omitas (skip/only) tests existentes sin permiso explícito.
- Valores esperados literales; no recalcules con la lógica del código.
- Cubre caso feliz, bordes y errores. Patrón Arrange-Act-Assert.
- E2E: localizadores accesibles (`getByRole`, `getByLabel`); nunca `waitForTimeout`.

## Seguridad
- Nunca leas ni muestres `.env*` ni `secrets/**`.
- No añadas dependencias sin justificarlo en el PR.
- Valida toda entrada externa. Sin SQL concatenado.

## Prohibido
- Tocar `<infra/prod/**>`.
- `git push --force`, reescribir historial de `main`.
- Commitear secretos o datos personales.
