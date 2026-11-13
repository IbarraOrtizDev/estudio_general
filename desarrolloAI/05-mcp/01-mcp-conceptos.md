# 05.1 · MCP (Model Context Protocol): conceptos

## Objetivos

- Entender qué problema resuelve MCP y su arquitectura host–cliente–servidor.
- Conocer las primitivas: tools, resources, prompts (y capacidades del cliente).
- Distinguir transportes: stdio y Streamable HTTP.
- Conocer los cambios de la especificación **2026-07-28**.
- Diseñar buenas herramientas MCP.

---

## 1. El problema

Sin un estándar, cada aplicación de IA (Claude Code, OpenCode, VS Code, Cursor, tu propio agente…) necesitaría una integración a medida para cada sistema (GitHub, Jira, Postgres, el navegador…): **N × M integraciones**.

**MCP** es un protocolo abierto (gobernado hoy por la *Agentic AI Foundation* de la Linux Foundation) que estandariza cómo las aplicaciones de IA se conectan a herramientas y datos: **N + M**. Es "el USB-C de la IA".

---

## 2. Arquitectura

```
┌──────────────────────── HOST (Claude Code, OpenCode, VS Code, tu app) ─────┐
│                                                                            │
│   LLM  ◄──►  Cliente MCP A  ◄─── stdio ───►  Servidor MCP "tareas" (local) │
│              Cliente MCP B  ◄─── HTTP  ───►  Servidor MCP "github" (remoto)│
│              Cliente MCP C  ◄─── stdio ───►  Servidor MCP "playwright"     │
└────────────────────────────────────────────────────────────────────────────┘
```

| Rol | Qué es |
|---|---|
| **Host** | La aplicación con la que interactúa el usuario; contiene el LLM y gestiona permisos |
| **Cliente** | Componente dentro del host que mantiene la conexión con **un** servidor |
| **Servidor** | Programa que expone capacidades (tools, resources, prompts) |

El protocolo usa mensajes **JSON-RPC 2.0**.

---

## 3. Primitivas del servidor

| Primitiva | Controlada por | Qué es | Ejemplo |
|---|---|---|---|
| **Tools** | El **modelo** decide llamarlas | Funciones con efectos o cálculos; entrada definida con JSON Schema | `crear_tarea(titulo, prioridad)` |
| **Resources** | La **aplicación**/usuario decide incluirlos | Datos de solo lectura identificados por URI | `tareas://lista`, `file:///...`, `db://esquema` |
| **Prompts** | El **usuario** los elige | Plantillas de mensajes reutilizables | `/mcp__tareas__resumen_semanal` |

Detalles útiles:
- Las tools pueden devolver **contenido** (texto, imágenes, recursos) para el modelo y **contenido estructurado** (`structuredContent`, validado con un `outputSchema`) para el código.
- Las tools pueden tener **anotaciones** (p. ej. `readOnlyHint`, `destructiveHint`) que el host usa para decidir permisos.
- Los resources pueden ser estáticos o **plantillas** (`users://{id}/profile`).

### Capacidades del lado del cliente
- **Elicitation**: el servidor pide información al usuario durante una operación (formularios, confirmaciones, URLs). En 2026-07-28 se implementa con *Multi Round-Trip Requests* (el servidor responde "necesito más input" y el cliente reintenta con la respuesta).
- **Roots** y **Sampling**: existían en especificaciones anteriores; **deprecados en 2026-07-28** (los SDK los marcan como obsoletos). No diseñes servidores nuevos alrededor de ellos.

### Extensiones
La especificación 2026-07-28 formaliza un marco de **extensiones** que evolucionan aparte del núcleo, por ejemplo **MCP Apps** (interfaces interactivas que una tool puede mostrar en el host) y **Tasks** (operaciones de larga duración).

---

## 4. Transportes

| Transporte | Cómo funciona | Cuándo |
|---|---|---|
| **stdio** | El host lanza el servidor como **subproceso** y se comunican por stdin/stdout | Herramientas locales, acceso al sistema de archivos, desarrollo |
| **Streamable HTTP** | El servidor es un endpoint HTTP (p. ej. `POST /mcp`), con respuestas JSON o en streaming (SSE) | Servidores remotos, compartidos, en la nube, con OAuth |
| ~~SSE (HTTP+SSE)~~ | Transporte antiguo | **Legado**: no lo uses en servidores nuevos |

> ⚠️ **Regla de oro de stdio:** **stdout es el canal del protocolo.** Nunca escribas en stdout (`print`, `console.log`, `Console.WriteLine`) desde un servidor stdio: usa **stderr** o un logger configurado a stderr. Es el error nº 1 de principiantes.

---

## 5. La especificación 2026-07-28 (lo que cambió)

La revisión publicada el 28 de julio de 2026 es la más grande desde el lanzamiento:

| Antes (≤ 2025-11-25) | Ahora (2026-07-28) |
|---|---|
| Handshake `initialize`/`initialized` obligatorio | **Eliminado**: cada petición es autocontenida (versión, info y capacidades del cliente viajan en `_meta`) |
| Sesiones con cabecera `Mcp-Session-Id` | **Sin sesiones de protocolo** → servidores *stateless* detrás de cualquier balanceador |
| Negociación al inicio | Descubrimiento con `server/discover` |
| Elicitation iniciada por el servidor | **Multi Round-Trip Requests (MRTR)** |
| Roots, Sampling, logging por MCP | **Deprecados** |
| — | Cabeceras HTTP estándar (`MCP-Protocol-Version`, `Mcp-Method`, `Mcp-Name`) para gateways |
| — | Endurecimiento de OAuth (validación de `iss`, etc.) y política formal de deprecación |

**Qué significa para ti:**
- Usa los **SDK v2** (Python `mcp` 2.x, TS `@modelcontextprotocol/server`/`client`, C# `ModelContextProtocol` 2.x). Ocultan casi todo esto.
- Los SDK v2 siguen sirviendo a clientes de revisiones anteriores (compatibilidad).
- Mucha documentación y tutoriales en Internet usan la API v1 (`FastMCP`, `@modelcontextprotocol/sdk`, `server.tool(...)`). Esta guía usa v2 y señala las diferencias.

---

## 6. Diseñar buenas tools

1. **Nombres claros y consistentes**: `crear_tarea`, `listar_tareas` (verbo_sustantivo).
2. **Descripciones orientadas al modelo**: qué hace, cuándo usarla, qué devuelve, limitaciones.
3. **Esquemas estrictos**: tipos, enums, rangos, `description` en cada parámetro.
4. **Pocas tools bien diseñadas** > muchas tools finas (cada una ocupa contexto). Piensa en *tareas del usuario*, no en endpoints 1:1 de tu API.
5. **Respuestas compactas**: paginación, filtros, resúmenes; no devuelvas 5 MB de JSON.
6. **Errores útiles**: devuelve `isError: true` con un mensaje que ayude al modelo a corregirse ("la prioridad debe ser alta|media|baja").
7. **Idempotencia y seguridad**: marca las destructivas; valida todo; principio de mínimo privilegio en credenciales.
8. **Nunca confíes en la entrada**: el LLM puede haber sido manipulado (prompt injection).

---

## 7. Herramientas del ecosistema

| Herramienta | Uso |
|---|---|
| **MCP Inspector** (`npx @modelcontextprotocol/inspector`) | Probar servidores visualmente: listar y llamar tools/resources/prompts |
| **Registro oficial de MCP** | Descubrir servidores públicos |
| Servidores de referencia (`@modelcontextprotocol/server-everything`, filesystem, git…) | Aprender y probar clientes |
| Servidores populares | GitHub, Playwright, Chrome DevTools, Context7 (docs), Sentry, bases de datos |

---

## Ejercicios

1. Ejecuta `npx @modelcontextprotocol/inspector npx -y @modelcontextprotocol/server-everything`, conéctate y explora tools, resources y prompts.
2. Diseña (solo en papel) un servidor MCP para tu dominio: 3–5 tools, 2 resources y 1 prompt, con nombres, descripciones y esquemas.
   - ✅ Éxito: cada tool tiene descripción con "cuándo usarla" y parámetros documentados.
3. Explica con tus palabras por qué un servidor *stateless* escala mejor y qué cambió en 2026-07-28.

## Checklist

- [ ] Entiendo host, cliente y servidor.
- [ ] Distingo tools, resources y prompts.
- [ ] Sé cuándo usar stdio y cuándo Streamable HTTP.
- [ ] Nunca escribo en stdout en servidores stdio.
- [ ] Conozco los cambios de la spec 2026-07-28.

---

⬅️ [04.3](../04-extensibilidad/03-hooks-comandos-y-plugins.md) · ➡️ [05.2 · Servidor MCP en Python](02-mcp-servidor-python.md)
