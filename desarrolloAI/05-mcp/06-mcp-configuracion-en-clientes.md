# 05.6 · Configurar servidores MCP en clientes (Claude Code, OpenCode, VS Code, Claude Desktop)

## Objetivos

- Añadir servidores MCP locales (stdio) y remotos (HTTP, OAuth) en cada cliente.
- Entender los ámbitos (personal, proyecto, equipo) y cómo compartir configuración.
- Gestionar secretos y variables de entorno.
- Diagnosticar problemas de conexión.
- Conocer servidores MCP útiles para desarrollo.

---

## 1. Claude Code

### 1.1 Por CLI
```bash
# Local (stdio): todo lo que va después de -- es el comando del servidor
claude mcp add tareas -- uv run --directory /ruta/mcp-tareas-py server.py

# Con variables de entorno
claude mcp add tareas --env TAREAS_ARCHIVO=/ruta/tareas.json -- uv run --directory /ruta server.py

# Remoto (Streamable HTTP)
claude mcp add --transport http github https://api.githubcopilot.com/mcp/

# Remoto con cabecera
claude mcp add --transport http mi-api https://api.ejemplo.com/mcp --header "Authorization: Bearer $MI_TOKEN"

# Ámbitos
claude mcp add --scope local   ...   # (por defecto) solo tú, este proyecto
claude mcp add --scope project ...   # se guarda en .mcp.json (compartido vía git)
claude mcp add --scope user    ...   # tú, en todos tus proyectos

# Gestión
claude mcp list
claude mcp get tareas
claude mcp remove tareas
```

Dentro de la sesión: **`/mcp`** muestra estado, tools y permite autenticarse con OAuth en servidores remotos.

### 1.2 Archivo `.mcp.json` (proyecto, se commitea)
```json
{
  "mcpServers": {
    "tareas": {
      "command": "uv",
      "args": ["run", "--directory", "${PROJECT_ROOT:-.}/mcp", "server.py"],
      "env": { "TAREAS_ARCHIVO": "${TAREAS_ARCHIVO}" }
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    },
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer ${GITHUB_TOKEN}" }
    }
  }
}
```
- Expansión de variables: `${VAR}` y `${VAR:-valor_por_defecto}`.
- Claude Code pide aprobación antes de usar servidores de un `.mcp.json` de proyecto (seguridad).

### 1.3 Windows
En Windows nativo, los comandos `npx` suelen necesitar el envoltorio `cmd /c`:
```bash
claude mcp add playwright -- cmd /c npx -y @playwright/mcp@latest
```

### 1.4 Permisos de herramientas MCP
Las tools MCP se nombran `mcp__<servidor>__<tool>`:
```json
{
  "permissions": {
    "allow": ["mcp__tareas__listar_tareas", "mcp__playwright__browser_snapshot"],
    "deny": ["mcp__github__delete_repository"]
  }
}
```
Los **prompts** MCP aparecen como comandos `/mcp__<servidor>__<prompt>` y los **resources** se mencionan con `@servidor:uri`.

---

## 2. OpenCode (formato V2)

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "servers": {
      "tareas": {
        "type": "local",
        "command": ["uv", "run", "--directory", "/ruta/mcp-tareas-py", "server.py"],
        "cwd": ".",
        "environment": { "TAREAS_ARCHIVO": "{env:TAREAS_ARCHIVO}" },
        "timeout": 10000
      },
      "context7": {
        "type": "remote",
        "url": "https://mcp.context7.com/mcp",
        "oauth": false,
        "headers": { "CONTEXT7_API_KEY": "{env:CONTEXT7_API_KEY}" }
      },
      "sentry": {
        "type": "remote",
        "url": "https://mcp.sentry.dev/mcp"
        // OAuth activado por defecto: autentícate con `opencode mcp auth sentry` o /mcps
      }
    }
  },
  "permissions": [
    { "action": "context7_*", "resource": "*", "effect": "allow" },
    { "action": "sentry_*", "resource": "*", "effect": "ask" }
  ]
}
```

- `local`: obligatorios `type` y `command` (array). Opcionales: `cwd`, `environment`, `disabled`, `timeout`…
- `remote`: obligatorios `type` y `url` absoluta. Opcionales: `headers`, `oauth`, `disabled`, `timeout`…
- Sustitución de variables: **`{env:NOMBRE}`** (`$NOMBRE` no se expande en JSON).
- Las tools MCP se nombran `<servidor>_<tool>` en los permisos; los prompts MCP aparecen como `/<servidor>:<prompt>`.
- **V1** usaba `"mcp": { "nombre": {...} }` (sin `servers`); OpenCode 2 acepta ambos.
- Patrón para muchos servidores: denegarlos globalmente y permitirlos solo en ciertos agentes (permisos por agente).
- CLI: `opencode mcp add`, `opencode mcp auth <nombre>`, `opencode mcp debug <nombre>`.

---

## 3. VS Code (GitHub Copilot agent mode)

`.vscode/mcp.json`:
```json
{
  "inputs": [
    { "type": "promptString", "id": "github-token", "description": "GitHub token", "password": true }
  ],
  "servers": {
    "tareas": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "${workspaceFolder}/mcp", "server.py"]
    },
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer ${input:github-token}" }
    }
  }
}
```
Comandos útiles: *MCP: List Servers*, *MCP: Add Server*.

---

## 4. Claude Desktop

`claude_desktop_config.json` (Configuración → Desarrollador → Editar configuración):
```json
{
  "mcpServers": {
    "tareas": {
      "command": "uv",
      "args": ["run", "--directory", "C:\\ruta\\mcp-tareas-py", "server.py"]
    }
  }
}
```
Reinicia la app tras editar. Los servidores remotos se añaden como **conectores** desde la configuración.

---

## 5. Tabla resumen de formatos

| Cliente | Archivo | Clave raíz | stdio | HTTP | Variables |
|---|---|---|---|---|---|
| Claude Code | `.mcp.json` | `mcpServers` | `command` + `args` | `"type": "http"`, `url` | `${VAR}` |
| OpenCode 2 | `opencode.json` | `mcp.servers` | `"type": "local"`, `command: []` | `"type": "remote"`, `url` | `{env:VAR}` |
| VS Code | `.vscode/mcp.json` | `servers` | `"type": "stdio"` | `"type": "http"` | `${input:id}`, `${workspaceFolder}` |
| Claude Desktop | `claude_desktop_config.json` | `mcpServers` | `command` + `args` | conectores | — |

---

## 6. Servidores MCP útiles para desarrollo

| Servidor | Para qué | Instalación típica |
|---|---|---|
| **Playwright MCP** | Controlar un navegador (accesibilidad/snapshots): probar UI, E2E | `npx -y @playwright/mcp@latest` |
| **Chrome DevTools MCP** | Depurar con DevTools: consola, red, rendimiento | `npx -y chrome-devtools-mcp@latest` |
| **GitHub** | Issues, PRs, código, Actions | Remoto: `https://api.githubcopilot.com/mcp/` |
| **Context7** | Documentación actualizada de librerías | Remoto: `https://mcp.context7.com/mcp` |
| **Sentry** | Errores de producción | Remoto con OAuth |
| **Bases de datos** (Postgres, SQL Server…) | Consultar esquemas y datos (¡en solo lectura!) | Varía |
| **Filesystem / Git** (referencia) | Aprender y pruebas | `@modelcontextprotocol/server-filesystem` |

> Aplica la checklist de seguridad de [02.2 §5](../02-flujos-de-trabajo/02-seguridad-y-buenas-practicas.md) antes de instalar cualquiera.

---

## 7. Diagnóstico de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| "Failed to connect" / timeout | El comando no existe en el PATH del cliente; arranque lento (`dotnet run`) | Rutas absolutas; publicar binario; aumentar `timeout` |
| Conecta pero falla al instante | El servidor escribe en stdout | Logs a stderr |
| No encuentra archivos | Directorio de trabajo distinto | `--directory`, `cwd` o rutas absolutas |
| Funciona en terminal pero no en el cliente | Variables de entorno distintas | Pasar `env`/`environment` explícitamente |
| Windows: `spawn npx ENOENT` | `npx` es un `.cmd` | `cmd /c npx ...` |
| Las tools no aparecen | Servidor deshabilitado o sin aprobar | `/mcp` (Claude Code), `/mcps` (OpenCode) |

Herramientas: `claude --debug`, `claude mcp get <n>`, `opencode mcp debug <n>`, y siempre **MCP Inspector** para aislar si el problema es del servidor o del cliente.

---

## Ejercicios

1. Registra tus servidores de Python, Node y C# en Claude Code con ámbito `project` y verifica el `.mcp.json` generado.
2. Replica la configuración en `opencode.json` y en `.vscode/mcp.json`.
3. Añade Playwright MCP y pide: *"Abre https://playwright.dev, busca 'locators' y resume la página."*
4. Provoca a propósito un `print()` en stdout en tu servidor Python y observa el error; luego arréglalo.
   - ✅ Éxito: sabes reconocer el síntoma y su causa.

## Checklist

- [ ] Configuro MCP en Claude Code, OpenCode, VS Code y Claude Desktop.
- [ ] Comparto configuración de proyecto sin secretos.
- [ ] Controlo permisos de tools MCP.
- [ ] Sé diagnosticar problemas de conexión.

---

⬅️ [05.5](05-mcp-clientes-python-node-csharp.md) · ➡️ [06.1 · OpenSpec](../06-spec-driven/01-openspec.md)
