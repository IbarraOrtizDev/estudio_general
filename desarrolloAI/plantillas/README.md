# Plantillas reutilizables

Copia lo que necesites a la raíz de tu proyecto y sustituye los `<marcadores>`.

> ℹ️ Copia la carpeta `claude-code/.claude/` a la raíz de tu proyecto (conservando el nombre `.claude`). Ejemplo en PowerShell:
> `Copy-Item -Recurse plantillas\claude-code\.claude C:\ruta\mi-proyecto\.claude`

| Archivo | Destino en tu proyecto | Módulo |
|---|---|---|
| [`AGENTS.md`](AGENTS.md) | `AGENTS.md` | 01.3 |
| [`CLAUDE.md`](CLAUDE.md) | `CLAUDE.md` (opcional) | 01.3 |
| [`claude-code/.claude/settings.json`](claude-code/.claude/settings.json) | `.claude/settings.json` | 02.2, 03.1, 04.3 |
| [`claude-code/.claude/hooks/`](claude-code/.claude/hooks/) | `.claude/hooks/` | 04.3 |
| [`claude-code/.claude/skills/`](claude-code/.claude/skills/) | `.claude/skills/` (también las lee OpenCode) | 04.1 |
| [`claude-code/.claude/agents/`](claude-code/.claude/agents/) | `.claude/agents/` | 04.2 |
| [`opencode/opencode.jsonc`](opencode/opencode.jsonc) | `opencode.jsonc` | 03.2 |
| [`opencode/.opencode/agents/`](opencode/.opencode/agents/) | `.opencode/agents/` | 04.2 |
| [`opencode/.opencode/commands/`](opencode/.opencode/commands/) | `.opencode/commands/` | 04.3 |
| [`mcp/claude-code.mcp.json`](mcp/claude-code.mcp.json) | `.mcp.json` | 05.6 |
| [`mcp/vscode.mcp.json`](mcp/vscode.mcp.json) | `.vscode/mcp.json` | 05.6 |
| [`mcp/claude_desktop_config.json`](mcp/claude_desktop_config.json) | config de Claude Desktop | 05.6 |
| [`openspec/changes/nombre-del-cambio/`](openspec/changes/nombre-del-cambio/) | referencia de formato OpenSpec | 06.1 |
| [`playwright/`](playwright/) | `playwright.config.ts`, `tests/` | 07.2, 07.3 |

> En Windows, la carpeta `.claude` puede quedar oculta en el Explorador: actívala en *Vista → Elementos ocultos*.
> Los hooks usan `python3`; en Windows cámbialo por `python` o `py` si es necesario.
