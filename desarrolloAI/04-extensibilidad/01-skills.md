# 04.1 · Skills

## Objetivos

- Entender qué es una skill y en qué se diferencia de instrucciones, subagentes y MCP.
- Crear skills con `SKILL.md`, archivos de soporte y scripts.
- Controlar cuándo se invocan (modelo vs usuario) y con qué herramientas.
- Escribir skills portables entre Claude Code y OpenCode.

---

## 1. ¿Qué es una skill?

Una **skill** es una carpeta con un archivo `SKILL.md` (frontmatter YAML + instrucciones en Markdown) y, opcionalmente, archivos de referencia, plantillas y scripts. Enseña al agente a hacer **una tarea concreta de una forma concreta**.

Clave: **divulgación progresiva** (*progressive disclosure*):
1. Al inicio, el agente solo ve `nombre + descripción` de cada skill (pocos tokens).
2. Cuando una tarea encaja con la descripción, carga el cuerpo de `SKILL.md`.
3. Si el cuerpo lo indica, lee archivos adicionales o ejecuta scripts.

Así puedes tener decenas de skills sin saturar el contexto.

### Skill vs otras piezas

| Pieza | Úsala para | Se carga |
|---|---|---|
| `AGENTS.md` | Reglas que aplican **siempre** | Siempre |
| **Skill** | Procedimientos/conocimiento que aplican **a veces** | Bajo demanda |
| Subagente | Delegar trabajo con **contexto aislado** | Cuando se delega |
| MCP | Acceso a **sistemas externos** (APIs, BD, navegador) | Descripciones de tools siempre; datos bajo demanda |
| Hook | Acción **determinista** en un evento | Automáticamente |

> En Claude Code, las skills **también son los comandos `/`**: `.claude/skills/deploy/SKILL.md` crea `/deploy` (los antiguos `.claude/commands/*.md` siguen funcionando).

---

## 2. Ubicaciones

| Herramienta | Proyecto | Personal |
|---|---|---|
| Claude Code | `.claude/skills/<nombre>/SKILL.md` | `~/.claude/skills/<nombre>/SKILL.md` |
| OpenCode | `.opencode/skills/`, **`.claude/skills/`**, `.agents/skills/` | `~/.config/opencode/skills/`, `~/.claude/skills/`, `~/.agents/skills/` |

Claude Code también carga skills de plugins (`/plugin:skill`), de subdirectorios anidados y de directorios añadidos con `--add-dir`.

> ✅ **Portabilidad:** pon tus skills de proyecto en `.claude/skills/`: las leen ambas herramientas.

---

## 3. Estructura

```
.claude/skills/crear-endpoint/
├── SKILL.md              ← obligatorio: resumen y navegación (< 500 líneas)
├── referencia.md         ← detalle, se lee solo si hace falta
├── ejemplos.md
├── plantillas/
│   └── Controller.cs.tpl
└── scripts/
    └── validar_rutas.py  ← se ejecuta, no se carga en contexto
```

---

## 4. Frontmatter

### Campos comunes (portables)
| Campo | Descripción |
|---|---|
| `name` | Nombre/comando. En Claude Code por defecto es el nombre de la carpeta; en OpenCode el ID sale de la ruta y `name` es solo visual |
| `description` | **Lo más importante**: qué hace y cuándo usarla. Sin descripción, OpenCode no la anuncia al modelo |
| `disable-model-invocation` | `true` = solo la invoca el usuario (útil para acciones con efectos: deploy, release) |

### Campos adicionales de Claude Code
| Campo | Descripción |
|---|---|
| `when_to_use` | Frases/ejemplos que deben activarla |
| `argument-hint` | Pista de autocompletado, p. ej. `[numero-issue]` |
| `arguments` | Argumentos con nombre para usar como `$nombre` |
| `user-invocable` | `false` = oculta del menú `/` (solo la usa el modelo) |
| `allowed-tools` | Herramientas pre-aprobadas durante el turno que la invoca |
| `disallowed-tools` | Herramientas retiradas mientras está activa |
| `model`, `effort` | Modelo / esfuerzo mientras está activa |
| `context: fork` + `agent` | Ejecutar la skill en un subagente aislado (`Explore`, `Plan`, `general-purpose` o uno propio) |
| `paths` | Globs que limitan cuándo se carga automáticamente |
| `hooks` | Hooks registrados al invocarla |

### Campos adicionales de OpenCode
| Campo | Descripción |
|---|---|
| `metadata.opencode/autoinvoke: false` | Oculta la skill de la lista del modelo (equivalente a `disable-model-invocation`) |

### Argumentos (Claude Code)
- `$ARGUMENTS`: todo lo escrito tras el comando.
- `$0`, `$1`… o `$ARGUMENTS[N]`: posicionales.
- `` !`comando` ``: inyecta la salida de un comando antes de enviar el prompt.

---

## 5. Escribir una buena descripción

❌ Mal:
```yaml
description: Ayuda con endpoints
```
✅ Bien:
```yaml
description: >
  Crea un endpoint REST nuevo en services/api siguiendo Clean Architecture
  (comando, handler, validador FluentValidation, controller y tests xUnit).
  Úsala cuando el usuario pida "crear/añadir un endpoint", "nueva ruta de API"
  o "exponer X por HTTP". No la uses para endpoints GraphQL.
```
Incluye: **qué hace**, **cuándo usarla** (frases típicas), **cuándo no**.

---

## 6. Ejemplos completos

### 6.1 Skill invocada por el modelo: convenciones de endpoints

`.claude/skills/crear-endpoint/SKILL.md`
```markdown
---
name: crear-endpoint
description: >
  Crea un endpoint REST en services/api siguiendo Clean Architecture con tests.
  Úsala cuando pidan crear, añadir o exponer un endpoint/ruta HTTP nueva.
---

# Crear endpoint REST

## Pasos
1. Lee `referencia.md` para las convenciones de nombres y carpetas.
2. Crea en `src/Application/<Feature>/`:
   - `<Accion><Entidad>Command.cs` (record)
   - `<Accion><Entidad>Handler.cs`
   - `<Accion><Entidad>Validator.cs` (FluentValidation)
3. Añade el endpoint en `src/Api/Endpoints/<Feature>Endpoints.cs` usando Minimal APIs.
4. Crea tests en `tests/Application.Tests/<Feature>/` (caso feliz, validación, no encontrado).
5. Ejecuta `python scripts/validar_rutas.py` para comprobar que no hay rutas duplicadas.
6. Ejecuta `dotnet test` y `dotnet format --verify-no-changes`.

## Reglas
- Nunca devuelvas entidades de dominio: usa DTOs.
- Rutas en kebab-case y plural: `/api/tareas-recurrentes`.
```

### 6.2 Skill de acción solo para el usuario: release

`.claude/skills/release/SKILL.md`
```markdown
---
name: release
description: Prepara una release: changelog, versión, tag y notas
disable-model-invocation: true
argument-hint: "[major|minor|patch]"
allowed-tools: Bash(git log *) Bash(git tag *) Bash(npm version *)
---

Prepara una release de tipo $ARGUMENTS.

Commits desde el último tag:
!`git log $(git describe --tags --abbrev=0)..HEAD --oneline`

1. Agrupa los commits en Features, Fixes y Otros (en español).
2. Actualiza CHANGELOG.md.
3. Ejecuta `npm version $ARGUMENTS`.
4. Muéstrame el resumen y NO hagas push: lo haré yo.
```
Uso: `/release minor`.

### 6.3 Skill en subagente aislado: investigación

```markdown
---
name: investigar
description: Investiga a fondo cómo funciona una parte del código y devuelve un informe con referencias
context: fork
agent: Explore
---

Investiga $ARGUMENTS:
1. Localiza archivos relevantes con Glob y Grep.
2. Lee y analiza el código.
3. Devuelve un resumen con rutas y números de línea.
```

### 6.4 Versión equivalente para OpenCode (si no quieres usar `.claude/skills`)

`.opencode/skills/release/SKILL.md`
```markdown
---
name: Release
description: Prepara una release (changelog, versión, tag y notas)
metadata:
  opencode/autoinvoke: false
---

Prepara el changelog, la subida de versión, el tag y las notas de release.
```
En OpenCode puedes cargarla escribiendo `@release` en el prompt.

---

## 7. Buenas prácticas

1. **Una skill = una tarea**. Mejor 5 skills pequeñas que 1 enorme.
2. `SKILL.md` corto (< 500 líneas); detalle en archivos referenciados explícitamente.
3. Scripts para lo determinista (validar, generar, transformar) en lugar de pedir al modelo que "lo haga a mano".
4. Incluye **criterios de verificación** en los pasos.
5. Prueba la activación: escribe 5 peticiones que deberían activarla y 5 que no.
6. Versiona las skills de proyecto en git y revísalas en PR como código.
7. Revisa skills de terceros (incluidos scripts) antes de instalarlas.

> En la app de Claude y Claude Code existe una skill integrada `skill-creator` que ayuda a crear y evaluar skills.

---

## Errores comunes

- Descripción vaga → la skill nunca se activa o se activa siempre.
- Poner en una skill reglas que deberían estar siempre (`AGENTS.md`).
- Skills con efectos (deploy) invocables por el modelo.
- Referenciar archivos de soporte sin decir *cuándo* leerlos.

## Ejercicios

1. Crea la skill `crear-endpoint` (o una equivalente para tu stack) y pide *"añade un endpoint para archivar tareas"*. Verifica que se activa sola.
2. Crea `/release` con `disable-model-invocation: true` y comprueba que el modelo no la usa solo.
3. Abre el mismo repo en OpenCode y comprueba que la skill de `.claude/skills` aparece y funciona.
4. Convierte una sección larga de tu `AGENTS.md` en una skill y mide la reducción de contexto con `/context`.
   - ✅ Éxito: el contexto inicial baja y la regla se sigue aplicando cuando corresponde.

## Checklist

- [ ] Sé cuándo usar skill vs instrucciones vs subagente vs MCP.
- [ ] Escribo descripciones que activan la skill correctamente.
- [ ] Uso archivos de soporte y scripts.
- [ ] Mis skills funcionan en Claude Code y OpenCode.

---

⬅️ [03.3](../03-herramientas/03-comparativa-claude-code-vs-opencode.md) · ➡️ [04.2 · Agentes y subagentes](02-agentes-y-subagentes.md)
