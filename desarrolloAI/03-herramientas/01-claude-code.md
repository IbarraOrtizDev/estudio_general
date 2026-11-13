# 03.1 · Claude Code

## Objetivos

- Instalar y configurar Claude Code en Windows, macOS o Linux.
- Dominar la interfaz: comandos `/`, atajos, modos de permiso, plan mode.
- Gestionar sesiones, contexto, checkpoints y modelos.
- Usar Claude Code en modo headless y en CI.
- Conocer su configuración (settings, memoria, MCP, extensiones).

---

## 1. ¿Qué es?

**Claude Code** es el agente de programación de Anthropic. Funciona en la **terminal**, en IDEs (extensiones de VS Code y JetBrains), en la app de escritorio, en la web y en el móvil. Lee y edita tu código, ejecuta comandos, usa git, navega la web, se conecta a servidores MCP y se extiende con skills, subagentes, hooks y plugins.

---

## 2. Instalación

```bash
# macOS / Linux / WSL (instalador nativo recomendado)
curl -fsSL https://claude.ai/install.sh | bash
```
```powershell
# Windows (PowerShell)
irm https://claude.ai/install.ps1 | iex
```
```bash
# Alternativa con npm (requiere Node.js 18+)
npm install -g @anthropic-ai/claude-code
```

Primera ejecución:
```bash
cd mi-proyecto
claude            # inicia sesión con tu cuenta Claude (Pro/Max/Team/Enterprise) o API key
claude doctor     # diagnostica la instalación
```

> Consulta requisitos y métodos actualizados en la documentación oficial (`code.claude.com/docs`).

---

## 3. Primeros pasos en un proyecto

```text
> /init
```
Genera un `CLAUDE.md` analizando el repo. **Edítalo** (ver 01.3). Si tu repo ya tiene `AGENTS.md` y no `CLAUDE.md`, Claude Code lo usará automáticamente.

Prompts para orientarte:
```text
> ¿Qué hace este proyecto? Dame un mapa de carpetas y responsabilidades.
> ¿Cómo se ejecutan los tests? Ejecútalos y dime cuáles fallan.
> Explica el flujo de una petición HTTP desde el controller hasta la base de datos.
```

---

## 4. Interfaz: atajos y entradas especiales

| Entrada | Efecto |
|---|---|
| `@ruta/archivo` | Menciona un archivo/carpeta (se añade al contexto) |
| `!comando` | Modo bash: ejecuta un comando de shell directamente |
| `/comando` | Comandos integrados, skills y comandos personalizados |
| `Shift+Tab` | Cicla modos de permiso: *default* → *accept edits* → *plan* (→ *auto* si está disponible) |
| `Esc` | Interrumpe al agente (puedes redirigirlo) |
| `Esc` `Esc` | Abre el *rewind*: vuelve a un punto anterior de la conversación/código |
| `Ctrl+C` | Cancela / sale |
| Pegar imagen | Arrastra o pega capturas (diseños, errores) |
| `↑` | Historial de prompts |

---

## 5. Comandos `/` más útiles

> La lista exacta cambia entre versiones: escribe `/` para ver los disponibles o `/help`.

| Comando | Para qué |
|---|---|
| `/init` | Generar `CLAUDE.md` |
| `/memory` | Ver/editar archivos de memoria e instrucciones cargados |
| `/config` | Configuración (tema, modelo, *Project instructions*, etc.) |
| `/model` | Cambiar de modelo |
| `/permissions` | Gestionar reglas allow/ask/deny |
| `/clear` | Vaciar la conversación (nueva tarea) |
| `/compact [instrucciones]` | Resumir la conversación para liberar contexto |
| `/context` | Ver qué ocupa la ventana de contexto |
| `/rewind` | Restaurar conversación y/o código a un checkpoint |
| `/resume` | Retomar una sesión anterior |
| `/mcp` | Ver y gestionar servidores MCP (incluye autenticación OAuth) |
| `/agents` | Gestionar subagentes |
| `/hooks` | Ver hooks configurados |
| `/plugin` | Instalar y gestionar plugins y marketplaces |
| `/usage` o `/cost` | Consumo |
| `/doctor` | Diagnóstico |
| `/help` | Ayuda |

---

## 6. Modos de permiso y plan mode

| Modo | Comportamiento | Cuándo |
|---|---|---|
| **default** | Pide permiso para ediciones y comandos no permitidos | Aprendizaje, código sensible |
| **accept edits** | Aplica ediciones sin preguntar; comandos siguen pidiendo permiso | Trabajo diario en rama |
| **plan** | Solo lectura: investiga y propone un plan | Fase de exploración y planificación |
| **auto** | Un clasificador aprueba acciones seguras y bloquea las arriesgadas | Tareas largas con supervisión ligera (si tu plan lo permite) |
| **bypassPermissions** | Sin preguntas (`--dangerously-skip-permissions`) | **Solo** contenedores desechables |

Arrancar directamente en plan mode:
```bash
claude --permission-mode plan
```

---

## 7. Sesiones, checkpoints y git

```bash
claude                    # nueva sesión
claude --continue         # continúa la última sesión del directorio
claude --resume           # elige una sesión anterior
claude "explica este repo"  # sesión interactiva con prompt inicial
```

- **Checkpoints**: Claude Code guarda el estado antes de cada edición. `Esc Esc` o `/rewind` restauran código y/o conversación. No sustituye a git: haz commits frecuentes.
- **Git**: pídeselo en lenguaje natural: *"crea una rama feat/x, haz commit con mensaje convencional y abre un PR"* (usa `gh` si está instalado).

---

## 8. Configuración: archivos y precedencia

| Archivo | Alcance | ¿Se commitea? |
|---|---|---|
| Políticas gestionadas (managed settings) | Organización | — (máxima prioridad) |
| `~/.claude/settings.json` | Tu usuario, todos los proyectos | No |
| `.claude/settings.json` | Proyecto (equipo) | **Sí** |
| `.claude/settings.local.json` | Proyecto, personal | No |
| `~/.claude/CLAUDE.md` | Instrucciones personales globales | No |
| `CLAUDE.md` / `AGENTS.md` | Instrucciones del proyecto | Sí |
| `.mcp.json` | Servidores MCP del proyecto | Sí |
| `.claude/skills/`, `.claude/agents/`, `.claude/commands/` | Extensiones del proyecto | Sí |

Ejemplo de `.claude/settings.json` de equipo:
```json
{
  "model": "sonnet",
  "permissions": {
    "allow": ["Bash(pnpm test:*)", "Bash(pnpm lint)", "Bash(git diff:*)"],
    "deny": ["Read(./.env*)", "Bash(git push --force:*)"]
  },
  "env": {
    "NODE_ENV": "development"
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "pnpm exec prettier --write \"$(jq -r '.tool_input.file_path')\"" }]
      }
    ]
  }
}
```

---

## 9. Modo headless (`-p`) y automatización

```bash
# Respuesta única, salida en texto
claude -p "¿Qué archivos tocan la tabla Usuarios?"

# Salida JSON para scripts
claude -p "Lista los TODO del repo como JSON" --output-format json

# Limitar herramientas permitidas en esta ejecución
claude -p "Corrige los errores de lint" --allowedTools "Edit" "Bash(pnpm lint:*)"

# Pipes
cat error.log | claude -p "Explica la causa raíz de este error"
```

- `--output-format stream-json` para procesar eventos en tiempo real.
- `--max-turns N` para limitar iteraciones.
- **GitHub Actions**: integración oficial (`anthropics/claude-code-action`) para responder a `@claude` en PRs/issues o ejecutar revisiones. Instálala desde Claude Code con `/install-github-app`.
- **Agent SDK**: para construir tus propios agentes con el mismo motor de Claude Code (Python y TypeScript).

---

## 10. Extensiones (visión general)

| Extensión | Qué hace | Módulo |
|---|---|---|
| **Skills** (`SKILL.md`) | Conocimiento/procedimientos bajo demanda; también son los comandos `/` personalizados | [04.1](../04-extensibilidad/01-skills.md) |
| **Subagentes** | Agentes especializados con contexto propio | [04.2](../04-extensibilidad/02-agentes-y-subagentes.md) |
| **Hooks** | Scripts en eventos del ciclo de vida | [04.3](../04-extensibilidad/03-hooks-comandos-y-plugins.md) |
| **Plugins** | Paquetes distribuibles de skills + agentes + hooks + MCP | [04.3](../04-extensibilidad/03-hooks-comandos-y-plugins.md) |
| **MCP** | Herramientas y datos externos | [05.6](../05-mcp/06-mcp-configuracion-en-clientes.md) |
| **Output styles / statusline** | Personalizar tono y barra de estado | docs oficiales |

---

## 11. Flujo diario recomendado

```text
1. git switch -c feat/mi-tarea
2. claude --permission-mode plan
3. > Explora X y propón un plan para Y (revisar y ajustar)
4. Shift+Tab → accept edits
5. > Implementa el plan; ejecuta tests tras cada paso
6. > Usa el subagente code-reviewer para revisar el diff
7. > Haz commit y abre PR
8. /clear  (siguiente tarea)
```

---

## Errores comunes

- Usar `--dangerously-skip-permissions` en tu máquina principal.
- No commitear `.claude/settings.json` y `.mcp.json` → cada miembro del equipo tiene otra configuración.
- Olvidar `/clear` entre tareas.
- No usar plan mode y aceptar el primer enfoque.
- En Windows nativo: rutas y comandos POSIX en hooks (usa PowerShell o WSL coherentemente).

## Ejercicios

1. Instala Claude Code, ejecuta `/init` en un repo y refina el `CLAUDE.md`.
2. Implementa una mejora pequeña usando plan mode → accept edits. Usa `/rewind` para deshacer un paso y probar otra alternativa.
3. Crea `.claude/settings.json` con permisos para tu stack (test, lint, build) y denegación de `.env`.
4. Ejecuta en headless: `git log --since="1 week ago" --oneline | claude -p "Escribe release notes en español"`.
   - ✅ Éxito: obtienes notas agrupadas por tipo (features, fixes).

## Checklist

- [ ] Instalé y configuré Claude Code.
- [ ] Domino `@`, `!`, `/`, `Shift+Tab`, `Esc Esc`.
- [ ] Sé gestionar contexto (`/clear`, `/compact`, `/context`) y sesiones (`--continue`, `--resume`).
- [ ] Sé usar el modo headless.

---

⬅️ [02.2](../02-flujos-de-trabajo/02-seguridad-y-buenas-practicas.md) · ➡️ [03.2 · OpenCode](02-opencode.md)
