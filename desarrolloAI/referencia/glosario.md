# Glosario (inglés → español)

Los términos técnicos se mantienen en inglés en la guía; aquí su significado.

| Término | Significado |
|---|---|
| **Agent / agente** | Sistema que usa un LLM en un loop para planificar, ejecutar herramientas y observar resultados hasta cumplir un objetivo |
| **Agentic loop** | Ciclo razonar → actuar (tool call) → observar → repetir |
| **AGENTS.md** | Archivo estándar de instrucciones de proyecto para agentes de código |
| **Annotations (MCP)** | Metadatos de una tool (`readOnlyHint`, `destructiveHint`…) que ayudan al host a decidir permisos |
| **Archive (OpenSpec)** | Fusionar los deltas de un cambio en `specs/` y moverlo a `changes/archive/` |
| **Agentic search** | Búsqueda del agente con herramientas (grep, glob, read) en lugar de un índice vectorial |
| **Assertion** | Comprobación en un test (`expect(...)`, `Assert.Equal`) |
| **Auto-waiting** | Playwright espera automáticamente a que los elementos estén listos |
| **Auto memory** | Notas que Claude Code escribe para sí mismo por proyecto (`~/.claude/projects/<p>/memory/`) |
| **BM25** | Algoritmo clásico de búsqueda por palabras clave; se combina con vectores en búsqueda híbrida |
| **Checkpoint / rewind** | Punto de restauración del código/conversación en Claude Code |
| **CLAUDE.md** | Archivo de instrucciones/memoria de Claude Code |
| **Chunking** | Dividir documentos en fragmentos para indexarlos en RAG |
| **Codegen** | Herramienta de Playwright que graba acciones y genera código |
| **Compaction / compact** | Resumir la conversación para liberar ventana de contexto |
| **Context engineering** | Diseñar todo lo que el modelo ve: instrucciones, archivos, tools, skills, ejemplos |
| **Contextual retrieval** | Añadir a cada chunk un resumen de su contexto antes de indexarlo para mejorar la recuperación |
| **Context window** | Máximo de tokens que el modelo procesa a la vez |
| **Dataset (eval)** | Conjunto de casos de entrada y resultado esperado para evaluar |
| **Delta spec** |
| **Dev Container** | Entorno de desarrollo en contenedor definido en `.devcontainer/devcontainer.json` | En OpenSpec, requisitos ADDED/MODIFIED/REMOVED de un cambio |
| **E2E (end-to-end)** | Pruebas del sistema completo desde la perspectiva del usuario |
| **Egress firewall** | Restricción del tráfico de red saliente a dominios permitidos |
| **Elicitation** |
| **Embedding** | Vector numérico que representa el significado de un texto |
| **Eval** | Evaluación repetible de un sistema de IA con dataset, graders y métricas | Mecanismo MCP para que el servidor pida información al usuario |
| **Fixture** | Recurso preparado para tests (página, datos, sesión) e inyectado en ellos |
| **Fork (context: fork)** | Ejecutar una skill en un subagente aislado |
| **Frontmatter** | Bloque YAML entre `---` al inicio de un Markdown (skills, agentes, comandos) |
| **Faithfulness** | Grado en que una respuesta RAG se apoya solo en los fragmentos recuperados |
| **Grader** | Calificador de una eval: por código, LLM-as-judge o humano |
| **Hallucination** | Respuesta plausible pero inventada |
| **Harness** | Programa que ejecuta el loop agéntico (Claude Code, OpenCode) |
| **Headless** | Sin interfaz (agente con `-p`/`run`; navegador sin ventana) |
| **Healer** | Agente de Playwright que repara tests fallidos |
| **Hook** | Comando que se ejecuta automáticamente en un evento del ciclo de vida |
| **Host (MCP)** | Aplicación que contiene el LLM y los clientes MCP |
| **LLM-as-judge** | Usar un LLM con una rúbrica para puntuar salidas de otro |
| **Locator** | Forma de encontrar elementos en Playwright (`getByRole`…) |
| **Marketplace** | Catálogo de plugins de Claude Code |
| **MCP** | Model Context Protocol: protocolo estándar para conectar IA con herramientas y datos |
| **Memory poisoning** | Contenido malicioso guardado en la memoria del agente que luego reutiliza |
| **Memory tool** | Herramienta de la API de Claude para leer/escribir archivos de memoria en `/memories` |
| **MicroVM** | Máquina virtual ligera con kernel propio (p. ej. Docker Sandboxes) |
| **MCP Inspector** | Herramienta visual para probar servidores MCP |
| **Managed settings** | Configuración impuesta por la organización con máxima prioridad |
| **Mock / fake / stub** | Sustitutos de dependencias en tests |
| **MRTR** | Multi Round-Trip Requests: mecanismo de MCP 2026-07-28 para pedir input adicional |
| **Mutation testing** | Introducir bugs artificiales para medir la eficacia de los tests |
| **Observability** | Capacidad de entender el comportamiento en ejecución mediante métricas, logs y trazas |
| **OpenTelemetry (OTel)** | Estándar abierto de telemetría (métricas, logs, trazas) |
| **pass@k / pass^k** | Éxito en al menos uno / en todos los k intentos de una tarea |
| **Plan mode** | Modo de solo lectura para investigar y planificar |
| **Planner / generator** | Agentes de Playwright que crean planes de prueba / tests |
| **Plugin** | Paquete distribuible de extensiones (skills, agentes, hooks, MCP) |
| **POM (Page Object Model)** | Patrón que encapsula páginas en clases para tests E2E |
| **Primary agent** | Agente principal seleccionable (OpenCode: build, plan) |
| **Progressive disclosure** | Cargar información por niveles solo cuando hace falta (skills) |
| **Prompt** | Mensaje/instrucción al modelo; en MCP, plantilla reutilizable |
| **Prompt injection** | Instrucciones maliciosas ocultas en contenido que el agente lee |
| **Proposal** | Documento de OpenSpec con el porqué y el qué de un cambio |
| **RAG** | Retrieval-Augmented Generation: recuperar información relevante y dársela al modelo |
| **Recall@k** | % de consultas cuyo documento correcto aparece entre los k primeros resultados |
| **Reranking** | Reordenar resultados recuperados con un modelo más preciso |
| **Resource (MCP)** | Datos de solo lectura identificados por URI |
| **Sandbox** | Entorno restringido por el SO/contenedor/VM que limita archivos, red y procesos |
| **Scenario** |
| **Span / trace** | Unidad de trabajo medida / árbol de spans de una ejecución completa | Caso WHEN/THEN que hace verificable un requisito |
| **Seed test** | Test inicial que prepara la app para los agentes de Playwright |
| **Skill** | Carpeta con `SKILL.md` que enseña al agente una tarea concreta |
| **Slash command** | Comando que empieza por `/` en el chat del agente |
| **SDD (spec-driven development)** | Acordar especificaciones antes de implementar |
| **Stateless** | Sin estado de sesión entre peticiones (MCP 2026-07-28) |
| **stdio** | Transporte MCP por entrada/salida estándar de un subproceso |
| **Storage state** | Cookies/almacenamiento guardados para reutilizar sesión en Playwright |
| **Streamable HTTP** | Transporte MCP sobre HTTP para servidores remotos |
| **Structured content** | Salida JSON tipada de una tool MCP (con `outputSchema`) |
| **Subagent** | Agente especializado con contexto propio al que se delegan tareas |
| **TDD** | Test-Driven Development: Red → Green → Refactor |
| **Token** | Unidad de texto que procesa el modelo |
| **Tool / tool call** | Función que el modelo puede invocar / la invocación concreta |
| **Tool poisoning** | Descripciones de tools manipuladas para inducir acciones maliciosas |
| **Trace viewer** | Visor de trazas de ejecución de Playwright |
| **Transport** | Canal de comunicación MCP (stdio, Streamable HTTP) |
| **Typosquatting / slopsquatting** | Paquetes maliciosos con nombres parecidos a reales / a nombres alucinados por IA |
| **Vector database** | Base de datos que almacena embeddings y busca por similitud (Chroma, Qdrant, pgvector…) |
| **Web-first assertions** | Aserciones de Playwright que reintentan hasta cumplirse |
| **Worktree (git)** | Directorio de trabajo adicional ligado al mismo repo, en otra rama |
