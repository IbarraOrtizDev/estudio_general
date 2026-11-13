# 01.3 · Context engineering e instrucciones (`CLAUDE.md`, `AGENTS.md`, rules)

## Objetivos

- Aplicar *context engineering*: dar al agente el contexto justo, ni más ni menos.
- Escribir archivos de instrucciones de proyecto efectivos.
- Entender la jerarquía de instrucciones en Claude Code y OpenCode.
- Escribir buenos *prompts* de tarea.

---

## 1. De *prompt engineering* a *context engineering*

*Prompt engineering* = redactar bien una petición. *Context engineering* = diseñar **todo lo que el agente ve**: instrucciones persistentes, archivos relevantes, herramientas disponibles, skills, specs, ejemplos y feedback de verificación.

Principios:

1. **Persistente vs. puntual**: lo que aplica siempre va en `AGENTS.md`/`CLAUDE.md`; lo que aplica a una tarea va en el prompt; lo que aplica a veces va en una **skill**.
2. **Conciso y accionable**: el archivo de instrucciones se carga en *cada* sesión. Cada línea cuesta tokens y atención.
3. **Específico**: "usa `pnpm`, no `npm`" es mejor que "usa buenas prácticas".
4. **Verificable**: incluye los comandos exactos de build/test/lint.
5. **Vivo**: cuando el agente se equivoca dos veces en lo mismo, añade una regla.

---

## 2. Archivos de instrucciones: quién lee qué

| Archivo | Leído por | Notas |
|---|---|---|
| `AGENTS.md` | **Estándar abierto** leído por +30 herramientas: OpenCode, Codex, Copilot, Cursor, Windsurf… y **Claude Code** (desde v2.1.277, si no hay `CLAUDE.md`) | Recomendado como fuente única compartida |
| `CLAUDE.md` | Claude Code | Si existe, Claude Code lo usa en lugar de `AGENTS.md` (configurable en `/config` → *Project instructions*) |
| `CLAUDE.local.md` | Claude Code | Preferencias personales del proyecto (añádelo a `.gitignore`) |
| `~/.claude/CLAUDE.md` | Claude Code | Preferencias globales personales |
| `.claude/rules/*.md` | Claude Code | Reglas modulares (pueden limitarse por rutas) |
| `~/.config/opencode/AGENTS.md` | OpenCode | Reglas globales personales |
| `instructions` en `opencode.json` | OpenCode | Lista de archivos/globs extra a incluir |

### Estrategia recomendada para equipos que usan ambas herramientas

**Opción A (más simple):** solo `AGENTS.md`. Claude Code lo leerá automáticamente si no hay `CLAUDE.md`.

**Opción B (necesitas cosas específicas de Claude):** `AGENTS.md` con lo común + un `CLAUDE.md` mínimo que lo importe:

```markdown
<!-- CLAUDE.md -->
@AGENTS.md

## Específico de Claude Code
- Usa el subagente `code-reviewer` antes de proponer un commit.
```

**Opción C:** en `/config` de Claude Code, *Project instructions* → `claude-md-and-agents-md` para cargar ambos.

> Comprueba qué se cargó con `/memory` en Claude Code.

### Jerarquía y monorepos

Ambas herramientas buscan archivos de instrucciones en el directorio actual y sus padres; Claude Code además carga los de subdirectorios cuando trabaja con archivos dentro de ellos. En monorepos:

```
repo/
├── AGENTS.md              ← reglas globales del repo
├── apps/web/AGENTS.md     ← reglas del frontend
└── services/api/AGENTS.md ← reglas del backend (.NET)
```

---

## 3. Qué poner en `AGENTS.md` / `CLAUDE.md`

Estructura recomendada (plantilla completa en [`plantillas/AGENTS.md`](../plantillas/AGENTS.md)):

```markdown
# Proyecto: Gestor de Tareas

## Resumen
API REST (ASP.NET Core 10) + SPA (React 19 + Vite) + servidor MCP (Python).

## Comandos
- Instalar: `pnpm install` · `dotnet restore`
- Dev: `pnpm dev` (web en :5173) · `dotnet run --project services/api` (:5000)
- Tests unitarios: `pnpm test` · `dotnet test` · `uv run pytest`
- E2E: `pnpm exec playwright test`
- Lint/format: `pnpm lint` · `dotnet format`

## Arquitectura
- `apps/web`: UI. Estado con TanStack Query. NO usar Redux.
- `services/api`: Clean Architecture (Domain / Application / Infrastructure / Api).
- `mcp/`: servidor MCP con SDK `mcp` 2.x (`MCPServer`).

## Convenciones
- TypeScript estricto; prohibido `any`.
- C#: nullable habilitado, `async` de punta a punta, sufijo `Async`.
- Commits: Conventional Commits en español (`feat: añade paginación`).

## Flujo de trabajo obligatorio
1. Antes de cambiar código, lee los tests existentes del módulo.
2. Escribe/actualiza tests primero cuando arregles un bug.
3. Ejecuta tests y lint antes de declarar una tarea terminada.

## Prohibido
- Tocar `infra/prod/**`.
- Commitear `.env` o secretos.
- Desactivar tests para que "pasen".
```

### Qué **no** poner

- Documentación extensa (enlázala o conviértela en **skill**).
- Reglas que un linter ya impone (configura el linter + un hook).
- Información obvia que el agente deduce leyendo el código.
- Secretos o URLs internas sensibles.

> 💡 Usa `/init` (Claude Code y OpenCode) para generar un primer borrador analizando el repo, y luego **edítalo a mano**: quita lo genérico y añade lo que solo tú sabes.

---

## 4. Anatomía de un buen prompt de tarea

Fórmula **C-O-R-V** (Contexto, Objetivo, Restricciones, Verificación):

```text
Contexto: En services/api, el endpoint GET /tareas devuelve todas las tareas.
Con 10k registros tarda 4 s.

Objetivo: Añadir paginación por cursor (parámetros `cursor` y `limit`, máx 100).

Restricciones:
- Mantén compatibilidad: sin parámetros, devuelve los primeros 50.
- Sigue el patrón de TareasRepository; no añadas dependencias nuevas.
- No modifiques el esquema de base de datos.

Verificación:
- Añade tests en TareasEndpointTests para: sin parámetros, con cursor, límite > 100.
- `dotnet test` debe pasar y `dotnet format --verify-no-changes` no debe dar errores.
Primero muéstrame un plan; no edites hasta que lo apruebe.
```

### Técnicas que funcionan

| Técnica | Ejemplo |
|---|---|
| Referenciar archivos con `@` | `Revisa @src/auth/login.ts y @tests/auth.test.ts` |
| Pedir plan primero | "Piensa a fondo y propón un plan; no edites aún" |
| Dar ejemplos | "Sigue el estilo de `UsuariosController.cs`" |
| Imágenes | Pegar captura de un diseño o de un error de UI |
| Criterios de "terminado" | "Termina cuando los 3 tests nuevos pasen" |
| Pedir preguntas | "Si algo es ambiguo, pregúntame antes de asumir" |
| Limitar alcance | "Solo toca archivos dentro de `src/pagos/`" |

---

## 5. Otras fuentes de contexto

- **Skills** (módulo 04.1): conocimiento procedimental cargado bajo demanda.
- **MCP** (módulo 05): documentación viva, tickets, bases de datos, navegador.
- **Specs OpenSpec** (módulo 06): requisitos acordados y versionados.
- **Memoria automática**: Claude Code puede guardar aprendizajes por proyecto; revísalos con `/memory`.

---

## Errores comunes

- `AGENTS.md` de 800 líneas generado y nunca revisado.
- Instrucciones contradictorias entre `CLAUDE.md` y `AGENTS.md`.
- Escribir reglas en tono vago ("intenta", "si puedes").
- No incluir los comandos de test → el agente no verifica.

## Ejercicios

1. Ejecuta `/init` en un repo propio. Reduce el resultado a **menos de 80 líneas** sin perder información crítica.
   - ✅ Éxito: contiene comandos exactos, arquitectura, convenciones y prohibiciones.
2. Reescribe con la fórmula C-O-R-V tres peticiones que hayas hecho recientemente a una IA.
3. Prueba la opción B (`CLAUDE.md` con `@AGENTS.md`) y verifica con `/memory` que ambos se cargan.

## Checklist

- [ ] Tengo un `AGENTS.md` (y opcionalmente `CLAUDE.md`) conciso y verificable.
- [ ] Sé qué va en instrucciones, qué en skills y qué en el prompt.
- [ ] Escribo prompts con contexto, objetivo, restricciones y verificación.

---

⬅️ [01.2](02-llms-contexto-y-tokens.md) · ➡️ [02.1 · Flujos de trabajo agénticos](../02-flujos-de-trabajo/01-flujos-de-trabajo-agenticos.md)
