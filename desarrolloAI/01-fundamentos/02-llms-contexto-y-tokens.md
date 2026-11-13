# 01.2 · LLMs, contexto y tokens (lo que necesitas saber)

## Objetivos

- Entender qué es un *token* y una *ventana de contexto* y por qué importan.
- Conocer cómo funciona el *tool use* (function calling) a nivel de API.
- Gestionar el contexto en sesiones largas: compactación, limpieza, subagentes.
- Elegir modelo y nivel de esfuerzo según la tarea.

---

## 1. Conceptos mínimos

| Término | Definición práctica |
|---|---|
| **Token** | Fragmento de texto (≈ ¾ de palabra en inglés; en español y código suele haber más tokens por palabra). Todo se mide en tokens: coste, límites y velocidad. |
| **Ventana de contexto** | Máximo de tokens que el modelo "ve" a la vez: system prompt + instrucciones + historial + resultados de herramientas + tu mensaje. |
| **System prompt** | Instrucciones base del harness (cómo usar tools, estilo). Tú lo amplías con `CLAUDE.md`/`AGENTS.md`. |
| **Tool use / function calling** | El modelo devuelve una petición estructurada (`nombre` + `argumentos JSON`) en lugar de texto. |
| **Temperatura** | Aleatoriedad del muestreo. Los harness de código la gestionan por ti. |
| **Razonamiento extendido / effort** | El modelo "piensa" antes de responder. Más esfuerzo = mejor en tareas difíciles, más lento y caro. |
| **Alucinación** | Respuesta plausible pero falsa (APIs inexistentes, archivos inventados). Se mitiga con verificación y contexto real. |
| **Prompt caching** | Reutilizar prefijos del prompt entre llamadas para abaratar y acelerar. Los harness lo hacen automáticamente. |

---

## 2. Cómo se ve un *tool call* por dentro

Una herramienta se describe con **nombre, descripción y JSON Schema** de entrada:

```json
{
  "name": "buscar_tareas",
  "description": "Busca tareas por texto. Úsala cuando el usuario pregunte por tareas existentes.",
  "input_schema": {
    "type": "object",
    "properties": {
      "texto": { "type": "string", "description": "Texto a buscar" },
      "limite": { "type": "integer", "default": 10 }
    },
    "required": ["texto"]
  }
}
```

El modelo responde algo como:

```json
{ "type": "tool_use", "id": "toolu_01", "name": "buscar_tareas", "input": { "texto": "login" } }
```

El harness ejecuta, y devuelve:

```json
{ "type": "tool_result", "tool_use_id": "toolu_01", "content": "[{\"id\": 7, \"titulo\": \"Arreglar login\"}]" }
```

> 💡 **Consecuencia práctica:** la **descripción** de una herramienta (o de una skill, o de un subagente) es lo que el modelo usa para decidir *cuándo* usarla. Escribirla bien es tan importante como el código. Esto aplica a MCP (módulo 05), skills y subagentes (módulo 04).

---

## 3. La ventana de contexto es tu recurso más escaso

Todo compite por el mismo espacio:

```
┌──────────────────────── ventana de contexto ────────────────────────┐
│ system prompt │ CLAUDE.md/AGENTS.md │ descripciones de tools/MCP/skills│
│ historial de conversación │ archivos leídos │ salidas de comandos │ ... │
└──────────────────────────────────────────────────────────────────────┘
```

Síntomas de contexto saturado:
- El agente "olvida" reglas que le diste al principio.
- Repite errores ya corregidos.
- Se vuelve lento o caro.
- Mezcla tareas diferentes.

### Estrategias de gestión de contexto

| Estrategia | Claude Code | OpenCode |
|---|---|---|
| Ver uso de contexto | `/context` | indicador en la TUI |
| Empezar de cero entre tareas | `/clear` | nueva sesión (`/new`) |
| Resumir la conversación | `/compact [instrucciones]` (y auto-compactación) | `/compact` (agente de compactación) |
| Aislar exploración ruidosa | **Subagentes** (Explore, general-purpose, custom) | **Subagentes** (`explore`, `general`, custom) |
| Cargar conocimiento solo cuando hace falta | **Skills** (se carga solo el cuerpo al usarse) | **Skills** |
| Reducir herramientas cargadas | Desactivar servidores MCP no usados (`/mcp`) | `disabled`/permisos por agente |
| Retomar una sesión | `claude --continue` / `--resume` | lista de sesiones |

**Regla práctica:** *una tarea = una sesión*. Cuando terminas algo, haz commit y `/clear`.

---

## 4. Elegir modelo y esfuerzo

| Tipo de tarea | Modelo sugerido | Esfuerzo |
|---|---|---|
| Búsquedas, renombrados, tareas mecánicas | Modelo rápido (p. ej. Haiku) | bajo |
| Desarrollo diario, features medianas | Modelo equilibrado (p. ej. Sonnet) | medio |
| Arquitectura, bugs difíciles, planificación, specs | Modelo más capaz (p. ej. Opus) | alto |
| Subagentes de exploración | Rápido/equilibrado | bajo–medio |

Patrón muy usado: **modelo potente para planificar, modelo rápido para ejecutar** un plan bien escrito (OpenSpec lo recomienda explícitamente para `/opsx:apply`).

---

## 5. Por qué los agentes alucinan menos con buen contexto

Un LLM predice texto plausible. Si no tiene el dato, "rellena". Antídotos:

1. **Dale fuentes reales**: archivos del repo, documentación vía MCP (p. ej. Context7) o skills.
2. **Dale cómo verificar**: `npm test`, `dotnet build`, `pytest`, linters, type-checkers.
3. **Pídele que cite**: *"indica archivo y línea"*.
4. **Fija versiones**: "usamos React 19 y MCP SDK v2", en tu `AGENTS.md`.

---

## Errores comunes

- Pegar logs gigantes en el chat (usa archivos y pide al agente que los lea/filtre).
- Tener 15 servidores MCP activos "por si acaso" (cada uno añade descripciones de tools al contexto).
- Mezclar tres features en la misma sesión.
- Usar siempre el modelo más caro para todo.

## Ejercicios

1. Abre una sesión, ejecuta `/context` (Claude Code) y anota cuánto ocupan las instrucciones, tools y MCP antes de escribir nada.
2. Haz una exploración larga del repo; luego pide la misma información pero diciendo *"usa un subagente para explorar y devuélveme solo un resumen"*. Compara el contexto consumido.
3. Escribe la descripción de una herramienta imaginaria `crear_factura` de forma vaga y luego de forma precisa (cuándo usarla, cuándo no, formato de argumentos).

## Checklist

- [ ] Sé qué ocupa espacio en la ventana de contexto.
- [ ] Uso `/clear`, `/compact` y subagentes conscientemente.
- [ ] Entiendo que las descripciones guían la elección de herramientas.

---

⬅️ [01.1](01-que-es-el-desarrollo-agentico.md) · ➡️ [01.3 · Context engineering e instrucciones](03-context-engineering-e-instrucciones.md)
