# 04.2 · Agentes y subagentes

## Objetivos

- Entender qué es un subagente y por qué mejora calidad y contexto.
- Crear subagentes en Claude Code y en OpenCode.
- Diseñar equipos de agentes (revisor, tester, explorador, documentador…).
- Conocer patrones de orquestación multi-agente.

---

## 1. ¿Qué es un subagente?

Un **subagente** es un agente especializado que el agente principal invoca para una subtarea. Tiene:

- **Su propia ventana de contexto** (no ve tu conversación, solo la tarea que le delegan).
- **Su propio system prompt** (el cuerpo del archivo `.md`).
- **Herramientas/permisos propios** (p. ej. solo lectura).
- Opcionalmente **otro modelo** (rápido para explorar, potente para revisar).

Devuelve al principal **solo un resumen**, lo que mantiene limpio el contexto principal.

```
Agente principal (tu sesión)
 ├─► subagente "explorador"   → "Los pagos se procesan en src/pagos/... (resumen)"
 ├─► subagente "test-writer"  → "Añadí 8 tests, todos pasan"
 └─► subagente "revisor"      → "2 hallazgos altos, 1 medio"
```

### Cuándo usar subagentes
- Exploración que leería muchos archivos.
- Tareas con un rol claro y repetible (revisar, testear, documentar, auditar seguridad).
- Trabajo en paralelo sobre partes independientes.
- Obtener una "segunda opinión" sin el sesgo del contexto principal.

### Cuándo no
- Tareas pequeñas (el coste de arranque no compensa).
- Cuando la subtarea necesita todo el contexto de la conversación.

---

## 2. Subagentes en Claude Code

### Integrados
| Subagente | Para qué |
|---|---|
| **Explore** | Búsqueda rápida de solo lectura en el código |
| **Plan** | Investigación de solo lectura durante plan mode |
| **general-purpose** | Tareas multi-paso con exploración y modificación |
| statusline-setup, claude-code-guide | Utilidades |

### Ubicaciones (de mayor a menor prioridad)
Políticas gestionadas → flag `--agents` → `.claude/agents/` (proyecto) → `~/.claude/agents/` (usuario) → plugins.

### Formato
```markdown
---
name: code-reviewer
description: >
  Revisor de código senior. Úsalo PROACTIVAMENTE después de cualquier cambio
  de código significativo y antes de hacer commit.
tools: Read, Glob, Grep, Bash
model: sonnet
---

Eres un revisor de código senior, exigente pero constructivo.

Cuando te invoquen:
1. Ejecuta `git diff` (y `git diff --staged`) para ver los cambios.
2. Revisa: corrección, casos borde, manejo de errores, seguridad (inyección,
   secretos, validación), rendimiento, legibilidad y cobertura de tests.
3. Comprueba que no se han debilitado tests existentes.

Formato de salida:
## Crítico (debe arreglarse)
## Importante (debería arreglarse)
## Sugerencias
Cada hallazgo con `archivo:línea`, explicación y propuesta concreta.
No edites archivos.
```

### Campos del frontmatter (Claude Code)
| Campo | Descripción |
|---|---|
| `name` *(obligatorio)* | Identificador único |
| `description` *(obligatorio)* | Cuándo delegar. "Úsalo proactivamente…" fomenta la delegación automática |
| `tools` | Lista permitida (si se omite, hereda todas, incluidas MCP) |
| `disallowedTools` | Lista denegada |
| `model` | `sonnet`, `opus`, `haiku`, ID completo o `inherit` |
| `permissionMode` | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | Límite de iteraciones |
| `skills` | Skills precargadas en su contexto |
| `mcpServers` | Servidores MCP propios del subagente |
| `hooks` | Hooks con alcance de subagente |
| `memory` | Memoria persistente: `user`, `project` o `local` |
| `isolation` | `worktree` = trabaja en un git worktree temporal |
| `background`, `effort`, `color`, `omitClaudeMd` | Comportamiento y presentación |

### Invocación
- **Automática**: el principal delega cuando la tarea encaja con la `description`.
- **Explícita**: *"Usa el subagente code-reviewer para revisar mis cambios."*
- Crearlos: pide a Claude *"crea un subagente para X"* o edita los archivos directamente (`/agents` te orienta).
- Deshabilitar uno: añade `Agent(nombre)` a `permissions.deny`.

---

## 3. Agentes y subagentes en OpenCode

### Integrados
**build** y **plan** (primarios, se alternan con `Tab`), **general** y **explore** (subagentes).

### Ubicaciones
`.opencode/agents/<nombre>.md` (proyecto) y `~/.config/opencode/agents/<nombre>.md` (global), o la clave `agents` en `opencode.json`.

### Formato (V2)
```markdown
---
description: >
  Revisor de código senior. Úsalo después de cambios significativos y antes de commit.
mode: subagent
model: anthropic/claude-sonnet-5-5
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

(mismo cuerpo que la versión de Claude Code)
```

| Campo | Descripción |
|---|---|
| `description` | Cuándo usarlo |
| `mode` | `primary` (agente principal seleccionable con `Tab`), `subagent` o `all` |
| `model` | `proveedor/modelo[#variante]` |
| `permissions` | Reglas `{action, resource, effect}` |
| `steps` | Límite de pasos |
| `hidden`, `disabled`, `color` | Presentación/estado |

> **Agentes primarios propios**: en OpenCode puedes crear agentes *primarios* nuevos (p. ej. `docs-writer` o `architect`) y alternarlos con `Tab` igual que build/plan.

---

## 4. Equipo de agentes recomendado

| Agente | Herramientas | Modelo | Rol |
|---|---|---|---|
| `explorador` | Solo lectura | Rápido | Mapear código y devolver resúmenes con rutas |
| `arquitecto` | Solo lectura | Potente | Proponer diseños y planes, evaluar trade-offs |
| `test-writer` | Lectura, edición en `tests/**`, comandos de test | Equilibrado | Escribir tests (sin tocar código de producción) |
| `code-reviewer` | Lectura + `git diff` | Potente | Revisión de calidad |
| `security-auditor` | Lectura + herramientas SAST | Potente | OWASP, secretos, dependencias |
| `docs-writer` | Lectura, edición en `docs/**` | Rápido | Documentación y changelogs |
| `e2e-tester` | Playwright MCP + comandos de test | Equilibrado | Probar flujos en navegador |

Plantillas en [`plantillas/`](../plantillas/README.md).

---

## 5. Patrones de orquestación

### 5.1 Pipeline secuencial
```text
Implementa la feature X siguiendo este proceso:
1. Usa el subagente `explorador` para localizar el código relevante.
2. Implementa los cambios.
3. Usa `test-writer` para añadir tests.
4. Usa `code-reviewer`; corrige los hallazgos críticos e importantes.
5. Resume lo hecho.
```
Puedes empaquetar este proceso en una **skill** (`/feature`) para reutilizarlo.

### 5.2 Fan-out en paralelo
```text
Usa 3 subagentes en paralelo para analizar los módulos auth, pagos y notificaciones.
Cada uno debe devolver: responsabilidades, dependencias y deuda técnica.
Luego consolida un informe.
```

### 5.3 Escritor–revisor con aislamiento
El implementador trabaja; el revisor tiene contexto limpio (subagente o sesión aparte, idealmente otro modelo).

### 5.4 Agentes en worktrees
Con `isolation: worktree` (Claude Code), cada subagente trabaja en un worktree temporal, evitando conflictos de archivos al paralelizar.

### 5.5 Equipos de agentes y orquestación externa
Claude Code incluye funcionalidades experimentales de *agent teams* (varios agentes coordinados) y puedes orquestar agentes desde scripts usando el modo headless o el **Claude Agent SDK**; OpenCode expone un servidor/SDK para lo mismo.

---

## Errores comunes

- Descripción genérica → nunca se delega (o se delega todo).
- Dar herramientas de escritura a un revisor.
- Subagentes que necesitan contexto que no reciben: la tarea delegada debe ser autocontenida.
- Demasiados subagentes con descripciones largas → ocupan contexto al arrancar.

## Ejercicios

1. Crea `code-reviewer` en Claude Code **y** en OpenCode. Introduce a propósito un bug (p. ej. SQL concatenado) y comprueba que ambos lo detectan.
2. Crea `test-writer` restringido a editar `tests/**` y pídele cubrir un módulo sin tests.
   - ✅ Éxito: solo se modifican archivos de `tests/` y la cobertura sube.
3. Crea una skill `/feature` que orqueste explorador → implementación → test-writer → reviewer.
4. Lanza un fan-out de 3 subagentes sobre tu repo y compara el contexto consumido con hacerlo en la sesión principal.

## Checklist

- [ ] Sé cuándo un subagente aporta valor.
- [ ] Creé subagentes con permisos mínimos en ambas herramientas.
- [ ] Apliqué al menos dos patrones de orquestación.

---

⬅️ [04.1](01-skills.md) · ➡️ [04.3 · Hooks, comandos y plugins](03-hooks-comandos-y-plugins.md)
