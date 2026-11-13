# Cheatsheet · OpenCode 2.x

## Instalación y arranque
```bash
curl -fsSL https://opencode.ai/install | bash   # ver opencode.ai/docs (Windows: binario standalone o WSL)
opencode --version
opencode                     # TUI
opencode run "prompt"        # sin TUI
opencode --standalone        # servidor privado
opencode pair                # enlazar web/app
opencode upgrade --major     # de 1.x a 2.x
```

## En la TUI
| Entrada | Efecto |
|---|---|
| `Tab` | Alternar agentes primarios (build ↔ plan) |
| `@archivo` / `@skill-id` | Adjuntar archivo / cargar skill |
| `!cmd` | Shell |
| `/init` | Crear/actualizar AGENTS.md |
| `/connect` `/models` | Proveedor y modelo |
| `/undo` `/redo` | Deshacer/rehacer |
| `/compact` `/new` `/sessions` | Contexto y sesiones |
| `/mcps` `/share` `/help` | MCP, compartir, ayuda |

## Archivos
| Ruta | Para qué |
|---|---|
| `AGENTS.md` | Instrucciones (no lee CLAUDE.md) |
| `opencode.json(c)` / `.opencode/opencode.json(c)` | Config del proyecto |
| `~/.config/opencode/opencode.json(c)` | Config global |
| `.opencode/agents/<n>.md` | Agentes |
| `.opencode/commands/<n>.md` | Comandos `/n` |
| `.opencode/skills/` + `.claude/skills/` + `.agents/skills/` | Skills |
| `.opencode/plugins/` | Plugins JS/TS |

## Permisos V2
```jsonc
"permissions": [
  { "action": "shell", "resource": "*", "effect": "ask" },
  { "action": "shell", "resource": "git status *", "effect": "allow" },
  { "action": "shell", "resource": "git push *", "effect": "deny" }
]
```
Acciones: `read`, `edit`, `glob`, `grep`, `shell`, `subagent`, `skill`, `webfetch`, `websearch`, `external_directory`, `<servidor>_<tool>`.
Gana la **última** regla que coincide. Sin coincidencia → `ask`.

## MCP V2
```jsonc
"mcp": { "servers": {
  "local":  { "type": "local",  "command": ["npx", "-y", "pkg"], "environment": { "K": "{env:K}" } },
  "remoto": { "type": "remote", "url": "https://x/mcp", "headers": { "Auth": "{env:TOKEN}" } }
} }
```
CLI: `opencode mcp add` · `opencode mcp auth <n>` · `opencode mcp debug <n>`

## Agente (Markdown)
```markdown
---
description: Qué hace y cuándo
mode: subagent        # primary | subagent | all
model: anthropic/claude-sonnet-5-5
permissions:
  - { action: edit, resource: "*", effect: deny }
---
Prompt del agente…
```

## Comando
```markdown
---
description: ...
agent: plan
---
Revisa $ARGUMENTS ($1, $2…). Salida de shell: !`git diff --stat`
```

## V1 → V2
`permission`→`permissions[]` · `agent`/`mode`→`agents` · `bash`→`shell` · `task`→`subagent` · `write`/`patch`→`edit` · `mcp.<n>`→`mcp.servers.<n>` · `autoshare`→`share`
