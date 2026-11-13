# 02.1 · Flujos de trabajo agénticos

## Objetivos

- Dominar los flujos de trabajo más efectivos con agentes de código.
- Saber cuál elegir según el tamaño y la ambigüedad de la tarea.
- Trabajar en paralelo con varios agentes de forma segura (git worktrees).
- Integrar agentes en revisión de código y CI.

---

## 1. Elegir el flujo según la tarea

| Tarea | Flujo recomendado |
|---|---|
| Arreglo trivial (typo, renombrado) | **Directo**: pide y revisa el diff |
| Feature pequeña/mediana clara | **Explore → Plan → Code → Commit** |
| Bug | **Reproducir → Test que falla → Arreglo → Verificar** |
| Lógica con reglas claras | **TDD con agente** |
| Feature grande o ambigua, varias personas | **Spec-driven** (OpenSpec) |
| UI | **Iteración visual** (capturas, Playwright MCP) |
| Muchas tareas independientes | **Multi-agente en paralelo** con worktrees |
| Tareas repetitivas | **Headless / CI** |

---

## 2. Flujo base: Explore → Plan → Code → Commit

### Paso 1 · Explore (sin editar)
```text
Lee los archivos relacionados con la autenticación (controladores, servicios,
middleware y tests). NO escribas código todavía. Explícame cómo funciona el
flujo de login actual y dónde se validan los tokens.
```
Usa **plan mode** (Claude Code: `Shift+Tab` hasta "plan mode"; OpenCode: agente **plan** con `Tab`) para garantizar que no edite.

### Paso 2 · Plan
```text
Quiero añadir refresh tokens. Piensa a fondo y propón un plan paso a paso:
archivos a crear/modificar, cambios de esquema, tests a añadir y riesgos.
```
- Revisa y corrige el plan. Es **10× más barato** corregir un plan que un diff.
- Para tareas grandes, pide que guarde el plan en `docs/plans/refresh-tokens.md` (o usa OpenSpec).

### Paso 3 · Code
```text
Implementa el plan. Después de cada paso ejecuta `dotnet test`.
Si un test falla, corrígelo antes de seguir.
```
Cambia a modo de edición (Claude Code: *accept edits*; OpenCode: agente **build**).

### Paso 4 · Commit / PR
```text
Revisa el diff completo buscando errores, código muerto y secretos.
Luego crea un commit con Conventional Commits y abre un PR con descripción.
```

---

## 3. Flujo de bugs: reproducir primero

1. *"Escribe un test que reproduzca el bug: al crear una tarea con fecha en UTC-5 se guarda un día antes."*
2. Verifica que **el test falla por la razón correcta**.
3. *"Ahora arregla el código para que el test pase, sin modificar el test."*
4. *"Ejecuta toda la suite para comprobar que no hay regresiones."*

---

## 4. TDD con agentes (Red → Green → Refactor)

```text
Vamos a hacer TDD para la función calcularDescuento(carrito).
Reglas: 10% si total > 100; 15% si además es cliente premium; nunca > 50€.
1) Escribe SOLO los tests (pytest) cubriendo casos normales y bordes. No implementes.
2) Ejecútalos y confirma que fallan.
```
Revisa los tests (son tu especificación). Luego:
```text
Implementa el código mínimo para que pasen. No modifiques los tests.
```
Finalmente: *"Refactoriza manteniendo los tests en verde."*

> ⚠️ Vigila el "gaming" de tests: el agente podría ajustar los tests o poner casos especiales. Instrucción útil en `AGENTS.md`: **"Nunca modifiques un test para que pase sin pedirme permiso."** Detalle en [07.1](../07-testing/01-pruebas-unitarias-con-ia.md).

---

## 5. Spec-driven development (SDD)

Para cambios grandes: primero se acuerda **qué** se construye en documentos versionados (propuesta, requisitos con escenarios, diseño, tareas), y el agente implementa contra eso.

```
/opsx:explore  →  /opsx:propose  →  revisión humana  →  /opsx:apply  →  /opsx:archive
```

Ventajas: alineación humano–IA, trazabilidad, specs como documentación viva. Ver [06.1 · OpenSpec](../06-spec-driven/01-openspec.md).

---

## 6. Iteración visual (UI)

1. Da una referencia visual (captura/mock) o describe el diseño.
2. El agente implementa.
3. El agente **ve** el resultado: Playwright MCP o Chrome DevTools MCP toman capturas/snapshots.
4. Compara y repite 2–3 veces.

```text
Implementa la pantalla según la imagen adjunta. Luego usa Playwright MCP para
abrir http://localhost:5173/tareas, toma una captura y compárala con el diseño.
Itera hasta que coincidan espaciado y colores.
```

---

## 7. Multi-agente y trabajo en paralelo

### 7.1 Subagentes dentro de una sesión
El agente principal delega: un subagente explora, otro revisa seguridad, otro escribe tests. Cada uno con su propio contexto y devuelve solo un resumen. Ver [04.2](../04-extensibilidad/02-agentes-y-subagentes.md).

### 7.2 Varias sesiones en paralelo con git worktrees
```bash
# Un worktree por tarea, cada uno en su rama
git worktree add ../tareas-paginacion -b feat/paginacion
git worktree add ../tareas-export -b feat/export-csv

# Terminal 1
cd ../tareas-paginacion && claude
# Terminal 2
cd ../tareas-export && opencode

# Al terminar
git worktree remove ../tareas-paginacion
```
- Claude Code también puede aislar subagentes en worktrees temporales (`isolation: worktree` en el frontmatter del subagente).

### 7.3 Patrón escritor–revisor
- Sesión A implementa.
- Sesión B (contexto limpio, idealmente otro modelo) revisa el diff: *"Revisa los cambios de la rama feat/paginacion como un revisor senior exigente."*
- Pasas el feedback a A.

---

## 8. Headless y CI

Los agentes también corren sin interfaz:

```bash
# Claude Code: modo no interactivo
claude -p "Analiza los tests que fallan en el último run y propone un arreglo" \
  --output-format json

# Encadenar con otras herramientas
git diff main --name-only | claude -p "Resume el impacto de estos cambios"
```

```bash
# OpenCode: ejecutar un prompt sin TUI
opencode run "Actualiza el CHANGELOG con los commits desde el último tag"
```

Usos en CI: revisión automática de PRs, triage de issues, generación de release notes, arreglo de lint. Hay integraciones oficiales con GitHub Actions para ambos. **Siempre** con permisos mínimos y sin secretos innecesarios.

---

## 9. Ciclo de revisión humana (no negociable)

Antes de aceptar trabajo de un agente:

- [ ] ¿Leí el diff completo?
- [ ] ¿Los tests prueban comportamiento real (no solo "no lanza error")?
- [ ] ¿Se modificaron tests existentes? ¿Por qué?
- [ ] ¿Hay dependencias nuevas? ¿Son legítimas (no *typosquatting*)?
- [ ] ¿Secretos, logs con datos sensibles, `TODO` olvidados?
- [ ] ¿Pasa CI (build, tests, lint, type-check)?

---

## Errores comunes

- Saltarse el plan en tareas no triviales.
- Dejar que el agente "arregle" tests rojos cambiando las aserciones.
- Varios agentes editando la misma carpeta a la vez (usa worktrees).
- Sesiones gigantes con 5 tareas mezcladas.

## Ejercicios

1. Implementa una feature pequeña con los 4 pasos de Explore → Plan → Code → Commit. Guarda el plan en un `.md`.
   - ✅ Éxito: el plan aprobado y el diff final coinciden; tests en verde.
2. Toma un bug real (o inventa uno) y aplica el flujo "reproducir primero".
3. Crea dos worktrees y trabaja dos tareas en paralelo con dos sesiones de agente; integra ambas ramas.
4. Ejecuta un prompt en modo headless que genere un resumen del `git log` de la última semana.

## Checklist

- [ ] Elijo el flujo según tamaño y ambigüedad.
- [ ] Siempre planifico antes de tareas no triviales.
- [ ] Sé trabajar en paralelo con worktrees.
- [ ] Reviso con la checklist de la sección 9.

---

⬅️ [01.3](../01-fundamentos/03-context-engineering-e-instrucciones.md) · ➡️ [02.2 · Seguridad y buenas prácticas](02-seguridad-y-buenas-practicas.md)
