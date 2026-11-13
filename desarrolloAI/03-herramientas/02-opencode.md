# 03.2 · OpenCode

## Objetivos

- Instalar OpenCode 2.x y conectar proveedores de modelos.
- Usar los agentes integrados (build, plan, general, explore).
- Configurar `opencode.json` (formato V2): modelos, permisos, agentes, MCP, instrucciones.
- Crear comandos, agentes y skills propios.
- Ejecutar OpenCode sin interfaz.

---

## 1. ¿Qué es?

**OpenCode** es un agente de programación **open source** (TUI de terminal, app de escritorio y web) que funciona con **muchos proveedores de modelos**: Anthropic, OpenAI, Google, OpenRouter, modelos locales y más, además de sus propias ofertas (OpenCode Console / OpenCode Go). Usa `AGENTS.md` como archivo de instrucciones y es compatible con skills de Claude (`.claude/skills`).

> **Versión:** desde octubre de 2026 la línea actual es **OpenCode 2.x**. Lee la misma ubicación de configuración que la 1.x y acepta el formato V1, pero el formato **nativo V2** cambia varios nombres (p. ej. `permission` → `permissions`, `agent` → `agents`, `bash` → `shell`, `task` → `subagent`). Esta guía usa V2 e indica el equivalente V1 cuando ayuda.

---

## 2. Instalación

Consulta siempre la sección *Install* de `opencode.ai/docs` (cambia con frecuencia). A noviembre de 2026:

```bash
# macOS / Linux: script oficial
curl -fsSL https://opencode.ai/install | bash

# O con un gestor de paquetes JS (npm, bun, pnpm…) — verifica el nombre del paquete en la doc
```

- **Windows**: los gestores de paquetes de Windows no están soportados; descarga el **binario standalone** (x64/ARM64) desde la web oficial o usa **WSL2**.
- Si vienes de la 1.x: `opencode upgrade --major` (haz copia de `~/.config/opencode` y `~/.local/share/opencode` antes).

```bash
opencode --version   # debe mostrar 2.x
cd mi-proyecto
opencode             # abre la TUI
```

---

## 3. Conectar un proveedor de modelos

Dentro de la TUI:
```text
/connect
```
Elige el proveedor (Anthropic, OpenAI, OpenRouter, etc.) y autentícate (API key u OAuth según el proveedor). Después:
```text
/models
```
para elegir modelo. Los modelos se identifican como `proveedor/modelo`, opcionalmente con variante: `anthropic/claude-sonnet-5-5#high`.

---

## 4. Primeros pasos

```text
/init
```
Analiza el proyecto y crea/actualiza `AGENTS.md`. Revísalo (ver 01.3).

> ⚠️ OpenCode 2 descubre **solo `AGENTS.md`** (no usa `CLAUDE.md` como respaldo). Si tus reglas viven en `CLAUDE.md`, muévelas a `AGENTS.md` y deja en `CLAUDE.md` un `@AGENTS.md`.

### Entradas y atajos habituales en la TUI

| Entrada | Efecto |
|---|---|
| `Tab` | Cambiar entre agentes primarios (**build** ↔ **plan**) |
| `@archivo` | Adjuntar archivo al prompt (también `@skill-id` para cargar una skill) |
| `!comando` | Ejecutar un comando de shell |
| `/comando` | Comandos integrados y personalizados |
| `/undo`, `/redo` | Deshacer/rehacer cambios del agente |
| `/compact` | Compactar la sesión |
| `/new`, `/sessions` | Nueva sesión / cambiar de sesión |
| `/share` | Compartir sesión (según la política `share`) |
| `/mcps` | Ver servidores MCP y autenticarse |

> Usa `/help` para la lista actual; atajos y temas se configuran en la configuración de CLI (`~/.config/opencode/cli.json`).

---

## 5. Agentes integrados

| Agente | Tipo | Qué hace |
|---|---|---|
| **build** | primario (por defecto) | Agente de desarrollo con todas las herramientas |
| **plan** | primario | Explora y planifica **sin editar** archivos del proyecto |
| **general** | subagente | Investigación y tareas multi-paso (no puede lanzar más subagentes) |
| **explore** | subagente | Búsqueda/lectura de código o web, sin editar |
| compaction, title, summary | ocultos | Mantenimiento interno |

Flujo típico: `Tab` → **plan** para explorar y acordar el plan; `Tab` → **build** para implementarlo. Los subagentes se invocan pidiéndolo en lenguaje natural (*"usa el subagente reviewer para revisar mis cambios"*) y se ejecutan en una sesión hija con contexto limpio.

---

## 6. Configuración: `opencode.json(c)`

Ubicaciones (se combinan; la más específica gana):
- Global: `~/.config/opencode/opencode.json(c)`
- Proyecto: `opencode.json(c)` o `.opencode/opencode.json(c)`

Ejemplo completo en formato V2 (JSONC admite comentarios):

```jsonc
{
  "$schema": "https://opencode.ai/config.json",

  // Modelo por defecto
  "model": "anthropic/claude-sonnet-5-5",

  // Archivos de instrucciones adicionales (AGENTS.md se descubre solo)
  "instructions": ["CONTRIBUTING.md", "docs/guidelines/*.md"],

  // Permisos: lista ordenada, gana la última regla que coincide
  "permissions": [
    { "action": "shell", "resource": "*", "effect": "ask" },
    { "action": "shell", "resource": "pnpm test *", "effect": "allow" },
    { "action": "shell", "resource": "pnpm lint *", "effect": "allow" },
    { "action": "shell", "resource": "git push *", "effect": "deny" },
    { "action": "read", "resource": "*.env*", "effect": "deny" }
  ],

  // Agentes definidos en JSON (también pueden ir en .opencode/agents/*.md)
  "agents": {
    "docs": {
      "description": "Escribe y actualiza documentación técnica en español",
      "mode": "subagent",
      "model": "anthropic/claude-haiku-5-5",
      "permissions": [
        { "action": "shell", "resource": "*", "effect": "deny" }
      ]
    }
  },

  // Servidores MCP (V2: dentro de "servers")
  "mcp": {
    "servers": {
      "playwright": {
        "type": "local",
        "command": ["npx", "-y", "@playwright/mcp@latest"]
      },
      "context7": {
        "type": "remote",
        "url": "https://mcp.context7.com/mcp",
        "oauth": false,
        "headers": { "CONTEXT7_API_KEY": "{env:CONTEXT7_API_KEY}" }
      }
    }
  },

  "share": "manual"
}
```

### Equivalencias V1 → V2 más importantes

| V1 | V2 |
|---|---|
| `"permission": { "bash": { "git push *": "ask" }, "edit": "allow" }` | `"permissions": [ {action, resource, effect}, ... ]` |
| acción `bash` / `task` / `write`, `patch` | `shell` / `subagent` / `edit` |
| `"agent": {...}`, `"mode": {...}` | `"agents": {...}` |
| `"mcp": { "nombre": {...} }` | `"mcp": { "servers": { "nombre": {...} } }` |
| `"tools": { "websearch": false }` | regla `deny` en `permissions` |
| `"autoshare": true` | `"share": "auto"` |

> Truco oficial: pide a OpenCode *"Migra mi configuración de OpenCode, incluidas las definiciones en archivos, del formato V1 al formato nativo V2, preservando su comportamiento."*

---

## 7. Agentes personalizados en Markdown

`.opencode/agents/reviewer.md` (proyecto) o `~/.config/opencode/agents/reviewer.md` (global):

```markdown
---
description: Revisa cambios buscando bugs, regresiones y problemas de seguridad
mode: subagent
model: anthropic/claude-sonnet-5-5#high
permissions:
  - action: edit
    resource: "*"
    effect: deny
  - action: shell
    resource: "*"
    effect: deny
  - action: shell
    resource: "git diff *"
    effect: allow
---

Eres un revisor de código senior. Revisa los cambios actuales (`git diff`).
Lista los hallazgos ordenados por severidad (crítico, alto, medio, bajo)
con archivo y línea. No edites archivos.
```

- `mode`: `primary` (por defecto en agentes nuevos), `subagent` o `all`.
- Rutas anidadas forman el ID: `team/reviewer.md` → `team/reviewer`.
- Más en [04.2](../04-extensibilidad/02-agentes-y-subagentes.md).

---

## 8. Comandos personalizados

`.opencode/commands/review.md`:
```markdown
---
description: Revisa un archivo buscando bugs
agent: plan
model: anthropic/claude-sonnet-5-5#high
---

Revisa $ARGUMENTS. Informa primero de los bugs, luego de mejoras de estilo.
Cambios recientes:
!`git diff --stat`
```
Uso: `/review src/auth.ts`. Soporta `$ARGUMENTS`, `$1`, `$2`… e inyección de shell con `` !`comando` `` (se ejecuta **fuera** del sistema de permisos: solo comandos de confianza). Con `subagent: true` corre en una sesión hija en segundo plano.

---

## 9. Skills

OpenCode descubre skills en `.opencode/skills/`, `~/.config/opencode/skills/` **y también** en `.claude/skills/`, `~/.claude/skills/`, `.agents/skills/` y `~/.agents/skills/`. Por tanto, **una skill escrita para Claude Code suele funcionar en OpenCode**. Ver [04.1](../04-extensibilidad/01-skills.md).

---

## 10. Uso sin interfaz y servidor

```bash
# Ejecutar un prompt sin TUI
opencode run "Explica qué hace src/index.ts"

# Gestionar MCP desde la CLI
opencode mcp add
opencode mcp auth <nombre>

# Conectar la web/app a tu instancia
opencode pair
```

OpenCode 2 ejecuta por defecto un **servicio en segundo plano** compartido que gestiona sesiones, configuración, permisos y ejecución; la TUI, la app de escritorio y la web se conectan a él (`opencode --standalone` arranca un servidor privado). También existe un SDK cliente para integrarlo en tus herramientas y una integración con GitHub Actions.

---

## Errores comunes

- Mezclar en un mismo agente campos V1 y V2 (OpenCode no infiere formatos mezclados dentro de un agente).
- Esperar que OpenCode lea `CLAUDE.md`.
- Escribir `$VAR` en strings JSON (no se expande): usa `{env:VAR}`.
- Poner las reglas de permiso específicas *antes* de la general (gana la última).

## Ejercicios

1. Instala OpenCode, conecta un proveedor con `/connect` y ejecuta `/init`.
2. Haz la misma tarea que hiciste en Claude Code (03.1, ejercicio 2) usando **plan** → **build**. Anota diferencias.
3. Crea el subagente `reviewer` de la sección 7 y pide: *"usa el subagente reviewer para revisar mis cambios"*.
4. Crea el comando `/review` y pruébalo con un archivo.
   - ✅ Éxito: el comando aparece en la lista `/` y produce un informe priorizado.

## Checklist

- [ ] Instalé OpenCode 2 y conecté un proveedor.
- [ ] Alterno plan/build con `Tab`.
- [ ] Entiendo `opencode.json` V2 (permisos, agentes, MCP).
- [ ] Creé un agente y un comando propios.

---

⬅️ [03.1](01-claude-code.md) · ➡️ [03.3 · Comparativa](03-comparativa-claude-code-vs-opencode.md)
