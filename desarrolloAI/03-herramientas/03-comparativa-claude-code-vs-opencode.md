# 03.3 · Comparativa: Claude Code vs OpenCode

## Objetivo

Tener una referencia lado a lado para trabajar con ambos y decidir cuál usar en cada situación (o cómo compartir configuración entre ellos).

---

## 1. Tabla general

| Aspecto | Claude Code | OpenCode |
|---|---|---|
| Licencia | Propietario (Anthropic) | Open source |
| Modelos | Familia Claude (Opus, Sonnet, Haiku; también vía Bedrock, Vertex, Foundry) | Multi-proveedor: Anthropic, OpenAI, Google, OpenRouter, locales, OpenCode Go/Console… |
| Interfaces | Terminal, VS Code/JetBrains, escritorio, web, móvil | TUI, escritorio, web (`opencode pair`) |
| Instrucciones | `CLAUDE.md` (y `AGENTS.md` si no hay `CLAUDE.md`) | `AGENTS.md` (+ `instructions` en config) |
| Generar instrucciones | `/init` | `/init` |
| Modo solo lectura | **Plan mode** (`Shift+Tab`) | Agente **plan** (`Tab`) |
| Subagentes integrados | Explore, Plan, general-purpose… | explore, general |
| Subagentes propios | `.claude/agents/*.md` | `.opencode/agents/*.md` o `agents` en JSON |
| Skills | `.claude/skills/<n>/SKILL.md` | `.opencode/skills/` **+ lee `.claude/skills/` y `.agents/skills/`** |
| Comandos propios | Skills (o `.claude/commands/*.md`, compatible) | `.opencode/commands/*.md` |
| Hooks | Sí, muchos eventos (`PreToolUse`, `PostToolUse`, `Stop`, …) | Mediante **plugins** (JS/TS) que se suscriben a eventos |
| Plugins | Plugins + marketplaces (`/plugin`) | Plugins JS/TS |
| Permisos | `allow`/`ask`/`deny` con patrones tipo `Bash(npm test:*)` | Lista ordenada `{action, resource, effect}`; gana la última |
| MCP config | `.mcp.json` / `claude mcp add` | `mcp.servers` en `opencode.json` / `opencode mcp add` |
| Variables en MCP | `${VAR}` | `{env:VAR}` |
| Deshacer | Checkpoints: `Esc Esc` / `/rewind` | `/undo` / `/redo` |
| Headless | `claude -p "..."` | `opencode run "..."` |
| SDK | Claude Agent SDK (Python/TS) | SDK cliente + servidor HTTP |
| CI | GitHub Action oficial | GitHub Action / CLI |

---

## 2. Equivalencias rápidas de tareas

| Quiero… | Claude Code | OpenCode |
|---|---|---|
| Planificar sin editar | `Shift+Tab` → plan | `Tab` → plan |
| Cambiar modelo | `/model` | `/models` |
| Limpiar contexto | `/clear` | `/new` |
| Compactar | `/compact` | `/compact` |
| Ver MCP | `/mcp` | `/mcps` |
| Añadir MCP stdio | `claude mcp add nombre -- npx -y paquete` | `mcp.servers.nombre = {type:"local", command:[...]}` |
| Añadir MCP remoto | `claude mcp add --transport http nombre URL` | `{type:"remote", url:"..."}` |
| Crear subagente | archivo en `.claude/agents/` | archivo en `.opencode/agents/` con `mode: subagent` |
| Comando `/deploy` | `.claude/skills/deploy/SKILL.md` | `.opencode/commands/deploy.md` |
| Retomar sesión | `claude --continue` / `--resume` | `/sessions` |

---

## 3. ¿Cuál elegir?

**Elige Claude Code si…**
- Usas principalmente modelos Claude y quieres la integración más pulida con ellos.
- Necesitas hooks deterministas ricos, plugins/marketplaces, modo auto, sandbox, integración IDE/escritorio/web.
- Trabajas en una organización con políticas gestionadas.

**Elige OpenCode si…**
- Quieres libertad de proveedor (comparar modelos, usar modelos locales, optimizar costes).
- Prefieres software open source y auditable.
- Quieres un servidor de agente al que conectar distintas interfaces.

**Usa ambos** (muy común): el mismo repo con `AGENTS.md` + skills en `.claude/skills/` funciona en los dos. Por ejemplo: Claude Code para trabajo diario y OpenCode para probar otro modelo como **revisor** (patrón escritor–revisor con modelos distintos).

---

## 4. Configuración compartida en un mismo repo

```
mi-repo/
├── AGENTS.md                  ← instrucciones comunes (ambos)
├── CLAUDE.md                  ← opcional: "@AGENTS.md" + extras de Claude
├── .claude/
│   ├── settings.json          ← permisos y hooks de Claude Code
│   ├── skills/                ← skills: las leen Claude Code y OpenCode
│   └── agents/                ← subagentes de Claude Code
├── .opencode/
│   ├── agents/                ← agentes de OpenCode
│   └── commands/              ← comandos de OpenCode
├── .mcp.json                  ← MCP para Claude Code
└── opencode.json              ← config de OpenCode (incluye MCP)
```

> Los subagentes **no** son intercambiables directamente (frontmatter distinto: `tools` vs `permissions`, nombres de modelo). Mantén el *cuerpo* (prompt) igual y adapta el frontmatter. Las plantillas de este repositorio traen ambas versiones.

---

## Ejercicio

Elige una tarea mediana y hazla en las dos herramientas con el mismo `AGENTS.md`. Completa esta tabla:

| Métrica | Claude Code | OpenCode |
|---|---|---|
| Tiempo total | | |
| Nº de correcciones que tuviste que pedir | | |
| Calidad del plan (1–5) | | |
| Calidad del código (1–5) | | |
| Coste aproximado | | |

---

⬅️ [03.2](02-opencode.md) · ➡️ [04.1 · Skills](../04-extensibilidad/01-skills.md)
