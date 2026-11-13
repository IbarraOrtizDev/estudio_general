# 09.3 · Patrones RAG y memoria persistente

## Objetivos

- Entender **RAG** (*Retrieval-Augmented Generation*) y cuándo conviene frente a la **búsqueda agéntica**.
- Construir un pipeline RAG: *chunking*, *embeddings*, base vectorial, búsqueda híbrida, *reranking*.
- Exponer RAG a tus agentes como **servidor MCP**.
- Diseñar **memoria persistente**: en Claude Code (CLAUDE.md, rules, auto memory), en OpenCode, con servidores MCP de memoria y con la **memory tool** de la API de Claude.
- Evaluar la calidad de la recuperación.

---

## 1. El problema

Un LLM solo "sabe" lo que trae de su entrenamiento y lo que hay en su **ventana de contexto**. Dos necesidades distintas:

| Necesidad | Solución |
|---|---|
| Consultar **mucho conocimiento** que no cabe en el contexto (docs internas, wikis, tickets, normativas) | **RAG**: recuperar solo los fragmentos relevantes en cada pregunta |
| **Recordar** entre sesiones (decisiones, preferencias, lo aprendido) | **Memoria persistente**: el agente escribe y relee notas |

---

## 2. RAG vs búsqueda agéntica (para código)

Los agentes de código como Claude Code y OpenCode **no indexan tu repo con embeddings por defecto**: exploran con herramientas (`Glob`, `Grep`, `Read`) como haría un desarrollador. Esto se llama **búsqueda agéntica** (*agentic search*).

| Enfoque | Ventajas | Desventajas | Úsalo para |
|---|---|---|---|
| **Búsqueda agéntica** (grep/glob/read) | Siempre actualizada, exacta, sin infraestructura | Más iteraciones; peor con lenguaje vago | **Código** del repo actual |
| **RAG semántico** | Encuentra por significado, escala a millones de documentos | Índice que mantener; puede recuperar texto desactualizado o irrelevante | **Documentación** extensa, tickets, conocimiento no presente en el repo |
| **Híbrido** | Lo mejor de ambos | Más complejidad | Monorepos enormes + docs |

> **Regla práctica:** para el código de tu repo, confía en la búsqueda agéntica + buenas instrucciones. Usa RAG para conocimiento **externo al repo** y expónlo vía MCP.

Alternativas antes de construir RAG:
- **MCP de documentación** ya existentes (p. ej. Context7 para librerías).
- **Skills** con archivos de referencia (si el conocimiento es pequeño y estable).
- Poner los documentos en el repo (`docs/`) y dejar que el agente los busque con grep.

---

## 3. Pipeline RAG

```
INDEXACIÓN (offline)
 Documentos ─► Limpieza ─► Chunking ─► Embeddings ─► Base vectorial (+ índice BM25)
                                         (+ metadatos: fuente, fecha, sección)

CONSULTA (online)
 Pregunta ─► (reescritura) ─► Búsqueda híbrida (vectorial + palabras clave)
          ─► Reranking ─► Top-k fragmentos ─► LLM responde CITANDO fuentes
```

| Etapa | Decisiones clave |
|---|---|
| **Chunking** | Tamaño (≈ 300–800 tokens), solapamiento (10–20%), cortar por estructura (títulos, funciones) mejor que por caracteres |
| **Embeddings** | Modelo (local como `all-MiniLM`/`bge`, o API como Voyage AI u OpenAI); **misma** función para indexar y consultar |
| **Base vectorial** | Chroma, Qdrant, **pgvector** (Postgres), SQLite-vec, Azure AI Search, etc. |
| **Búsqueda híbrida** | Combinar similitud vectorial con BM25 (palabras exactas, códigos, nombres propios) |
| **Reranking** | Un modelo reordena los candidatos; mejora mucho la precisión |
| **Contextual retrieval** | Antes de indexar, añadir a cada chunk un breve resumen de su contexto en el documento; reduce fallos de recuperación |
| **Generación** | Instruir al modelo: "responde solo con los fragmentos; si no está, dilo; cita la fuente" |

---

## 4. Práctica: RAG local expuesto como servidor MCP (Python)

Construiremos un servidor MCP `docs` que indexa la carpeta `docs/` (Markdown) con **Chroma** (embeddings locales, sin API key) y expone la tool `buscar_docs`.

```bash
uv init mcp-docs && cd mcp-docs
uv add "mcp[cli]" chromadb
mkdir docs   # pon aquí tus .md (puedes copiar esta misma guía para probar)
```

### 4.1 Indexador
`indexar.py`
```python
"""Indexa docs/*.md en Chroma, cortando por títulos Markdown."""
import re
from pathlib import Path

import chromadb

CARPETA = Path("docs")
cliente = chromadb.PersistentClient(path=".chroma")
coleccion = cliente.get_or_create_collection("docs")   # usa la función de embeddings por defecto (local)


def trocear(texto: str, max_chars: int = 2000) -> list[tuple[str, str]]:
    """Devuelve (titulo_seccion, contenido) cortando por encabezados ## y ###."""
    partes = re.split(r"(?m)^(#{2,3} .+)$", texto)
    trozos, titulo = [], "Introducción"
    for parte in partes:
        if re.match(r"^#{2,3} ", parte):
            titulo = parte.lstrip("# ").strip()
        elif parte.strip():
            for i in range(0, len(parte), max_chars):  # secciones muy largas → sub-trozos
                trozos.append((titulo, parte[i : i + max_chars].strip()))
    return trozos


ids, documentos, metadatos = [], [], []
for archivo in CARPETA.rglob("*.md"):
    for n, (titulo, contenido) in enumerate(trocear(archivo.read_text(encoding="utf-8"))):
        ids.append(f"{archivo.as_posix()}#{n}")
        # "contextual retrieval" simple: anteponer archivo y sección al texto indexado
        documentos.append(f"Archivo: {archivo.name} · Sección: {titulo}\n\n{contenido}")
        metadatos.append({"fuente": archivo.as_posix(), "seccion": titulo})

coleccion.upsert(ids=ids, documents=documentos, metadatas=metadatos)
print(f"Indexados {len(ids)} fragmentos de {CARPETA}/")
```
```bash
uv run indexar.py
```

### 4.2 Servidor MCP
`server.py`
```python
"""Servidor MCP 'docs': búsqueda semántica sobre la documentación indexada."""
import logging

import chromadb
from pydantic import BaseModel
from mcp.server import MCPServer

logging.basicConfig(level=logging.INFO)   # stderr
coleccion = chromadb.PersistentClient(path=".chroma").get_or_create_collection("docs")
mcp = MCPServer("docs")


class Fragmento(BaseModel):
    fuente: str
    seccion: str
    texto: str
    distancia: float


class Resultados(BaseModel):
    consulta: str
    fragmentos: list[Fragmento]


@mcp.tool()
def buscar_docs(consulta: str, k: int = 5) -> Resultados:
    """Busca en la documentación interna del equipo por significado.

    Úsala para preguntas sobre procesos, arquitectura, convenciones o decisiones
    documentadas que NO estén en el código. Cita siempre la `fuente` en tu respuesta.
    Si los fragmentos no responden la pregunta, dilo en lugar de inventar.

    Args:
        consulta: Pregunta o tema en lenguaje natural.
        k: Número de fragmentos (1-10).
    """
    k = max(1, min(k, 10))
    r = coleccion.query(query_texts=[consulta], n_results=k)
    fragmentos = [
        Fragmento(fuente=m["fuente"], seccion=m["seccion"], texto=d[:1500], distancia=round(dist, 4))
        for d, m, dist in zip(r["documents"][0], r["metadatas"][0], r["distances"][0])
    ]
    return Resultados(consulta=consulta, fragmentos=fragmentos)


@mcp.resource("docs://fuentes")
def fuentes() -> str:
    """Lista de archivos indexados."""
    metas = coleccion.get(include=["metadatas"])["metadatas"]
    return "\n".join(sorted({m["fuente"] for m in metas}))


if __name__ == "__main__":
    mcp.run()
```

### 4.3 Conectarlo
```bash
claude mcp add docs -- uv run --directory /ruta/absoluta/mcp-docs server.py
```
```jsonc
// OpenCode
{ "mcp": { "servers": { "docs": { "type": "local", "command": ["uv", "run", "--directory", "/ruta/absoluta/mcp-docs", "server.py"] } } } }
```
Prueba: *"Según la documentación del equipo, ¿cómo se escriben los requisitos en OpenSpec? Cita la fuente."*

### 4.4 Mejoras para producción
- **Reindexado incremental** (por hash o fecha de modificación) y un job programado/CI.
- **Búsqueda híbrida** (BM25 + vectores) y **reranking**.
- **Filtros por metadatos** (proyecto, fecha, equipo) → parámetros de la tool.
- **Control de acceso**: no devuelvas documentos que el usuario no puede ver.
- **Base vectorial gestionada** (pgvector en tu Postgres, Qdrant, Azure AI Search).
- Variantes en **Node** (`registerTool` + cliente de tu base vectorial) o **C#** (`Microsoft.Extensions.VectorData` + `[McpServerTool]`) siguiendo los módulos 05.3 y 05.4.

---

## 5. Evaluar RAG

| Métrica | Pregunta | Cómo |
|---|---|---|
| **Recall@k** | ¿Está el fragmento correcto entre los k recuperados? | Dataset pregunta → fuente esperada; grader por código |
| **Precisión / MRR** | ¿Aparece arriba? | Posición del primer acierto |
| **Fidelidad** (*faithfulness*) | ¿La respuesta se apoya solo en los fragmentos? | LLM-as-judge con rúbrica |
| **Relevancia de respuesta** | ¿Responde lo preguntado? | LLM-as-judge / humano |

Eval mínima de recall:
```python
import json
from server import buscar_docs

casos = [json.loads(l) for l in open("evals/rag.jsonl", encoding="utf-8")]
# {"pregunta": "¿Qué es un delta spec?", "fuente": "docs/06-spec-driven/01-openspec.md"}
aciertos = sum(any(f.fuente == c["fuente"] for f in buscar_docs(c["pregunta"], k=5).fragmentos) for c in casos)
print(f"Recall@5: {aciertos}/{len(casos)}")
```
Herramientas especializadas: **Ragas**, DeepEval, promptfoo, Langfuse (ver [09.2](02-evaluacion-y-observabilidad.md)).

---

## 6. Memoria persistente: conceptos

| Tipo de memoria | Contenido | Ejemplo |
|---|---|---|
| **Procedimental** | Cómo hacer las cosas | `AGENTS.md`, skills, rules |
| **Semántica** | Hechos del proyecto/dominio | "La API usa cursor, no offset" |
| **Episódica** | Qué pasó en sesiones previas | "El 10/11 migramos a SDK v2; falló X por Y" |
| **Preferencias** | Gustos del usuario | "Respuestas en español; commits convencionales" |

Principios:
1. **Memoria = archivos legibles y versionables** siempre que se pueda (auditar, editar, borrar).
2. **Índice corto + detalle bajo demanda** (como las skills): no cargar todo en cada sesión.
3. **Curar**: la memoria se degrada; revisa y poda periódicamente.
4. **Seguridad**: nunca guardar secretos; cuidado con *memory poisoning* (contenido malicioso que se "recuerda" y se reutiliza).

---

## 7. Memoria en Claude Code

Claude Code tiene **dos sistemas**, ambos cargados al inicio de la sesión como contexto (no como reglas impuestas; para eso usa hooks o permisos):

### 7.1 Archivos que escribes tú (CLAUDE.md y rules)
| Ámbito | Ubicación |
|---|---|
| Organización | `/etc/claude-code/CLAUDE.md` (Linux/WSL), `C:\Program Files\ClaudeCode\CLAUDE.md` (Windows) |
| Usuario | `~/.claude/CLAUDE.md` |
| Proyecto | `./CLAUDE.md` o `./.claude/CLAUDE.md` |
| Local | `./CLAUDE.local.md` (en `.gitignore`) |

- Mantén cada archivo por debajo de ~200 líneas.
- Importa otros archivos con `@ruta` (hasta 4 niveles).
- **Rules por rutas**: `.claude/rules/*.md` con `paths` se cargan solo al trabajar con archivos que coinciden:
```markdown
---
paths:
  - "src/api/**/*.ts"
---
# Reglas de la API
- Todo endpoint valida la entrada
- Formato de error estándar
```

### 7.2 Auto memory (notas que escribe Claude)
- Se guarda en `~/.claude/projects/<proyecto>/memory/` (local a la máquina; compartida entre worktrees del mismo repo).
- `MEMORY.md` es un índice conciso: se cargan sus primeras ~200 líneas al iniciar; los archivos temáticos se leen cuando hacen falta.
```
~/.claude/projects/<proyecto>/memory/
├── MEMORY.md
├── debugging.md
└── api-conventions.md
```
- Gestionar: `/memory` (ver archivos cargados, activar/desactivar auto memory, abrir la carpeta).
- Desactivar: `"autoMemoryEnabled": false` en settings o `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.
- Subagentes con memoria propia: campo `memory: user | project | local` en su frontmatter (04.2).

**Flujo recomendado:** cuando Claude aprende algo útil para el equipo, pídele *"añade esto a CLAUDE.md"* (o a una rule/skill) y revísalo en el PR; deja en auto memory lo personal o efímero.

---

## 8. Memoria en OpenCode

- **`AGENTS.md`** (proyecto y global `~/.config/opencode/AGENTS.md`) e `instructions` en `opencode.json` cumplen el papel de memoria procedimental/semántica.
- **Skills** para conocimiento bajo demanda.
- Las **sesiones** se guardan y pueden retomarse.
- Para memoria entre sesiones gestionada por el agente, usa un **servidor MCP de memoria** (sección 9) o un archivo de notas del proyecto con una instrucción en `AGENTS.md`:

```markdown
## Memoria del proyecto
- Al terminar una tarea, añade en `docs/memoria/decisiones.md` (máx. 3 líneas)
  cualquier decisión técnica o aprendizaje no obvio, con fecha.
- Antes de empezar una tarea, lee `docs/memoria/decisiones.md`.
```
Este patrón funciona igual en Claude Code, OpenCode y cualquier agente: memoria **versionada y compartida por el equipo**.

---

## 9. Servidores MCP de memoria

Existen servidores MCP que dan memoria a cualquier cliente. El servidor de referencia `@modelcontextprotocol/server-memory` guarda un **grafo de conocimiento** (entidades, relaciones, observaciones) en un archivo local:

```bash
claude mcp add memoria -- npx -y @modelcontextprotocol/server-memory
```
```jsonc
{ "mcp": { "servers": { "memoria": { "type": "local", "command": ["npx", "-y", "@modelcontextprotocol/server-memory"],
  "environment": { "MEMORY_FILE_PATH": "/ruta/proyecto/.memoria/grafo.json" } } } } }
```
Añade en `AGENTS.md`: *"Usa las tools del servidor `memoria` para guardar decisiones y preferencias relevantes y consúltalas al inicio de cada tarea."*

También hay servicios de memoria más avanzados (con búsqueda semántica, multiusuario). Evalúalos con la checklist de seguridad de 02.2.

---

## 10. Memoria en tus propios agentes: memory tool de la API de Claude

La API de Claude ofrece una **memory tool** (`memory_20250818`) que permite a Claude crear, leer, actualizar y borrar archivos en un directorio `/memories` que **persiste entre conversaciones**. Funciona en el **lado cliente**: Claude pide operaciones y **tu aplicación** las ejecuta sobre el almacenamiento que tú controlas (disco, base de datos, por usuario…).

```python
import anthropic

client = anthropic.Anthropic()
resp = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=2048,
    messages=[{"role": "user", "content": "Ayúdame a responder este ticket de soporte."}],
    tools=[{"type": "memory_20250818", "name": "memory"}],
)
# La respuesta incluirá tool_use como: {"command": "view", "path": "/memories"}
# Tu código ejecuta el comando (view, create, str_replace, insert, delete, rename)
# y devuelve un tool_result. Es el loop de tool use estándar (05.5).
```

Puntos clave:
- **Valida las rutas**: rechaza cualquier ruta fuera de `/memories` (protección contra *path traversal*).
- Mapea `/memories` a almacenamiento **por usuario/tenant**.
- Combínala con **context editing** (limpieza automática de resultados de tools antiguos) para sesiones largas.
- El SDK de Python incluye utilidades/clases base para implementar el manejador; consulta la documentación de la memory tool.

---

## 11. Arquitectura de referencia: agente con RAG + memoria

```
                 ┌──────────────────────────────── Agente (Claude Code / OpenCode / propio) ─┐
Usuario ───────► │ Instrucciones (AGENTS.md)   Skills   Búsqueda agéntica en el repo          │
                 │        │                                                                   │
                 │        ├── MCP "docs"    → RAG sobre documentación (Chroma/pgvector)        │
                 │        ├── MCP "memoria" → grafo/archivos de memoria del proyecto           │
                 │        └── MCP "tareas"  → API del negocio                                  │
                 └──────────────────────────────────────────────────────────────────────────┘
                          │ trazas y métricas (OTel) → observabilidad (09.2)
                          │ ejecución aislada (09.1)
```

---

## Errores comunes

- Montar RAG sobre el código del repo cuando grep bastaba.
- Chunks enormes o cortados a mitad de frase/función.
- Indexar una vez y no reindexar (respuestas desactualizadas).
- No citar fuentes → imposible verificar.
- Memorias que crecen sin control y llenan el contexto.
- Guardar secretos o datos personales en la memoria.
- Implementar la memory tool sin validar rutas.

## Ejercicios

1. Indexa esta guía con el servidor `docs` y conéctalo a Claude Code y OpenCode. Haz 5 preguntas y verifica que cite fuentes correctas.
2. Crea `evals/rag.jsonl` con 15 preguntas y mide **Recall@5**. Cambia el tamaño de chunk y compara.
   - ✅ Éxito: justificas con números la configuración elegida.
3. Crea dos `.claude/rules/` con `paths` (frontend y backend) y comprueba con `/memory` cuándo se cargan.
4. Implementa el patrón `docs/memoria/decisiones.md` en un repo y úsalo durante una semana; poda lo que no aporte.
5. (Avanzado) Implementa la memory tool en tu agente de 05.5 guardando en `./memorias/<usuario>/` con validación de rutas.

## Checklist

- [ ] Sé cuándo usar búsqueda agéntica, RAG o ambos.
- [ ] Construí un pipeline RAG y lo expuse por MCP.
- [ ] Evalúo la recuperación con Recall@k.
- [ ] Domino CLAUDE.md, rules por rutas y auto memory.
- [ ] Tengo un patrón de memoria compartida para el equipo.
- [ ] Sé implementar memoria en un agente propio de forma segura.

---

⬅️ [09.2](02-evaluacion-y-observabilidad.md) · 🏠 [Índice](../README.md)
