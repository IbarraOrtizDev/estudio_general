# Cheatsheet · Claude Code

## Instalación
```bash
curl -fsSL https://claude.ai/install.sh | bash      # macOS/Linux/WSL
irm https://claude.ai/install.ps1 | iex             # Windows PowerShell
npm install -g @anthropic-ai/claude-code            # alternativa
claude doctor
```

## Arranque
| Comando | Efecto |
|---|---|
| `claude` | Sesión interactiva |
| `claude "prompt"` | Sesión con prompt inicial |
| `claude -p "prompt"` | Headless (una respuesta) |
| `claude -p ... --output-format json\|stream-json` | Salida para scripts |
| `claude --continue` / `--resume` | Continuar última / elegir sesión |
| `claude --permission-mode plan` | Empezar en plan mode |
| `claude --model opus` | Elegir modelo |
| `claude --allowedTools "Edit" "Bash(npm test:*)"` | Herramientas permitidas |
| `claude --plugin-dir ./mi-plugin` | Probar un plugin local |

## En la sesión
| Entrada | Efecto |
|---|---|
| `@archivo` | Mencionar archivo |
| `!cmd` | Ejecutar shell |
| `Shift+Tab` | default → accept edits → plan (→ auto) |
| `Esc` / `Esc Esc` | Interrumpir / rewind |
| `/init` `/memory` `/config` | Instrucciones y configuración |
| `/clear` `/compact` `/context` | Gestión de contexto |
| `/model` `/permissions` | Modelo y permisos |
| `/mcp` `/agents` `/hooks` `/plugin` | Extensiones |
| `/rewind` `/resume` | Checkpoints y sesiones |
| `/help` | Ayuda |

## MCP
```bash
claude mcp add <n> -- <comando> [args]                 # stdio
claude mcp add <n> --env K=V -- <comando>
claude mcp add --transport http <n> <url> [--header "K: V"]
claude mcp add --scope project|user|local ...
claude mcp list | get <n> | remove <n>
```
Tools: `mcp__<servidor>__<tool>` · Prompts: `/mcp__<servidor>__<prompt>`

## Archivos
| Ruta | Para qué |
|---|---|
| `CLAUDE.md` / `AGENTS.md` | Instrucciones (AGENTS.md si no hay CLAUDE.md) |
| `CLAUDE.local.md` | Personal (gitignore) |
| `.claude/settings.json` / `.local.json` | Permisos, hooks, env |
| `.claude/skills/<n>/SKILL.md` | Skills y comandos `/n` |
| `.claude/agents/<n>.md` | Subagentes |
| `.mcp.json` | MCP del proyecto |
| `~/.claude/...` | Equivalentes globales |

## Permisos (settings.json)
```json
{ "permissions": { "allow": ["Bash(npm test:*)"], "ask": ["Bash(git push:*)"], "deny": ["Read(./.env*)"] } }
```

## Hooks
Eventos clave: `SessionStart`, `UserPromptSubmit`, `PreToolUse` (bloquea), `PostToolUse`, `Stop`, `SubagentStop`, `PreCompact`, `SessionEnd`.
Exit `0` = continuar · `2` = bloquear (stderr → Claude) · otro = aviso.

## Subagente mínimo
```markdown
---
name: revisor
description: Revisa cambios antes de commit. Úsalo proactivamente.
tools: Read, Grep, Glob, Bash
model: sonnet
---
Instrucciones…
```

## Skill mínima
```markdown
---
name: mi-skill
description: Qué hace y cuándo usarla.
disable-model-invocation: false
---
Pasos… ($ARGUMENTS)
```
