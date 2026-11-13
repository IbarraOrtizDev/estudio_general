# 00 · Ruta de aprendizaje

> **Para quién es esta guía:** desarrolladores con experiencia intermedia (ya programas en al menos uno de Python, JavaScript/TypeScript o C#, usas git y la terminal) que quieren dominar el **desarrollo de software asistido por IA de forma agéntica**.
>
> **Versiones verificadas:** noviembre de 2026. Ver la nota de versiones al final.

---

## 1. ¿Qué vas a aprender?

Al terminar la ruta serás capaz de:

1. Explicar cómo funciona un **agente de código** (loop de razonamiento + herramientas + contexto).
2. Escribir **instrucciones de proyecto** efectivas (`CLAUDE.md`, `AGENTS.md`) y aplicar *context engineering*.
3. Aplicar **flujos de trabajo** probados: *Explore → Plan → Code → Commit*, TDD con agentes, *spec-driven development*, trabajo multi-agente.
4. Usar con fluidez **Claude Code** y **OpenCode**, y elegir cuál conviene en cada caso.
5. Crear **skills**, **subagentes**, **comandos**, **hooks** y **plugins**.
6. Construir **servidores y clientes MCP** en **Python, Node.js (TypeScript) y C#**, y conectarlos a cualquier cliente.
7. Dirigir cambios con **OpenSpec** (propuesta → specs → diseño → tareas → implementación → archivo).
8. Generar y mantener **pruebas unitarias** con IA, y **pruebas E2E en el navegador con Playwright** (incluyendo Playwright MCP y los *Playwright Test Agents*).
9. Integrarlo todo en un **proyecto real** de principio a fin.
10. Ejecutar agentes con **aislamiento serio** (sandbox, Dev Containers, microVMs).
11. **Evaluar y observar** agentes, skills y tools con datos (evals, OpenTelemetry).
12. Aplicar **RAG** y **memoria persistente** en agentes de código y en agentes propios.

---

## 2. Mapa del conocimiento

```
                    ┌─────────────────────────────┐
                    │ 01 Fundamentos              │
                    │ agentes · LLMs · contexto    │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │ 02 Flujos de trabajo         │
                    │ + seguridad y buenas prácticas│
                    └──────────────┬──────────────┘
                                   │
               ┌───────────────────▼───────────────────┐
               │ 03 Herramientas: Claude Code · OpenCode │
               └───────────────────┬───────────────────┘
                                   │
               ┌───────────────────▼───────────────────┐
               │ 04 Extensibilidad: skills · agentes ·   │
               │    hooks · comandos · plugins           │
               └─────────┬─────────────────────┬───────┘
                         │                     │
         ┌───────────────▼──────┐   ┌──────────▼──────────────┐
         │ 05 MCP               │   │ 06 OpenSpec              │
         │ Python · Node · C#   │   │ spec-driven development  │
         └───────────────┬──────┘   └──────────┬──────────────┘
                         │                     │
                    ┌────▼─────────────────────▼────┐
                    │ 07 Testing: unitarias · E2E    │
                    │ Playwright · Playwright MCP    │
                    └──────────────┬────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │ 08 Proyecto integrador       │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │ 09 Avanzado: aislamiento ·   │
                    │ evals/observabilidad · RAG y │
                    │ memoria                      │
                    └─────────────────────────────┘
```

---

## 3. Plan sugerido (10 semanas, ~6–8 h/semana)

| Semana | Módulos | Entregable al final de la semana |
|---|---|---|
| 1 | `01-fundamentos/*` | Un `AGENTS.md`/`CLAUDE.md` real para uno de tus repos |
| 2 | `02-flujos-de-trabajo/*` + `03-herramientas/01-claude-code.md` | Una feature pequeña hecha con *Explore → Plan → Code → Commit* |
| 3 | `03-herramientas/02-opencode.md`, `03-comparativa…` | La misma tarea hecha en OpenCode; notas de comparación |
| 4 | `04-extensibilidad/*` | 1 skill, 1 subagente revisor y 1 hook funcionando en tu repo |
| 5 | `05-mcp/01…03` | Servidor MCP en Python **y** en Node conectados a Claude Code |
| 6 | `05-mcp/04…06` | Servidor MCP en C# + un cliente propio (en el lenguaje que prefieras) |
| 7 | `06-spec-driven/*` + `07-testing/01` | Un cambio completo con OpenSpec + suite unitaria generada con TDD |
| 8 | `07-testing/02…03` + `08-proyecto-integrador` | Proyecto integrador con pruebas E2E en CI |
| 9 | `09-avanzado/01` + `09-avanzado/02` | TaskFlow en un Dev Container con firewall + evals en CI + métricas OTel |
| 10 | `09-avanzado/03` | Servidor MCP de RAG sobre tu documentación + patrón de memoria del equipo |

**Ritmo intensivo (2 semanas):** días 1–2 fundamentos y flujos; días 3–4 herramientas; día 5 extensibilidad; días 6–8 MCP; día 9 OpenSpec; días 10–11 testing; días 12–14 proyecto; días 15–18 temas avanzados (aislamiento, evals/observabilidad, RAG y memoria).

---

## 4. Prerrequisitos técnicos

Instala antes de empezar (todo multiplataforma; en Windows se recomienda PowerShell 7 o WSL2):

| Herramienta | Versión mínima | Para qué |
|---|---|---|
| Git | 2.40+ | Control de versiones, worktrees |
| Node.js | **20+** (ideal 22/24 LTS) | Claude Code (npm), OpenSpec, MCP TS SDK v2, Playwright |
| Python | **3.11+** | MCP Python SDK v2 |
| `uv` | reciente | Gestor de proyectos Python (recomendado por el SDK de MCP) |
| .NET SDK | **8.0+** (ideal 10) | MCP C# SDK |
| VS Code | reciente | Editor; Playwright y agentes de VS Code |
| Cuenta de proveedor LLM | — | Claude (Pro/Max/API) para Claude Code; OpenCode admite muchos proveedores |

Comprobación rápida:

```bash
git --version && node -v && python --version && uv --version && dotnet --version
```

---

## 5. Cómo estudiar cada módulo

Cada archivo sigue la misma estructura:

1. **Objetivos** – qué sabrás hacer.
2. **Conceptos** – la teoría mínima necesaria.
3. **Práctica guiada** – código/comandos completos para copiar y ejecutar.
4. **Errores comunes** – lo que suele salir mal.
5. **Ejercicios** – con criterios de éxito verificables.
6. **Checklist** – autoevaluación antes de avanzar.

> 💡 **Regla de oro:** no avances de módulo sin completar los ejercicios. El desarrollo agéntico se aprende *haciendo* y *revisando* lo que hace el agente.

---

## 6. Checklist global de progreso

- [ ] 01 · Entiendo el loop agéntico y la ventana de contexto
- [ ] 01 · Tengo un archivo de instrucciones de proyecto bien escrito
- [ ] 02 · Aplico Explore → Plan → Code → Commit sin pensarlo
- [ ] 02 · Conozco los riesgos (prompt injection, secretos, permisos)
- [ ] 03 · Uso Claude Code (modos de permiso, plan mode, headless)
- [ ] 03 · Uso OpenCode (agentes build/plan, proveedores, permisos)
- [ ] 04 · Creé skills, subagentes, comandos y hooks
- [ ] 05 · Construí servidores MCP en Python, Node y C#
- [ ] 05 · Construí un cliente MCP y lo conecté a un LLM
- [ ] 06 · Completé un ciclo OpenSpec propose → apply → archive
- [ ] 07 · Hice TDD con un agente (unitarias)
- [ ] 07 · Tengo pruebas E2E Playwright corriendo en CI
- [ ] 07 · Usé Playwright MCP y los Test Agents (planner/generator/healer)
- [ ] 08 · Terminé el proyecto integrador
- [ ] 09 · Ejecuto agentes autónomos solo en entornos aislados
- [ ] 09 · Tengo evals con umbral en CI y métricas de uso/coste
- [ ] 09 · Construí RAG vía MCP y uso memoria persistente con criterio

---

## 7. Nota sobre versiones (importante)

El ecosistema cambia muy rápido. Puntos verificados en noviembre de 2026:

- **MCP**: la especificación vigente es **2026-07-28** (núcleo *stateless*, sin handshake `initialize`, descubrimiento con `server/discover`; *roots*, *sampling* y *logging* quedan deprecados). Los SDK oficiales ya la soportan:
  - Python: paquete `mcp` **2.x** (clase `MCPServer`; en 1.x era `FastMCP`).
  - TypeScript: paquetes **v2** `@modelcontextprotocol/server` y `@modelcontextprotocol/client` (el v1 `@modelcontextprotocol/sdk` queda en mantenimiento).
  - C#: `ModelContextProtocol` **2.x** (HTTP *stateless* por defecto).
- **OpenCode 2.x** es la línea actual (configuración V1 sigue siendo compatible).
- **Claude Code** lee `AGENTS.md` cuando no existe `CLAUDE.md` (desde v2.1.277). Los *custom commands* se unificaron con las *skills*.
- **OpenSpec 1.x** usa los comandos `/opsx:*` (los antiguos `/openspec:*` desaparecieron).
- **Playwright 1.56+** incluye los *Test Agents* (planner, generator, healer).

Si algo no coincide con lo que ves, consulta la documentación oficial enlazada en [`referencia/recursos-y-fuentes.md`](referencia/recursos-y-fuentes.md).

---

➡️ **Siguiente:** [01 · ¿Qué es el desarrollo agéntico?](01-fundamentos/01-que-es-el-desarrollo-agentico.md)
