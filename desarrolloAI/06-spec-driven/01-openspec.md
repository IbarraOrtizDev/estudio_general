# 06.1 · OpenSpec y spec-driven development

## Objetivos

- Entender el *spec-driven development* (SDD) y cuándo usarlo.
- Instalar OpenSpec y configurarlo para Claude Code y OpenCode.
- Completar el ciclo **explore → propose → apply → archive**.
- Escribir requisitos y escenarios de calidad (deltas ADDED/MODIFIED/REMOVED).
- Usar el perfil expandido (`new`, `continue`, `ff`, `verify`…).

---

## 1. ¿Por qué spec-driven?

Con un prompt suelto, el agente decide muchas cosas implícitamente ("vibe coding"). Con SDD, **antes de escribir código** humano e IA acuerdan por escrito:

- **Por qué** (propuesta)
- **Qué** (requisitos con escenarios verificables)
- **Cómo** (diseño técnico)
- **Pasos** (tareas)

Beneficios: menos retrabajo, revisiones más rápidas (revisas intención antes que código), documentación viva del comportamiento del sistema, y cambios trazables.

**Úsalo** para features medianas/grandes, cambios que afectan a varias partes o cuando trabajan varias personas/agentes. **No hace falta** para arreglos triviales.

---

## 2. OpenSpec en una frase

**OpenSpec** (Fission-AI, open source) es un framework ligero de SDD: una CLI (`openspec`) + convenciones de carpetas + **comandos slash** que instala en tu asistente (Claude Code, OpenCode, Cursor, Copilot, Codex y 20+ más). Sin servidor ni daemon: solo archivos Markdown en tu repo.

> **OpenSpec 1.x** usa comandos `/opsx:*`. Los antiguos `/openspec:proposal|apply|archive` **ya no existen**. Si ves tutoriales con ellos, están desactualizados.

---

## 3. Instalación

Requiere **Node.js 20.19+**.

```bash
npm install -g @fission-ai/openspec@latest
cd mi-proyecto
openspec init
```

`openspec init` te pregunta qué herramientas usas e instala los comandos/skills correspondientes (p. ej. en `.claude/` para Claude Code y en `.opencode/` para OpenCode). Imprime la forma exacta de invocar los comandos en cada herramienta.

| Herramienta | Cómo se escribe |
|---|---|
| Claude Code | `/opsx:propose`, `/opsx:apply` |
| OpenCode | `/opsx-propose`, `/opsx-apply` (según instale `init`) |
| Cursor, Windsurf, Copilot | `/opsx-propose` |
| Codex | `$openspec-propose` |

> **Terminal vs chat:** los comandos `openspec ...` se escriben en la **terminal**; los `/opsx:...` en el **chat del agente**.

Actualizar:
```bash
npm install -g @fission-ai/openspec@latest
openspec update      # regenera comandos/instrucciones en tu proyecto
```

---

## 4. Estructura de carpetas

```
openspec/
├── config.yaml                  ← configuración y contexto del proyecto
├── specs/                       ← FUENTE DE VERDAD: cómo se comporta el sistema HOY
│   ├── tareas/
│   │   └── spec.md
│   └── autenticacion/
│       └── spec.md
└── changes/                     ← cambios en curso (propuestas)
    ├── agregar-paginacion/
    │   ├── proposal.md          ← por qué y qué cambia
    │   ├── design.md            ← decisiones técnicas
    │   ├── tasks.md             ← checklist de implementación
    │   └── specs/
    │       └── tareas/
    │           └── spec.md      ← DELTA: requisitos añadidos/modificados/eliminados
    └── archive/
        └── 2026-11-10-agregar-etiquetas/   ← cambios completados
```

Idea clave: `specs/` describe el **presente**; cada carpeta en `changes/` describe un **cambio propuesto** como *delta*. Al archivar, el delta se fusiona en `specs/`.

---

## 5. El ciclo (perfil `core`, por defecto)

```
/opsx:explore  ──►  /opsx:propose  ──►  (revisión humana)  ──►  /opsx:apply  ──►  /opsx:archive
  (opcional)        crea proposal,                           implementa         fusiona deltas
                    specs, design,                           tareas y las       en specs/ y
                    tasks                                    marca [x]          archiva
```

### 5.1 Explore (opcional, recomendado)
```text
/opsx:explore Quiero que la lista de tareas soporte miles de elementos sin ir lenta
```
Conversación para pensar opciones (paginación por cursor vs offset, scroll infinito…) **sin crear nada aún**.

### 5.2 Propose
```text
/opsx:propose agregar-paginacion
```
El agente crea `openspec/changes/agregar-paginacion/` con:

`proposal.md`
```markdown
# Propuesta: Paginación por cursor en la lista de tareas

## Por qué
Con más de 5.000 tareas, GET /api/tareas tarda > 3 s y la UI se bloquea.

## Qué cambia
- La API acepta `cursor` y `limit` y devuelve `nextCursor`.
- La UI carga páginas al hacer scroll.

## Impacto
- Specs afectadas: `tareas`
- Código: TareasEndpoints, TareasRepository, componente ListaTareas
- Compatibilidad: sin parámetros se devuelven las primeras 50 (no rompe clientes)
```

`specs/tareas/spec.md` (delta)
```markdown
## ADDED Requirements

### Requirement: Paginación por cursor
El sistema SHALL paginar el listado de tareas usando un cursor opaco.

#### Scenario: Primera página sin parámetros
- **WHEN** un cliente solicita GET /api/tareas sin parámetros
- **THEN** el sistema devuelve como máximo 50 tareas ordenadas por fecha de creación descendente
- **AND** incluye `nextCursor` si hay más resultados

#### Scenario: Límite máximo
- **WHEN** un cliente solicita `limit=500`
- **THEN** el sistema responde 400 con el mensaje "limit debe estar entre 1 y 100"

## MODIFIED Requirements

### Requirement: Listado de tareas
El sistema SHALL devolver las tareas del usuario autenticado de forma paginada.

#### Scenario: Usuario sin tareas
- **WHEN** un usuario sin tareas solicita el listado
- **THEN** el sistema devuelve una lista vacía y `nextCursor` nulo
```

`design.md`
```markdown
# Diseño
- Cursor = base64(createdAt|id) para orden estable.
- Índice compuesto (UserId, CreatedAt DESC, Id DESC).
- UI: TanStack Query `useInfiniteQuery` + IntersectionObserver.
## Alternativas descartadas
- Offset/limit: degrada con páginas profundas y es inestable ante inserciones.
```

`tasks.md`
```markdown
## 1. Backend
- [ ] 1.1 Añadir índice compuesto y migración
- [ ] 1.2 Implementar codificación/decodificación del cursor con tests
- [ ] 1.3 Actualizar TareasRepository.ListarAsync(cursor, limit)
- [ ] 1.4 Validar `limit` (1..100) y devolver 400
- [ ] 1.5 Tests de integración de los escenarios
## 2. Frontend
- [ ] 2.1 useInfiniteQuery en ListaTareas
- [ ] 2.2 Test E2E Playwright: scroll carga la segunda página
```

### 5.3 Revisión humana (el paso más importante)
Revisa y edita los archivos (a mano o pidiendo cambios al agente). Comprueba:
- ¿Cada requisito tiene escenarios **verificables**?
- ¿Se usan SHALL/MUST para lo obligatorio?
- ¿El diseño es coherente con la arquitectura?
- ¿Las tareas son pequeñas y ordenadas, e incluyen tests?

Valida el formato:
```bash
openspec validate agregar-paginacion
openspec show agregar-paginacion
```

### 5.4 Apply
```text
/opsx:apply agregar-paginacion
```
El agente implementa las tareas en orden y marca `[x]` en `tasks.md`. Puedes interrumpir y retomar: el progreso está en el archivo.

> Recomendación de OpenSpec: modelos con buen razonamiento para planificar; modelos más baratos pueden ejecutar `apply` si las tareas están bien especificadas.

### 5.5 Archive
```text
/opsx:archive agregar-paginacion
```
- Fusiona los deltas en `openspec/specs/tareas/spec.md`.
- Mueve el cambio a `openspec/changes/archive/AAAA-MM-DD-agregar-paginacion/`.

---

## 6. Perfil expandido

Para más control, activa el perfil expandido:
```bash
openspec config profile     # elegir comandos
openspec update             # aplicar
```

| Comando | Qué hace |
|---|---|
| `/opsx:new <nombre>` | Crea solo la carpeta del cambio |
| `/opsx:continue` | Genera el siguiente artefacto (paso a paso) |
| `/opsx:ff` | *Fast-forward*: genera todos los artefactos de planificación |
| `/opsx:verify` | Verifica que la implementación cumple las specs |
| `/opsx:sync` | Sincroniza deltas con las specs |
| `/opsx:bulk-archive` | Archiva varios cambios |
| `/opsx:onboard` | Guía de introducción al flujo |

Flujo expandido: `/opsx:new → /opsx:ff (o /opsx:continue) → /opsx:apply → /opsx:verify → /opsx:archive`.

---

## 7. CLI de referencia

| Comando | Para qué |
|---|---|
| `openspec init [ruta]` | Inicializar en un proyecto |
| `openspec update` | Actualizar comandos/instrucciones tras actualizar el paquete |
| `openspec list` | Listar cambios (o specs con `--specs`) |
| `openspec view` | Dashboard interactivo |
| `openspec show <nombre>` | Ver un cambio o spec |
| `openspec validate <nombre>` | Validar formato |
| `openspec status --change <nombre>` | Progreso de un cambio |
| `openspec archive <nombre> --yes` | Archivar desde la terminal |
| `openspec config profile` | Elegir perfil de comandos |

---

## 8. Escribir buenos requisitos

| ✅ Hazlo | ❌ Evítalo |
|---|---|
| "El sistema SHALL responder 400 si `limit` > 100" | "Debería validar bien los parámetros" |
| Escenarios WHEN/THEN concretos con valores | Escenarios abstractos sin datos |
| Un comportamiento por requisito | Requisitos que mezclan 5 cosas |
| Incluir casos de error y borde | Solo el camino feliz |
| Lenguaje del dominio | Detalles de implementación en la spec (van en design.md) |

> 💡 Los escenarios WHEN/THEN se traducen casi 1:1 a **tests**. Pide en `tasks.md` un test por escenario (unitario/integración/E2E).

---

## 9. OpenSpec + el resto de la guía

- **Skills/subagentes**: crea un subagente `spec-reviewer` que revise propuestas antes de `apply`.
- **TDD**: en `apply`, pide primero los tests de los escenarios.
- **Playwright**: los escenarios de UI se convierten en tests E2E (módulo 07).
- **Multi-agente**: cambios independientes en `changes/` pueden implementarse en paralelo en worktrees distintos.

---

## Errores comunes

- Saltarse la revisión de la propuesta y pasar directo a `apply`.
- Specs que describen implementación en vez de comportamiento.
- No archivar: `specs/` deja de reflejar la realidad.
- Usar comandos antiguos `/openspec:*`.

## Ejercicios

1. Instala OpenSpec en el proyecto de tareas (o uno propio) e inicialízalo para Claude Code **y** OpenCode.
2. Completa un ciclo entero con un cambio pequeño (p. ej. "etiquetas en tareas").
   - ✅ Éxito: `openspec/specs/` contiene el nuevo requisito y el cambio está en `archive/`.
3. Reescribe 3 requisitos vagos de tu proyecto actual en formato Requirement + Scenarios.
4. Activa el perfil expandido y usa `/opsx:verify` tras implementar.

## Checklist

- [ ] Entiendo specs (presente) vs changes (deltas).
- [ ] Completé propose → apply → archive.
- [ ] Escribo requisitos con SHALL y escenarios WHEN/THEN.
- [ ] Sé usar la CLI y el perfil expandido.

---

⬅️ [05.6](../05-mcp/06-mcp-configuracion-en-clientes.md) · ➡️ [07.1 · Pruebas unitarias con IA](../07-testing/01-pruebas-unitarias-con-ia.md)
