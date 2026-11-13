# 04.3 · Hooks, comandos y plugins

## Objetivos

- Usar **hooks** para automatizar y garantizar comportamientos deterministas.
- Crear **comandos** personalizados en Claude Code y OpenCode.
- Empaquetar todo en **plugins** y distribuirlos con marketplaces.

---

## 1. Hooks en Claude Code

Un **hook** es un comando (u otra acción) que Claude Code ejecuta automáticamente en un punto del ciclo de vida. A diferencia de las instrucciones, **siempre se ejecuta**.

### Eventos más usados
| Evento | Cuándo | Usos típicos |
|---|---|---|
| `SessionStart` | Al iniciar/reanudar sesión | Cargar contexto (rama, issues abiertos) |
| `UserPromptSubmit` | Al enviar un prompt | Añadir contexto, bloquear prompts con secretos |
| `PreToolUse` | Antes de ejecutar una herramienta (**puede bloquear**) | Proteger archivos, bloquear comandos peligrosos |
| `PermissionRequest` | Cuando se necesita decisión de permiso | Auto-aprobar/denegar según política |
| `PostToolUse` | Tras una herramienta exitosa | Formatear, lint, ejecutar tests relacionados |
| `Notification` | Cuando Claude notifica (p. ej. espera input) | Notificación de escritorio |
| `SubagentStart` / `SubagentStop` | Al lanzar/terminar subagentes | Logging, métricas |
| `Stop` | Cuando Claude termina de responder | Verificar que los tests pasan antes de "terminar" |
| `PreCompact` / `PostCompact` | Alrededor de la compactación | Guardar resúmenes |
| `SessionEnd` | Al cerrar sesión | Limpieza, informes |

> Hay muchos más (`PostToolUseFailure`, `InstructionsLoaded`, `FileChanged`, `WorktreeCreate`, `Elicitation`, `TaskCompleted`…). Consulta la referencia oficial de hooks.

### Estructura
En `~/.claude/settings.json`, `.claude/settings.json` o `.claude/settings.local.json`:
```json
{
  "hooks": {
    "NombreEvento": [
      {
        "matcher": "Herramienta|OtraHerramienta",
        "hooks": [
          { "type": "command", "command": "script o comando", "timeout": 30 }
        ]
      }
    ]
  }
}
```
- `matcher`: nombre exacto (`Bash`), alternativas (`Edit|Write`) o regex (`mcp__github__.*`). Vacío o `*` = todo.
- Tipos de handler: `command`, `http`, `mcp_tool`, `prompt` (evaluación con un LLM), `agent`.
- `if`: filtro con sintaxis de permisos, p. ej. `"Bash(rm *)"`.
- El hook recibe un **JSON por stdin** (sesión, herramienta, `tool_input`…).

### Códigos de salida
| Código | Efecto |
|---|---|
| `0` | Continúa. Si stdout es un objeto JSON, se interpreta (decisiones, contexto adicional) |
| `2` | **Bloquea** (en eventos bloqueables). stderr se envía a Claude como motivo |
| otro | Error no bloqueante; se muestra un aviso |

### Ejemplo 1 · Formatear tras cada edición (PostToolUse)
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs -I {} npx prettier --write {}"
          }
        ]
      }
    ]
  }
}
```

### Ejemplo 2 · Proteger archivos (PreToolUse, Python multiplataforma)
`.claude/hooks/proteger_archivos.py`
```python
#!/usr/bin/env python3
import json
import sys

PROTEGIDOS = (".env", "package-lock.json", "infra/prod/", ".git/")

datos = json.load(sys.stdin)
ruta = datos.get("tool_input", {}).get("file_path", "")

if any(p in ruta for p in PROTEGIDOS):
    print(f"Bloqueado: '{ruta}' está protegido. Pide confirmación al usuario.", file=sys.stderr)
    sys.exit(2)  # bloquea la herramienta

sys.exit(0)
```
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/proteger_archivos.py\"" }]
      }
    ]
  }
}
```

### Ejemplo 3 · Decisión estructurada: denegar `rm -rf`
```bash
#!/bin/bash
# .claude/hooks/block-rm.sh  (requiere jq)
COMMAND=$(jq -r '.tool_input.command')
if echo "$COMMAND" | grep -q 'rm -rf'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse",
          permissionDecision: "deny",
          permissionDecisionReason: "Comando destructivo bloqueado por hook"}}'
else
  exit 0
fi
```
```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [{ "type": "command", "if": "Bash(rm *)",
                    "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-rm.sh" }] }
    ]
  }
}
```

### Ejemplo 4 · No terminar con tests rojos (Stop)
```python
#!/usr/bin/env python3
# .claude/hooks/tests_antes_de_parar.py
import json, subprocess, sys

datos = json.load(sys.stdin)
if datos.get("stop_hook_active"):      # evita bucles infinitos
    sys.exit(0)

r = subprocess.run(["npm", "test", "--silent"], capture_output=True, text=True)
if r.returncode != 0:
    print("Los tests fallan. Corrígelos antes de terminar:\n" + r.stdout[-3000:], file=sys.stderr)
    sys.exit(2)   # Claude continúa trabajando con este feedback
sys.exit(0)
```

> 🪟 **Windows:** escribe hooks en Python o PowerShell (`"shell": "powershell"` donde aplique) o trabaja en WSL; evita depender de herramientas POSIX si tu equipo usa Windows nativo.

### Depuración
- `/hooks` para ver los hooks activos.
- Prueba el script a mano: `echo '{"tool_input":{"file_path":".env"}}' | python3 .claude/hooks/proteger_archivos.py; echo $?`

---

## 2. Hooks en OpenCode: plugins

OpenCode implementa la automatización mediante **plugins** en JavaScript/TypeScript que se suscriben a eventos (antes/después de herramientas, eventos de sesión, etc.). Se colocan en `.opencode/plugins/` (proyecto) o `~/.config/opencode/plugins/` (global), o se instalan desde npm vía configuración.

Ejemplo (estilo de la API de plugins; verifica nombres de eventos en la documentación de tu versión):
```ts
// .opencode/plugins/proteger-env.ts
import type { Plugin } from "@opencode-ai/plugin";

export const ProtegerEnv: Plugin = async ({ project, $ }) => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool === "read" && String(output.args.filePath).includes(".env")) {
        throw new Error("Lectura de .env bloqueada por política del proyecto");
      }
    },
  };
};
```
> Para bloqueos simples, prefiere **reglas de `permissions`** (más declarativas). Usa plugins para lógica (formatear, notificar, integrar herramientas).

---

## 3. Comandos personalizados

### Claude Code: comandos = skills
`.claude/skills/fix-issue/SKILL.md` (o el formato clásico `.claude/commands/fix-issue.md`):
```markdown
---
description: Analiza y arregla un issue de GitHub
argument-hint: "[numero]"
disable-model-invocation: true
allowed-tools: Bash(gh issue view *) Bash(gh pr create *)
---

Arregla el issue #$ARGUMENTS:

!`gh issue view $ARGUMENTS`

1. Entiende el problema y localiza el código.
2. Escribe un test que lo reproduzca.
3. Arréglalo y ejecuta la suite.
4. Crea un commit y un PR que referencie el issue.
```
Uso: `/fix-issue 123`.

### OpenCode
`.opencode/commands/fix-issue.md`:
```markdown
---
description: Analiza y arregla un issue de GitHub
agent: build
---

Arregla el issue #$1:

!`gh issue view $1`

1. Entiende el problema y localiza el código.
2. Escribe un test que lo reproduzca.
3. Arréglalo y ejecuta la suite.
```

### Comandos útiles para tener en todos tus repos
| Comando | Qué hace |
|---|---|
| `/plan-feature` | Explora y escribe un plan en `docs/plans/` sin editar código |
| `/fix-issue <n>` | Flujo completo de arreglo de issue |
| `/review` | Revisión del diff con checklist |
| `/test <ruta>` | Genera/actualiza tests de un módulo |
| `/release <tipo>` | Changelog + versión |
| `/explain <ruta>` | Explicación didáctica de un archivo |

---

## 4. Plugins de Claude Code

Un **plugin** empaqueta skills, subagentes, comandos, hooks y servidores MCP para compartirlos.

### Estructura
```
mi-plugin/
├── .claude-plugin/
│   └── plugin.json         ← manifiesto
├── skills/
│   └── crear-endpoint/SKILL.md
├── agents/
│   └── code-reviewer.md
├── commands/
│   └── release.md
├── hooks/
│   └── hooks.json
└── .mcp.json
```

`.claude-plugin/plugin.json`:
```json
{
  "name": "equipo-dotnet",
  "description": "Skills, agentes y hooks estándar del equipo .NET",
  "version": "1.0.0",
  "author": { "name": "Equipo Plataforma" }
}
```

Las skills de un plugin se invocan como `/equipo-dotnet:crear-endpoint`.

### Marketplaces
Un **marketplace** es un repositorio con `.claude-plugin/marketplace.json` que lista plugins:
```json
{
  "name": "plugins-de-mi-empresa",
  "owner": { "name": "Mi Empresa" },
  "plugins": [
    { "name": "equipo-dotnet", "source": "./plugins/equipo-dotnet", "description": "Estándares .NET" }
  ]
}
```

Uso:
```text
/plugin marketplace add mi-org/claude-plugins
/plugin install equipo-dotnet@plugins-de-mi-empresa
/plugin                      ← gestionar (activar, desactivar, actualizar)
```

Desarrollo local: `claude --plugin-dir ./mi-plugin` para probar sin instalar.

> Además de plugins, Claude Code admite *mods* (cambios a su propia interfaz, como paneles o líneas de estado) — consulta la documentación si te interesa personalizar la UI.

---

## Errores comunes

- Hooks lentos en `PostToolUse` que ralentizan cada edición (limita con `matcher` y `if`).
- Hook `Stop` sin comprobar `stop_hook_active` → bucle infinito.
- Usar `exit 1` esperando bloquear (bloquear es `exit 2`).
- Plugins con hooks que ejecutan comandos sin revisar (riesgo de seguridad).

## Ejercicios

1. Añade el hook de formateo automático y el de protección de archivos. Pide al agente que edite `.env` y verifica el bloqueo.
2. Crea el hook `Stop` que exige tests verdes.
   - ✅ Éxito: si rompes un test, Claude no da la tarea por terminada.
3. Crea `/fix-issue` en ambas herramientas.
4. Empaqueta tu skill, tu subagente revisor y tus hooks en un plugin; instálalo en otro repo con `--plugin-dir` o un marketplace local.

## Checklist

- [ ] Entiendo eventos, matchers y códigos de salida.
- [ ] Tengo al menos un hook de calidad y uno de seguridad.
- [ ] Creé comandos reutilizables.
- [ ] Sé empaquetar y distribuir un plugin.

---

⬅️ [04.2](02-agentes-y-subagentes.md) · ➡️ [05.1 · MCP: conceptos](../05-mcp/01-mcp-conceptos.md)
