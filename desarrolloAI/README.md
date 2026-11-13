# 🤖 Desarrollo de software asistido por IA (agéntico)

Guía completa en español para aprender a desarrollar software con **agentes de IA**: flujos de trabajo, instrucciones, skills, agentes, MCP (servidor y cliente en **Python, Node.js y C#**), **OpenSpec**, **Claude Code**, **OpenCode** y pruebas con **Playwright**.

> **Nivel:** desarrollador intermedio · **Duración:** ~10 semanas (o 3 en modo intensivo) · **Actualizada:** noviembre 2026

---

## 🚀 Empieza aquí

1. Lee la **[Ruta de aprendizaje](00-ruta-de-aprendizaje.md)**: objetivos, prerrequisitos, plan semanal y nota de versiones.
2. Sigue los módulos **en orden** (cada archivo enlaza al siguiente).
3. Haz los **ejercicios** y marca la **checklist** de cada módulo antes de avanzar.
4. Usa las **[plantillas](plantillas/README.md)** en tus propios proyectos.
5. Ten a mano la **[referencia](#-referencia-rápida)** (glosario y cheatsheets).

---

## 📚 Índice en orden de estudio

### Fase 1 · Fundamentos
| # | Módulo | Aprenderás |
|---|---|---|
| 01.1 | [¿Qué es el desarrollo agéntico?](01-fundamentos/01-que-es-el-desarrollo-agentico.md) | Loop agéntico, piezas de un agente, niveles de autonomía, qué delegar |
| 01.2 | [LLMs, contexto y tokens](01-fundamentos/02-llms-contexto-y-tokens.md) | Tokens, ventana de contexto, tool use, gestión de contexto, elección de modelo |
| 01.3 | [Context engineering e instrucciones](01-fundamentos/03-context-engineering-e-instrucciones.md) | `AGENTS.md`, `CLAUDE.md`, rules, prompts C-O-R-V |

### Fase 2 · Flujos de trabajo
| # | Módulo | Aprenderás |
|---|---|---|
| 02.1 | [Flujos de trabajo agénticos](02-flujos-de-trabajo/01-flujos-de-trabajo-agenticos.md) | Explore→Plan→Code→Commit, bugs, TDD, SDD, UI, multi-agente, worktrees, headless/CI |
| 02.2 | [Seguridad y buenas prácticas](02-flujos-de-trabajo/02-seguridad-y-buenas-practicas.md) | Prompt injection, permisos, aislamiento, secretos, evaluar MCP/skills |

### Fase 3 · Herramientas
| # | Módulo | Aprenderás |
|---|---|---|
| 03.1 | [Claude Code](03-herramientas/01-claude-code.md) | Instalación, interfaz, modos de permiso, sesiones, configuración, headless |
| 03.2 | [OpenCode](03-herramientas/02-opencode.md) | OpenCode 2.x, proveedores, agentes build/plan, `opencode.json` V2 |
| 03.3 | [Comparativa Claude Code vs OpenCode](03-herramientas/03-comparativa-claude-code-vs-opencode.md) | Equivalencias, cuándo usar cada uno, configuración compartida |

### Fase 4 · Extensibilidad
| # | Módulo | Aprenderás |
|---|---|---|
| 04.1 | [Skills](04-extensibilidad/01-skills.md) | `SKILL.md`, divulgación progresiva, invocación, portabilidad |
| 04.2 | [Agentes y subagentes](04-extensibilidad/02-agentes-y-subagentes.md) | Subagentes en ambas herramientas, equipos de agentes, orquestación |
| 04.3 | [Hooks, comandos y plugins](04-extensibilidad/03-hooks-comandos-y-plugins.md) | Hooks deterministas, comandos `/`, plugins y marketplaces |

### Fase 5 · MCP (Model Context Protocol)
| # | Módulo | Aprenderás |
|---|---|---|
| 05.1 | [Conceptos de MCP](05-mcp/01-mcp-conceptos.md) | Arquitectura, tools/resources/prompts, transportes, spec 2026-07-28, diseño de tools |
| 05.2 | [Servidor MCP en Python](05-mcp/02-mcp-servidor-python.md) | SDK `mcp` 2.x (`MCPServer`), salida estructurada, tests |
| 05.3 | [Servidor MCP en Node.js](05-mcp/03-mcp-servidor-nodejs.md) | SDK TS v2, Zod v4, stdio y HTTP, Vitest |
| 05.4 | [Servidor MCP en C#](05-mcp/04-mcp-servidor-csharp.md) | `ModelContextProtocol` 2.x, atributos, DI, ASP.NET Core, xUnit |
| 05.5 | [Clientes MCP y tu propio agente](05-mcp/05-mcp-clientes-python-node-csharp.md) | Clientes en 3 lenguajes, agente LLM + MCP |
| 05.6 | [Configurar MCP en clientes](05-mcp/06-mcp-configuracion-en-clientes.md) | Claude Code, OpenCode, VS Code, Claude Desktop, diagnóstico |

### Fase 6 · Spec-driven development
| # | Módulo | Aprenderás |
|---|---|---|
| 06.1 | [OpenSpec](06-spec-driven/01-openspec.md) | `/opsx:explore→propose→apply→archive`, specs y deltas, CLI |

### Fase 7 · Testing
| # | Módulo | Aprenderás |
|---|---|---|
| 07.1 | [Pruebas unitarias con IA](07-testing/01-pruebas-unitarias-con-ia.md) | pytest, Vitest, xUnit, TDD con agentes, Vitest Browser Mode, mutation testing |
| 07.2 | [Playwright E2E: fundamentos](07-testing/02-playwright-e2e-fundamentos.md) | Config, localizadores, aserciones, POM, auth, red, depuración, CI, Python/.NET |
| 07.3 | [Playwright con IA](07-testing/03-playwright-con-ia-mcp-y-test-agents.md) | Playwright MCP, Test Agents (planner/generator/healer) |

### Fase 8 · Integración
| # | Módulo | Aprenderás |
|---|---|---|
| 08 | [Proyecto integrador "TaskFlow"](08-proyecto-integrador/01-proyecto-integrador.md) | Todo junto: OpenSpec + MCP + agentes + tests + CI, con rúbrica |

### Fase 9 · Temas avanzados
| # | Módulo | Aprenderás |
|---|---|---|
| 09.1 | [Aislamiento serio: sandbox, Dev Containers y Docker Sandboxes](09-avanzado/01-aislamiento-sandbox-devcontainers-docker.md) | Sandbox de Bash (FS, red, credenciales), Dev Containers con firewall, microVMs, Windows/WSL2 |
| 09.2 | [Evaluación y observabilidad](09-avanzado/02-evaluacion-y-observabilidad.md) | Evals de tools/skills/subagentes/agente, promptfoo, CI, OpenTelemetry, trazas, KPIs |
| 09.3 | [Patrones RAG y memoria persistente](09-avanzado/03-rag-y-memoria-persistente.md) | RAG vs búsqueda agéntica, RAG como servidor MCP, Recall@k, CLAUDE.md/rules/auto memory, memory tool |

---

## 🧰 Plantillas

Listas para copiar: [`plantillas/`](plantillas/README.md)
- `AGENTS.md`, `CLAUDE.md`
- Claude Code: `settings.json`, hooks, skills, subagentes (`code-reviewer`, `test-writer`, `e2e-tester`)
- OpenCode: `opencode.jsonc` V2, agentes, comandos
- MCP: `.mcp.json`, `.vscode/mcp.json`, Claude Desktop
- OpenSpec: plantilla de cambio (proposal, design, tasks, delta spec)
- Playwright: config, auth setup, seed

## 📖 Referencia rápida

| Recurso | |
|---|---|
| [Glosario inglés → español](referencia/glosario.md) | Todos los términos técnicos |
| [Cheatsheet Claude Code](referencia/cheatsheet-claude-code.md) | Comandos, atajos, archivos, MCP, hooks |
| [Cheatsheet OpenCode](referencia/cheatsheet-opencode.md) | TUI, config V2, permisos, MCP, V1→V2 |
| [Cheatsheet MCP](referencia/cheatsheet-mcp.md) | SDKs v2 en Python, TS y C#; configuración en clientes |
| [Cheatsheet OpenSpec](referencia/cheatsheet-openspec.md) | CLI, comandos `/opsx`, formato de specs |
| [Cheatsheet Playwright](referencia/cheatsheet-playwright.md) | CLI, localizadores, aserciones, MCP, agentes |
| [Recursos y fuentes oficiales](referencia/recursos-y-fuentes.md) | Enlaces a documentación oficial |

---

## 🗂️ Estructura de la carpeta

```
desarrolloAI/
├── README.md                     ← este índice
├── 00-ruta-de-aprendizaje.md
├── 01-fundamentos/
├── 02-flujos-de-trabajo/
├── 03-herramientas/
├── 04-extensibilidad/
├── 05-mcp/
├── 06-spec-driven/
├── 07-testing/
├── 08-proyecto-integrador/
├── 09-avanzado/
├── plantillas/
└── referencia/
```

> 💡 **Consejo:** abre esta carpeta en VS Code (o Obsidian) para navegar los enlaces y ver los diagramas en vista previa de Markdown. Y úsala con tu agente: *"Lee 05-mcp/02-mcp-servidor-python.md y ayúdame a hacer el ejercicio 2"*.
