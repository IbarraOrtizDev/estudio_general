# 09.2 · Evaluación y observabilidad de agentes

## Objetivos

- Medir si tus **prompts, instrucciones, skills, subagentes y tools MCP** funcionan, con evaluaciones (*evals*) repetibles.
- Diseñar datasets, *graders* (por código, LLM-as-judge y humanos) y métricas.
- Automatizar evals en CI para detectar **regresiones**.
- Observar a los agentes en ejecución: **OpenTelemetry** en Claude Code, trazas de tu propio agente, costes y uso.

---

## 1. Por qué evaluar

Cambias una línea de `AGENTS.md`, la descripción de una skill o de una tool MCP… ¿mejoró o empeoró? Sin evals, solo tienes impresiones. Los LLM son **no deterministas**: un ejemplo que funciona una vez no prueba nada.

```
      ┌──────────── bucle de mejora ────────────┐
      ▼                                          │
 Cambio (prompt, skill, tool) → Evals (offline) → ¿Mejor? → Despliegue → Observabilidad (online)
                                     ▲                                        │
                                     └──── nuevos casos desde fallos reales ◄─┘
```

| Tipo | Qué es | Cuándo |
|---|---|---|
| **Offline (evals)** | Dataset fijo de casos + graders, se ejecuta bajo demanda o en CI | Antes de cambiar algo |
| **Online (observabilidad)** | Trazas, métricas y feedback del uso real | Durante el uso |

---

## 2. ¿Qué se evalúa en desarrollo agéntico?

| Objeto | Pregunta | Ejemplo de métrica |
|---|---|---|
| **Instrucciones** (`AGENTS.md`) | ¿El agente sigue las reglas? | % de sesiones que ejecutan tests antes de terminar |
| **Skills** | ¿Se activan cuando deben y solo entonces? ¿El resultado es correcto? | Precisión/recall de activación; % de salidas válidas |
| **Subagentes** | ¿El revisor detecta los bugs sembrados? | % de bugs detectados, falsos positivos |
| **Tools MCP** | ¿El modelo elige la tool correcta con argumentos correctos? | Exactitud de selección de tool y de argumentos |
| **Agente completo** | ¿Resuelve la tarea de punta a punta? | % de tareas con tests en verde (pass@k), coste y tiempo por tarea |
| **RAG** (09.3) | ¿Recupera los documentos correctos? ¿Responde con fundamento? | Recall@k, fidelidad (*faithfulness*) |

---

## 3. Anatomía de una eval

1. **Dataset**: casos con entrada y expectativa. Empieza con 20–50 casos reales (incluye casos borde y fallos pasados).
2. **Tarea**: lo que se ejecuta (un prompt, una llamada con tools, una sesión de agente headless).
3. **Graders** (calificadores):

| Grader | Cómo | Pros / contras |
|---|---|---|
| **Por código** | `assert`, regex, JSON válido, ¿pasan los tests?, ¿se llamó a la tool X? | Rápido, barato, determinista. Solo para lo verificable |
| **LLM-as-judge** | Otro modelo puntúa según una rúbrica | Evalúa calidad abierta. Calíbralo con revisión humana |
| **Humano** | Revisión manual de una muestra | Lo más fiable; lento y caro |

4. **Métricas**: tasa de aprobados, **pass@k** (al menos 1 éxito en k intentos) y **pass^k** (éxito en los k intentos, mide consistencia), coste, latencia.
5. **Repetición**: ejecuta cada caso varias veces (3–5) por el no determinismo.

> 💡 Prioriza graders **por código**: en agentes de software el mejor juez casi siempre es "¿compila y pasan los tests?".

---

## 4. Eval de selección de tools MCP (Python)

Comprueba que, con las descripciones actuales, el modelo elige la tool correcta. Reutiliza el servidor de [05.2](../05-mcp/02-mcp-servidor-python.md).

`evals/casos_tools.jsonl`
```json
{"entrada": "Apunta que mañana tengo que llamar al banco, es urgente", "tool": "agregar_tarea", "args": {"prioridad": "alta"}}
{"entrada": "¿Qué me queda pendiente?", "tool": "listar_tareas", "args": {}}
{"entrada": "Ya terminé la tarea 3", "tool": "completar_tarea", "args": {"tarea_id": 3}}
{"entrada": "¿Cuál es la capital de Francia?", "tool": null, "args": {}}
```

`evals/eval_tools.py`
```python
"""Eval: ¿el modelo elige la tool MCP correcta? Ejecuta cada caso N veces."""
import json
import anyio
import anthropic
from mcp import Client, StdioServerParameters

MODELO = "claude-haiku-5-5"   # evalúa con el modelo que usarás en producción
REPETICIONES = 3


async def main() -> None:
    llm = anthropic.Anthropic()
    casos = [json.loads(l) for l in open("evals/casos_tools.jsonl", encoding="utf-8")]

    async with Client(StdioServerParameters(command="uv", args=["run", "server.py"])) as mcp:
        tools = [{"name": t.name, "description": t.description or "", "input_schema": t.input_schema}
                 for t in (await mcp.list_tools()).tools]

        aciertos = total = 0
        for caso in casos:
            for _ in range(REPETICIONES):
                resp = llm.messages.create(model=MODELO, max_tokens=512, tools=tools,
                                           messages=[{"role": "user", "content": caso["entrada"]}])
                usadas = [b for b in resp.content if b.type == "tool_use"]
                elegida = usadas[0].name if usadas else None
                ok = elegida == caso["tool"]
                # comprobar argumentos esperados (si los hay)
                if ok and usadas:
                    ok = all(usadas[0].input.get(k) == v for k, v in caso["args"].items())
                aciertos += ok
                total += 1
                if not ok:
                    print(f"❌ '{caso['entrada']}' → {elegida} {usadas[0].input if usadas else ''}")

        print(f"\nExactitud: {aciertos}/{total} = {aciertos / total:.0%}")


if __name__ == "__main__":
    anyio.run(main)
```
Úsala así: cambia la descripción de una tool → vuelve a ejecutar → compara la exactitud.

---

## 5. Evals declarativas con promptfoo

**promptfoo** es una CLI open source (MIT) para evaluar prompts, agentes y hacer *red teaming* (prompt injection, fugas de datos…).

```bash
npx promptfoo@latest init
```

`promptfooconfig.yaml`
```yaml
description: "Revisor de código: ¿detecta bugs sembrados?"

prompts:
  - file://prompts/revisor.txt        # usa el cuerpo de tu subagente code-reviewer

providers:
  - id: anthropic:messages:claude-sonnet-5-5
  - id: anthropic:messages:claude-haiku-5-5   # comparar modelos

tests:
  - vars:
      diff: file://casos/sql_concatenado.diff
    assert:
      - type: icontains
        value: "inyección"
      - type: llm-rubric
        value: "Señala la inyección SQL como hallazgo crítico e indica la línea"

  - vars:
      diff: file://casos/cambio_limpio.diff
    assert:
      - type: not-icontains
        value: "crítico"
      - type: llm-rubric
        value: "No inventa problemas graves en un cambio correcto"

  - vars:
      diff: file://casos/test_debilitado.diff
    assert:
      - type: llm-rubric
        value: "Detecta que se relajó o eliminó una aserción de un test"
```
`prompts/revisor.txt`
```text
Eres un revisor de código senior. Revisa este diff y lista hallazgos por severidad
(Crítico, Importante, Sugerencia) con archivo:línea.

{{diff}}
```
```bash
npx promptfoo@latest eval
npx promptfoo@latest view      # comparativa en el navegador
```

---

## 6. Evaluar skills

1. **Activación**: escribe ~10 peticiones que *deberían* activar la skill y ~10 que *no*. Ejecútalas en modo headless y comprueba si se cargó:
   ```bash
   claude -p "añade un endpoint para archivar tareas" --output-format stream-json > salida.jsonl
   # busca en salida.jsonl el uso de la skill "crear-endpoint"
   ```
2. **Resultado**: para cada petición, graders por código (¿se crearon los archivos esperados?, ¿pasan los tests?).
3. Itera la `description` hasta tener alta precisión y recall.

> La skill integrada `skill-creator` de Claude incluye un flujo para crear evals de skills, medir rendimiento y optimizar la descripción.

---

## 7. Evaluar al agente completo (benchmark propio)

Inspirado en benchmarks tipo *SWE-bench*: un conjunto de **tareas reales de tu repo** con tests de aceptación.

```
evals/tareas/
├── 001-paginacion/
│   ├── prompt.md          ← la petición
│   ├── base_commit.txt    ← commit desde el que se parte
│   └── verificar.sh       ← tests que deben pasar (grader por código)
└── 002-export-csv/ ...
```
Script de ejecución (esquema):
```bash
for t in evals/tareas/*/; do
  git worktree add /tmp/eval-$(basename $t) $(cat $t/base_commit.txt)
  (cd /tmp/eval-$(basename $t) && \
     claude -p "$(cat $t/prompt.md)" --permission-mode acceptEdits --max-turns 40 \
       --output-format json > resultado.json; \
     bash "$OLDPWD/$t/verificar.sh" && echo "PASS $t" || echo "FAIL $t")
  git worktree remove --force /tmp/eval-$(basename $t)
done
```
Ejecútalo **dentro de un entorno aislado** (09.1). Úsalo para comparar: modelo A vs B, `AGENTS.md` antes/después, Claude Code vs OpenCode (`opencode run`).

---

## 8. Evals en CI

```yaml
# .github/workflows/evals.yml
name: Evals
on:
  pull_request:
    paths: ["AGENTS.md", ".claude/**", "mcp/**", "prompts/**"]
jobs:
  evals:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv run --directory mcp python ../evals/eval_tools.py
        env: { ANTHROPIC_API_KEY: "${{ secrets.ANTHROPIC_API_KEY }}" }
      - run: npx promptfoo@latest eval --no-progress-bar
        env: { ANTHROPIC_API_KEY: "${{ secrets.ANTHROPIC_API_KEY }}" }
```
Define un **umbral** (p. ej. exactitud de tools ≥ 90%) y haz fallar el job si baja.

---

## 9. Observabilidad de Claude Code con OpenTelemetry

Claude Code exporta **métricas** y **eventos** (logs) por OpenTelemetry.

### 9.1 Activar
```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp          # otlp | prometheus | console | none
export OTEL_LOGS_EXPORTER=otlp             # otlp | console | none
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_METRIC_EXPORT_INTERVAL=10000   # para pruebas (por defecto 60000 ms)
claude
```
```powershell
# PowerShell
$env:CLAUDE_CODE_ENABLE_TELEMETRY="1"; $env:OTEL_METRICS_EXPORTER="otlp"; $env:OTEL_LOGS_EXPORTER="otlp"
$env:OTEL_EXPORTER_OTLP_PROTOCOL="grpc"; $env:OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
claude
```
- Para probar rápido sin backend: `OTEL_METRICS_EXPORTER=console`.
- El contenido de prompts y de herramientas **no** se registra por defecto (`OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_TOOL_DETAILS` lo activan; cuidado con la privacidad).
- Los `.claude/settings.json` del repositorio **no** pueden fijar los exportadores: usa el shell, `~/.claude/settings.json` o managed settings.

### 9.2 Qué obtienes
| Métrica | Significado |
|---|---|
| `claude_code.session.count` | Sesiones iniciadas |
| `claude_code.token.usage` | Tokens usados |
| `claude_code.cost.usage` | Coste (USD) |
| `claude_code.lines_of_code.count` | Líneas modificadas |
| `claude_code.commit.count`, `claude_code.pull_request.count` | Commits y PRs creados |
| `claude_code.code_edit_tool.decision` | Decisiones de permiso en ediciones |
| `claude_code.active_time.total` | Tiempo activo |

Eventos: `claude_code.user_prompt`, `claude_code.tool_result`, `claude_code.tool_decision`, `claude_code.api_request`, `claude_code.api_error`…

### 9.3 Stack local mínimo (Docker Compose)
`observabilidad/docker-compose.yml`
```yaml
services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otel/config.yaml"]
    volumes: ["./otel-config.yaml:/etc/otel/config.yaml"]
    ports: ["4317:4317", "8889:8889"]
  prometheus:
    image: prom/prometheus:latest
    volumes: ["./prometheus.yml:/etc/prometheus/prometheus.yml"]
    ports: ["9090:9090"]
  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]
```
`observabilidad/otel-config.yaml`
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
exporters:
  prometheus:
    endpoint: 0.0.0.0:8889
  debug:
    verbosity: basic
service:
  pipelines:
    metrics: { receivers: [otlp], exporters: [prometheus] }
    logs:    { receivers: [otlp], exporters: [debug] }
```
`observabilidad/prometheus.yml`
```yaml
scrape_configs:
  - job_name: otel
    static_configs:
      - targets: ["otel-collector:8889"]
```
```bash
docker compose -f observabilidad/docker-compose.yml up -d
# Grafana en http://localhost:3000 → añade Prometheus (http://prometheus:9090) como data source
```
Alternativas gestionadas/open source con soporte OTLP: **Langfuse** (incluye guías para trazar agentes de código), **Arize Phoenix**, Datadog, Honeycomb, Grafana Cloud.

### 9.4 Consumo sin infraestructura
- Claude Code: `/usage` (o `/cost`) y `/context` en la sesión.
- OpenCode: consulta su documentación de la versión 2 sobre estadísticas y uso; además, la mayoría de proveedores ofrece paneles de consumo.

---

## 10. Trazas de tu propio agente

Para el agente de [05.5](../05-mcp/05-mcp-clientes-python-node-csharp.md), instrumenta con OpenTelemetry: un *span* por iteración del loop y por cada tool call.

```bash
uv add opentelemetry-sdk opentelemetry-exporter-otlp
```
```python
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

proveedor = TracerProvider(resource=Resource.create({"service.name": "agente-tareas"}))
proveedor.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)))
trace.set_tracer_provider(proveedor)
tracer = trace.get_tracer("agente")

# Dentro del loop del agente:
with tracer.start_as_current_span("llm.call") as span:
    resp = llm.messages.create(...)
    span.set_attribute("gen_ai.request.model", MODELO)
    span.set_attribute("gen_ai.usage.input_tokens", resp.usage.input_tokens)
    span.set_attribute("gen_ai.usage.output_tokens", resp.usage.output_tokens)

with tracer.start_as_current_span("tool.call") as span:
    span.set_attribute("tool.name", bloque.name)
    r = await mcp.call_tool(bloque.name, bloque.input)
    span.set_attribute("tool.is_error", bool(r.is_error))
```
> Usa las convenciones semánticas de OpenTelemetry para IA generativa (atributos `gen_ai.*`) para que las herramientas de observabilidad entiendan tus trazas. Añade el collector una ruta `traces` hacia Jaeger, Langfuse o Phoenix.

---

## 11. Qué vigilar (KPIs de un equipo agéntico)

| KPI | Por qué |
|---|---|
| Coste por tarea / por desarrollador | Presupuesto y elección de modelo |
| % de PRs de agente aceptados sin cambios grandes | Calidad real |
| Tasa de retrabajo (reverts, bugs posteriores) | Calidad a largo plazo |
| Tiempo hasta PR | Productividad |
| Denegaciones de permisos / bloqueos de hooks | Riesgo y fricción |
| Exactitud de evals de tools/skills | Salud de tu configuración |

---

## Errores comunes

- Evaluar con 3 ejemplos "a ojo".
- Un solo intento por caso (el no determinismo engaña).
- LLM-as-judge sin calibrar con revisiones humanas.
- Registrar prompts completos con datos sensibles en la telemetría.
- Medir solo velocidad y no retrabajo.

## Ejercicios

1. Crea la eval de selección de tools (sección 4) con 15 casos. Empeora a propósito una descripción y observa la caída; luego mejórala.
   - ✅ Éxito: puedes demostrar con números qué descripción es mejor.
2. Evalúa tu subagente `code-reviewer` con promptfoo usando 5 diffs con bugs sembrados y 2 limpios. Compara dos modelos.
3. Levanta el stack de observabilidad y visualiza `claude_code.token.usage` y `claude_code.cost.usage` de una sesión.
4. Instrumenta tu agente propio con spans y visualiza una traza completa.
5. Añade un workflow de evals que falle si la exactitud baja del 90%.

## Checklist

- [ ] Diferencio evals offline y observabilidad online.
- [ ] Tengo un dataset y graders para al menos una tool, skill o subagente.
- [ ] Ejecuto evals en CI con umbral.
- [ ] Exporto métricas de Claude Code con OpenTelemetry.
- [ ] Trazo mi propio agente.

---

⬅️ [09.1](01-aislamiento-sandbox-devcontainers-docker.md) · ➡️ [09.3 · RAG y memoria persistente](03-rag-y-memoria-persistente.md)
