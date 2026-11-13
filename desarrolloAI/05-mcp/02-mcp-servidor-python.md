# 05.2 · Servidor MCP en Python

## Objetivos

- Crear un servidor MCP completo con el **SDK oficial de Python v2** (`mcp` 2.x).
- Exponer tools (con salida estructurada), resources (estáticos y plantillas) y prompts.
- Usar `Context` (progreso, lectura de recursos) y logging seguro.
- Ejecutarlo por stdio y Streamable HTTP, probarlo con MCP Inspector y con pytest.

> **Proyecto común:** en Python, Node y C# construiremos el **mismo servidor "tareas"** para que compares los tres SDK.

---

## 1. Preparar el proyecto

Requisitos: Python 3.11+ y [`uv`](https://docs.astral.sh/uv/).

```bash
uv init mcp-tareas-py
cd mcp-tareas-py
uv add "mcp[cli]" pydantic
uv add --dev pytest anyio
```

> El extra `[cli]` instala el comando `mcp` (`mcp dev`, `mcp run`).
>
> **¿Vienes de v1?** En `mcp` 1.x la clase era `FastMCP` (`from mcp.server.fastmcp import FastMCP`). En v2 es `MCPServer` (`from mcp.server import MCPServer`). La API de decoradores es muy parecida. Revisa la *Migration Guide* oficial.

Estructura:
```
mcp-tareas-py/
├── pyproject.toml
├── server.py
├── almacen.py
└── tests/
    ├── test_almacen.py
    └── test_servidor.py
```

---

## 2. La lógica de negocio (independiente de MCP)

`almacen.py`
```python
"""Almacén de tareas en un archivo JSON. Sin dependencias de MCP: fácil de testear."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

Prioridad = Literal["alta", "media", "baja"]


class Tarea(BaseModel):
    id: int
    titulo: str = Field(min_length=1, max_length=200)
    prioridad: Prioridad = "media"
    completada: bool = False
    creada: str


class Almacen:
    def __init__(self, ruta: Path) -> None:
        self.ruta = ruta
        if not self.ruta.exists():
            self.ruta.write_text("[]", encoding="utf-8")

    def _leer(self) -> list[Tarea]:
        return [Tarea(**t) for t in json.loads(self.ruta.read_text(encoding="utf-8"))]

    def _guardar(self, tareas: list[Tarea]) -> None:
        self.ruta.write_text(
            json.dumps([t.model_dump() for t in tareas], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def agregar(self, titulo: str, prioridad: Prioridad = "media") -> Tarea:
        tareas = self._leer()
        nueva = Tarea(
            id=max((t.id for t in tareas), default=0) + 1,
            titulo=titulo.strip(),
            prioridad=prioridad,
            creada=datetime.now(timezone.utc).isoformat(),
        )
        tareas.append(nueva)
        self._guardar(tareas)
        return nueva

    def listar(self, solo_pendientes: bool = False) -> list[Tarea]:
        tareas = self._leer()
        return [t for t in tareas if not t.completada] if solo_pendientes else tareas

    def obtener(self, tarea_id: int) -> Tarea:
        for t in self._leer():
            if t.id == tarea_id:
                return t
        raise KeyError(f"No existe la tarea {tarea_id}")

    def completar(self, tarea_id: int) -> Tarea:
        tareas = self._leer()
        for t in tareas:
            if t.id == tarea_id:
                t.completada = True
                self._guardar(tareas)
                return t
        raise KeyError(f"No existe la tarea {tarea_id}")
```

---

## 3. El servidor MCP

`server.py`
```python
"""Servidor MCP 'tareas' con el SDK oficial de Python v2."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from pydantic import BaseModel

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from almacen import Almacen, Prioridad, Tarea

# Logging SIEMPRE a stderr (stdout es el canal del protocolo en stdio)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("mcp-tareas")

RUTA_DATOS = Path(os.environ.get("TAREAS_ARCHIVO", "tareas.json"))
almacen = Almacen(RUTA_DATOS)

mcp = MCPServer("tareas")


# ───────────────────────────── TOOLS ─────────────────────────────

@mcp.tool()
def agregar_tarea(titulo: str, prioridad: Prioridad = "media") -> Tarea:
    """Crea una tarea nueva.

    Úsala cuando el usuario quiera apuntar, añadir o crear una tarea/pendiente.

    Args:
        titulo: Texto corto de la tarea (máx. 200 caracteres).
        prioridad: 'alta', 'media' o 'baja'. Por defecto 'media'.
    """
    tarea = almacen.agregar(titulo, prioridad)
    logger.info("Tarea creada: %s", tarea.id)
    return tarea  # modelo Pydantic → salida estructurada + texto


class ListaTareas(BaseModel):
    total: int
    tareas: list[Tarea]


@mcp.tool()
def listar_tareas(solo_pendientes: bool = True) -> ListaTareas:
    """Lista las tareas. Por defecto solo las pendientes.

    Úsala para responder preguntas sobre qué hay pendiente o el estado de las tareas.
    """
    tareas = almacen.listar(solo_pendientes)
    return ListaTareas(total=len(tareas), tareas=tareas)


@mcp.tool()
def completar_tarea(tarea_id: int) -> Tarea:
    """Marca una tarea como completada a partir de su id numérico.

    Si no conoces el id, llama antes a `listar_tareas`.
    """
    try:
        return almacen.completar(tarea_id)
    except KeyError as e:
        # Una excepción se devuelve al cliente como resultado con is_error=True,
        # y el mensaje ayuda al modelo a corregirse.
        raise ValueError(f"{e}. Usa listar_tareas para ver los ids válidos.") from e


@mcp.tool()
async def resumen_con_progreso(ctx: Context) -> str:
    """Genera un resumen del estado de las tareas informando del progreso."""
    await ctx.report_progress(1, 3, "Leyendo tareas")
    tareas = almacen.listar()
    await ctx.report_progress(2, 3, "Calculando")
    pendientes = [t for t in tareas if not t.completada]
    altas = [t for t in pendientes if t.prioridad == "alta"]
    await ctx.report_progress(3, 3, "Listo")
    return (
        f"Total: {len(tareas)} · Pendientes: {len(pendientes)} · "
        f"Alta prioridad pendientes: {len(altas)}"
    )


# ─────────────────────────── RESOURCES ───────────────────────────

@mcp.resource("tareas://pendientes")
def recurso_pendientes() -> str:
    """Lista legible de tareas pendientes."""
    lineas = [f"- [{t.prioridad}] #{t.id} {t.titulo}" for t in almacen.listar(True)]
    return "\n".join(lineas) or "No hay tareas pendientes."


@mcp.resource("tareas://{tarea_id}")
def recurso_tarea(tarea_id: str) -> str:
    """Detalle de una tarea concreta en JSON."""
    return almacen.obtener(int(tarea_id)).model_dump_json(indent=2)


# ──────────────────────────── PROMPTS ────────────────────────────

@mcp.prompt()
def planificar_dia(horas_disponibles: str = "8") -> str:
    """Plantilla para planificar el día con las tareas pendientes."""
    return (
        f"Tengo {horas_disponibles} horas hoy. Usa la herramienta listar_tareas y "
        "propón un plan ordenado por prioridad, con estimación de tiempo por tarea "
        "y qué dejar para mañana si no da tiempo."
    )


if __name__ == "__main__":
    # stdio por defecto. Para HTTP: mcp.run(transport="streamable-http", port=8000)
    mcp.run()
```

**Puntos clave**
- Los **type hints** y el **docstring** generan el JSON Schema y la descripción: no escribes schemas a mano.
- `Literal["alta","media","baja"]` se convierte en un `enum` en el schema.
- Devolver un **modelo Pydantic** produce **salida estructurada** (`structured_content`) además del texto.
- `Context` se inyecta si declaras un parámetro `ctx: Context`; no aparece en el schema.
- No hay método de logging en `Context`: usa el módulo `logging` (a stderr).

---

## 4. Ejecutar y probar

### Con MCP Inspector (recomendado para desarrollar)
```bash
uv run mcp dev server.py
```
Abre el Inspector en el navegador (requiere `npx` en el PATH). Pestañas **Tools**, **Resources**, **Prompts**: prueba `agregar_tarea`, lee `tareas://pendientes`, etc.

### Por stdio (lo que hará Claude Code/OpenCode)
```bash
uv run server.py          # se queda esperando en stdin: es normal
```

### Por Streamable HTTP
```bash
uv run mcp run server.py --transport streamable-http
# o en el código: mcp.run(transport="streamable-http", port=8000)
```
Endpoint: `http://127.0.0.1:8000/mcp` (por defecto host `127.0.0.1`, puerto `8000`, ruta `/mcp`; se cambian con argumentos de `run()`, no del constructor).

---

## 5. Conectarlo a Claude Code y OpenCode

**Claude Code** (stdio):
```bash
claude mcp add tareas -- uv run --directory /ruta/absoluta/mcp-tareas-py server.py
# Windows: usa la ruta de Windows, p. ej. D:\\proyectos\\mcp-tareas-py
```
Comprueba con `/mcp` y pide: *"Añade una tarea de prioridad alta: preparar demo"*.

**OpenCode** (`opencode.json`):
```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "servers": {
      "tareas": {
        "type": "local",
        "command": ["uv", "run", "--directory", "/ruta/absoluta/mcp-tareas-py", "server.py"],
        "environment": { "TAREAS_ARCHIVO": "/ruta/absoluta/tareas.json" }
      }
    }
  }
}
```

Más opciones en [05.6](06-mcp-configuracion-en-clientes.md).

---

## 6. Tests

### Lógica pura
`tests/test_almacen.py`
```python
import pytest
from almacen import Almacen


@pytest.fixture
def almacen(tmp_path):
    return Almacen(tmp_path / "tareas.json")


def test_agregar_asigna_ids_incrementales(almacen):
    a = almacen.agregar("A")
    b = almacen.agregar("B", "alta")
    assert (a.id, b.id) == (1, 2)
    assert b.prioridad == "alta"


def test_listar_solo_pendientes(almacen):
    almacen.agregar("A")
    t = almacen.agregar("B")
    almacen.completar(t.id)
    assert [x.titulo for x in almacen.listar(solo_pendientes=True)] == ["A"]


def test_completar_inexistente_lanza_error(almacen):
    with pytest.raises(KeyError):
        almacen.completar(99)
```

### Integración vía protocolo (cliente MCP real por stdio)
`tests/test_servidor.py`
```python
import anyio
import pytest
from mcp import Client, StdioServerParameters


@pytest.mark.anyio
async def test_flujo_completo(tmp_path):
    params = StdioServerParameters(
        command="uv",
        args=["run", "server.py"],
        env={"TAREAS_ARCHIVO": str(tmp_path / "t.json")},
    )
    async with Client(params) as client:
        nombres = [t.name for t in (await client.list_tools()).tools]
        assert {"agregar_tarea", "listar_tareas", "completar_tarea"} <= set(nombres)

        r = await client.call_tool("agregar_tarea", {"titulo": "Probar MCP", "prioridad": "alta"})
        assert not r.is_error
        assert r.structured_content["titulo"] == "Probar MCP"

        r = await client.call_tool("completar_tarea", {"tarea_id": 999})
        assert r.is_error  # error devuelto como resultado, no como excepción
```
```bash
uv run pytest -q
```

> Si `env` reemplaza todo el entorno en tu plataforma, añade también `PATH` (`{**os.environ, "TAREAS_ARCHIVO": ...}`).

---

## 7. Más allá

- **Elicitation** (`ctx.elicit(...)`): pedir confirmación al usuario antes de acciones destructivas.
- **Autenticación OAuth** para servidores HTTP remotos (el SDK incluye soporte).
- **Montar en una app ASGI** existente (Starlette/FastAPI) para desplegar junto a tu API.
- **FastMCP (proyecto independiente, PrefectHQ)**: framework de alto nivel sobre el SDK con extras (proxies, composición, auth). Útil, pero aprende primero el SDK oficial.

---

## Errores comunes

- `print()` en el servidor → corrompe el protocolo stdio.
- Rutas relativas: el cliente lanza el proceso desde otro directorio. Usa `--directory` o rutas absolutas.
- Tutoriales v1 (`FastMCP`, `mcp.server.fastmcp`) mezclados con v2.
- Docstrings vacíos → el modelo no sabe cuándo usar la tool.

## Ejercicios

1. Implementa el servidor y pruébalo en el Inspector.
2. Añade la tool `eliminar_tarea(tarea_id)` que **pida confirmación** con elicitation (o, si tu cliente no la soporta, que exija un parámetro `confirmar: bool`).
3. Añade un filtro `prioridad` opcional a `listar_tareas` y su test.
4. Conéctalo a Claude Code y a OpenCode y planifica tu día con el prompt `planificar_dia`.
   - ✅ Éxito: el agente lista, crea y completa tareas solo con lenguaje natural.

## Checklist

- [ ] Sé crear tools, resources y prompts con `MCPServer`.
- [ ] Uso salida estructurada con Pydantic.
- [ ] Logging a stderr; nada en stdout.
- [ ] Pruebo con Inspector y con pytest.

---

⬅️ [05.1](01-mcp-conceptos.md) · ➡️ [05.3 · Servidor MCP en Node.js](03-mcp-servidor-nodejs.md)
