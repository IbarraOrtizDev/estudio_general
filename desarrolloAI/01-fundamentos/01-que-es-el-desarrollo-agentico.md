# 01.1 · ¿Qué es el desarrollo agéntico?

## Objetivos

- Distinguir entre *autocompletado*, *chat asistente* y *agente*.
- Entender el **loop agéntico** (percibir → razonar → actuar → observar).
- Conocer las piezas de un sistema agéntico: modelo, herramientas, contexto, instrucciones, permisos.
- Saber qué tareas delegar a un agente y cuáles no.

---

## 1. Tres generaciones de IA para programar

| Generación | Ejemplo | Quién decide los pasos | Qué ve la IA |
|---|---|---|---|
| **Autocompletado** | Sugerencias inline en el editor | Tú | El archivo actual |
| **Chat asistente** | Pegar código en un chat y pedir ayuda | Tú (copias/pegas) | Lo que pegas |
| **Agente** | Claude Code, OpenCode, Codex CLI, Copilot agent mode | **El agente**, dentro de límites que tú defines | El repo completo, la terminal, la web, herramientas MCP |

**Desarrollo agéntico** = delegar *objetivos* (no solo líneas de código) a un agente que **planifica, ejecuta herramientas, observa resultados y se corrige**, mientras tú actúas como arquitecto, revisor y responsable final.

---

## 2. El loop agéntico

```
         ┌──────────────────────────────────────────┐
         │                OBJETIVO                   │
         │ "Añade paginación al endpoint /tareas"    │
         └───────────────────┬──────────────────────┘
                             ▼
   ┌──────────┐   ┌──────────────────┐   ┌───────────────────┐
   │ CONTEXTO │──►│  MODELO (LLM)     │──►│ LLAMADA A TOOL     │
   │ prompt,  │   │  razona y decide  │   │ Read, Grep, Bash,  │
   │ archivos,│   │  el siguiente paso│   │ Edit, MCP...       │
   │ historial│   └──────────────────┘   └─────────┬─────────┘
   └────▲─────┘                                    │
        │            ┌────────────────────┐        │
        └────────────│ OBSERVACIÓN         │◄───────┘
                     │ salida, errores,    │
                     │ resultados de tests │
                     └────────────────────┘
          (se repite hasta cumplir el objetivo o pedir ayuda)
```

En cada iteración el modelo recibe **todo el contexto acumulado** y emite, o bien texto para ti, o bien una **llamada a herramienta** (*tool call*) con argumentos JSON. El *harness* (Claude Code, OpenCode…) ejecuta la herramienta, devuelve el resultado y vuelve a llamar al modelo.

### Pseudocódigo de un agente mínimo

```python
mensajes = [system_prompt, instrucciones_proyecto, objetivo_usuario]

while True:
    respuesta = llm(mensajes, herramientas=TOOLS)
    if respuesta.es_texto_final:
        mostrar(respuesta.texto)
        break
    for llamada in respuesta.tool_calls:
        if not permiso_concedido(llamada):        # permisos / humano en el loop
            resultado = "Permiso denegado por el usuario"
        else:
            resultado = ejecutar(llamada.nombre, llamada.args)
        mensajes.append(resultado_de_tool(llamada.id, resultado))
```

> En el módulo 05.5 construirás un agente real de este tipo conectado a servidores MCP.

---

## 3. Anatomía de un sistema agéntico

| Pieza | Qué es | Dónde lo configuras |
|---|---|---|
| **Modelo** | El LLM que razona (Claude Opus/Sonnet/Haiku, GPT, Gemini, modelos locales…) | `/model` en Claude Code; `model` en `opencode.json` |
| **Harness** | El programa que ejecuta el loop, gestiona herramientas, permisos y contexto | Claude Code, OpenCode |
| **Herramientas (tools)** | Acciones que el agente puede ejecutar: leer, editar, shell, buscar, web | Integradas + **MCP** |
| **Instrucciones** | Reglas persistentes del proyecto | `CLAUDE.md`, `AGENTS.md`, rules |
| **Skills** | Paquetes de conocimiento/procedimientos que se cargan bajo demanda | `.claude/skills/`, `.opencode/skills/` |
| **Subagentes** | Agentes especializados con su propio contexto | `.claude/agents/`, `.opencode/agents/` |
| **Hooks** | Scripts deterministas que se ejecutan en eventos del ciclo de vida | `settings.json` / plugins |
| **Permisos** | Qué puede hacer el agente sin preguntar | `settings.json`, `opencode.json` |
| **Specs** | Acuerdo explícito de *qué* construir | OpenSpec (`openspec/`) |

---

## 4. Niveles de autonomía

| Nivel | Descripción | Cuándo usarlo |
|---|---|---|
| 0 · Consulta | El agente solo lee y responde | Entender un repo nuevo |
| 1 · Propone | Planifica pero no toca archivos (*plan mode*) | Diseño, tareas ambiguas |
| 2 · Edita con aprobación | Cada edición/comando pide permiso | Código crítico, aprendizaje |
| 3 · Edita libremente | Acepta ediciones; pide permiso para comandos peligrosos | Trabajo diario en una rama |
| 4 · Autónomo | Corre sin supervisión (headless/CI), en entorno aislado | Tareas repetitivas, CI, sandbox/contenedor |

> ⚠️ **A más autonomía, más aislamiento**: ramas, *git worktrees*, contenedores, sin secretos de producción.

---

## 5. ¿Qué delegar y qué no?

**Muy buen ajuste para agentes**
- Explorar y explicar un código desconocido.
- Implementar features bien especificadas con tests de aceptación.
- Refactors mecánicos, migraciones de API/versión, renombrados masivos.
- Escribir y arreglar tests, reproducir bugs.
- Documentación, changelogs, scripts de automatización.

**Requiere mucha supervisión**
- Decisiones de arquitectura de largo plazo.
- Seguridad, criptografía, autenticación, pagos.
- Cambios en datos de producción e infraestructura.
- Requisitos ambiguos (primero aclara con una spec).

**El humano siempre es responsable** de: los requisitos, la revisión del diff, la decisión de *merge* y la seguridad.

---

## 6. El cambio de rol del desarrollador

| Antes | Ahora (agéntico) |
|---|---|
| Escribir cada línea | Definir objetivos, restricciones y criterios de aceptación |
| Buscar en docs/StackOverflow | Dar al agente acceso a docs (MCP, skills) |
| Depurar manualmente | Diseñar loops de verificación (tests, linters, type-check) que el agente use |
| Revisar PRs de humanos | Revisar PRs de agentes (y de humanos) con más rigor |
| Conocimiento en tu cabeza | Conocimiento **escrito** en instrucciones, skills y specs |

> 🔑 **Idea central:** la calidad del resultado depende de (1) el **contexto** que das, (2) la **capacidad de verificar** que tiene el agente y (3) tu **revisión**.

---

## Errores comunes

- Pedir "hazme la app" sin contexto ni criterios de aceptación.
- No darle al agente forma de comprobar su trabajo (sin tests ni comandos de build).
- Aceptar diffs enormes sin leerlos.
- Dar permisos totales en la máquina principal con credenciales reales.
- Conversaciones eternas que llenan el contexto (ver 01.2).

---

## Ejercicios

1. **Observa el loop.** Abre Claude Code u OpenCode en un repo tuyo y pide: *"Explica la arquitectura de este proyecto y lista los 5 archivos más importantes."* Anota qué herramientas usó y en qué orden.
   - ✅ Éxito: puedes enumerar al menos 3 tool calls (p. ej. Glob → Read → Grep).
2. **Clasifica tareas.** Escribe 10 tareas de tu backlog y clasifícalas en "delegar", "delegar con supervisión" y "no delegar", justificando cada una.
3. **Pseudocódigo.** Modifica el pseudocódigo de la sección 2 para añadir un límite máximo de iteraciones y una herramienta `preguntar_al_usuario`.

## Checklist

- [ ] Puedo explicar el loop agéntico en 1 minuto.
- [ ] Conozco las piezas: modelo, harness, tools, instrucciones, skills, subagentes, hooks, permisos.
- [ ] Sé elegir el nivel de autonomía según el riesgo.

---

⬅️ [Ruta](../00-ruta-de-aprendizaje.md) · ➡️ [01.2 · LLMs, contexto y tokens](02-llms-contexto-y-tokens.md)
