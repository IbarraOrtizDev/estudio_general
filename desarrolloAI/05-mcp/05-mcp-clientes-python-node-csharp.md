# 05.5 · Clientes MCP en Python, Node.js y C# (y tu propio agente)

## Objetivos

- Conectarte a cualquier servidor MCP desde código (stdio y HTTP) en los tres lenguajes.
- Listar y llamar tools, leer resources y obtener prompts.
- Construir un **agente mínimo**: LLM + herramientas MCP en un loop.

---

## 1. ¿Cuándo escribir un cliente MCP?

- Para **probar** tus servidores en tests de integración (ya lo hiciste en 05.2–05.4).
- Para **integrar** herramientas MCP en tu propia aplicación (backend, bot, pipeline).
- Para **construir tu propio agente** o host.
- Para automatizar tareas (scripts que usan servidores MCP existentes).

---

## 2. Cliente en Python (SDK `mcp` 2.x)

```bash
uv add "mcp[cli]"
```

### stdio
```python
import anyio
from mcp import Client, StdioServerParameters
from mcp.types import TextContent, TextResourceContents


async def main() -> None:
    params = StdioServerParameters(command="uv", args=["run", "server.py"])
    async with Client(params) as client:               # el bloque es todo el ciclo de vida
        tools = await client.list_tools()
        print("Tools:", [t.name for t in tools.tools])

        r = await client.call_tool("agregar_tarea", {"titulo": "Desde Python", "prioridad": "alta"})
        if r.is_error:
            print("Error:", r.content)
        else:
            for bloque in r.content:
                if isinstance(bloque, TextContent):
                    print(bloque.text)
            print("Estructurado:", r.structured_content)

        recurso = await client.read_resource("tareas://pendientes")
        for c in recurso.contents:
            if isinstance(c, TextResourceContents):
                print(c.text)


if __name__ == "__main__":
    anyio.run(main)
```

### Streamable HTTP
Solo cambia el argumento de `Client`:
```python
async with Client("http://localhost:8000/mcp") as client:
    ...
```

Notas:
- No hay `connect()`/`close()`: el `async with` gestiona todo, y un `Client` no se reutiliza después del bloque.
- Comprueba `r.is_error` antes de usar `structured_content`: una tool que lanza excepción devuelve un resultado con error, no una excepción.

---

## 3. Cliente en Node.js (SDK v2)

```bash
npm install @modelcontextprotocol/client
```

### stdio
```ts
import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const client = new Client({ name: 'mi-cliente', version: '1.0.0' });
const transport = new StdioClientTransport({ command: 'npx', args: ['tsx', 'src/stdio.ts'] });

try {
    await client.connect(transport);

    const { tools } = await client.listTools();
    for (const t of tools) console.log(t.name, '—', t.description);

    const r = await client.callTool({ name: 'agregar_tarea', arguments: { titulo: 'Desde Node' } });
    for (const b of r.content) if (b.type === 'text') console.log(b.text);

    const res = await client.readResource({ uri: 'tareas://pendientes' });
    console.log(res.contents);

    const prompt = await client.getPrompt({ name: 'planificar_dia', arguments: { horas: '6' } });
    console.log(prompt.messages);
} finally {
    await client.close();   // termina el proceso del servidor
}
```

### Streamable HTTP
```ts
import { Client } from '@modelcontextprotocol/client';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/client';

const client = new Client({ name: 'mi-cliente', version: '1.0.0' });
await client.connect(new StreamableHTTPClientTransport(new URL('http://127.0.0.1:3000/mcp')));
```
> Consulta la guía *Connect* de la doc v2 para la ruta de importación exacta del transporte HTTP en tu versión. El cliente v2 habla tanto la revisión 2026-07-28 como las anteriores.

---

## 4. Cliente en C# (`ModelContextProtocol` 2.x)

```bash
dotnet add package ModelContextProtocol
```

### stdio
```csharp
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol;

var transport = new StdioClientTransport(new StdioClientTransportOptions
{
    Name = "tareas",
    Command = "dotnet",
    Arguments = ["run", "--project", "../McpTareas"],
    StandardErrorLines = line => Console.Error.WriteLine($"[server] {line}") // ver logs del servidor
});

await using var client = await McpClient.CreateAsync(transport);

foreach (var tool in await client.ListToolsAsync())
    Console.WriteLine($"{tool.Name}: {tool.Description}");

var result = await client.CallToolAsync("agregar_tarea",
    new Dictionary<string, object?> { ["titulo"] = "Desde C#", ["prioridad"] = "Alta" });

foreach (var block in result.Content)
    if (block is TextContentBlock text) Console.WriteLine(text.Text);
```

### Streamable HTTP
```csharp
var transport = new HttpClientTransport(new HttpClientTransportOptions
{
    Endpoint = new Uri("http://localhost:5050/mcp"),
    AdditionalHeaders = new Dictionary<string, string> { ["X-Api-Key"] = "..." }
});
await using var client = await McpClient.CreateAsync(transport);
```

> En v2, `McpClient.CreateAsync` sondea primero con `server/discover` y negocia la versión de protocolo automáticamente.

---

## 5. Construye tu propio agente (LLM + MCP)

El patrón es el loop de [01.1](../01-fundamentos/01-que-es-el-desarrollo-agentico.md): convertir las tools MCP al formato del LLM, y ejecutar las *tool calls* contra el servidor MCP.

### 5.1 Python + API de Claude

```bash
uv add anthropic "mcp[cli]"
export ANTHROPIC_API_KEY=...   # PowerShell: $env:ANTHROPIC_API_KEY="..."
```

`agente.py`
```python
import anyio
import anthropic
from mcp import Client, StdioServerParameters
from mcp.types import TextContent

MODELO = "claude-sonnet-5-5"


async def main(objetivo: str) -> None:
    llm = anthropic.Anthropic()
    params = StdioServerParameters(command="uv", args=["run", "server.py"])

    async with Client(params) as mcp:
        # 1) MCP tools → formato de tools de la API
        tools = [
            {"name": t.name, "description": t.description or "", "input_schema": t.input_schema}
            for t in (await mcp.list_tools()).tools
        ]

        mensajes = [{"role": "user", "content": objetivo}]

        for _ in range(10):  # límite de iteraciones
            resp = llm.messages.create(
                model=MODELO, max_tokens=2048,
                system="Eres un asistente que gestiona tareas. Responde en español.",
                tools=tools, messages=mensajes,
            )
            mensajes.append({"role": "assistant", "content": resp.content})

            if resp.stop_reason != "tool_use":
                print("".join(b.text for b in resp.content if b.type == "text"))
                return

            # 2) Ejecutar cada tool call contra el servidor MCP
            resultados = []
            for bloque in resp.content:
                if bloque.type == "tool_use":
                    print(f"→ {bloque.name}({bloque.input})")
                    r = await mcp.call_tool(bloque.name, bloque.input)
                    texto = "\n".join(c.text for c in r.content if isinstance(c, TextContent))
                    resultados.append({
                        "type": "tool_result",
                        "tool_use_id": bloque.id,
                        "content": texto,
                        "is_error": bool(r.is_error),
                    })
            mensajes.append({"role": "user", "content": resultados})


if __name__ == "__main__":
    anyio.run(main, "Añade 'preparar demo' con prioridad alta y dime qué tengo pendiente.")
```

> En el atributo `input_schema` el SDK de Python expone el schema de la tool MCP (verifica el nombre del atributo en tu versión: `input_schema`/`inputSchema`). La API de Anthropic también ofrece un **conector MCP** que conecta directamente con servidores MCP remotos sin escribir el loop; y el **Claude Agent SDK** te da el motor completo de Claude Code.

### 5.2 Node.js + API de Claude (esqueleto)

```ts
import Anthropic from '@anthropic-ai/sdk';
import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const llm = new Anthropic();
const mcp = new Client({ name: 'agente', version: '1.0.0' });
await mcp.connect(new StdioClientTransport({ command: 'npx', args: ['tsx', 'src/stdio.ts'] }));

const tools = (await mcp.listTools()).tools.map(t => ({
    name: t.name, description: t.description ?? '', input_schema: t.inputSchema as Anthropic.Tool.InputSchema
}));

const mensajes: Anthropic.MessageParam[] = [{ role: 'user', content: '¿Qué tareas tengo pendientes?' }];

for (let i = 0; i < 10; i++) {
    const resp = await llm.messages.create({ model: 'claude-sonnet-5-5', max_tokens: 2048, tools, messages: mensajes });
    mensajes.push({ role: 'assistant', content: resp.content });
    if (resp.stop_reason !== 'tool_use') {
        console.log(resp.content.filter(b => b.type === 'text').map(b => b.text).join(''));
        break;
    }
    const resultados: Anthropic.ToolResultBlockParam[] = [];
    for (const b of resp.content) {
        if (b.type !== 'tool_use') continue;
        const r = await mcp.callTool({ name: b.name, arguments: b.input as Record<string, unknown> });
        const texto = r.content.filter(c => c.type === 'text').map(c => (c as { text: string }).text).join('\n');
        resultados.push({ type: 'tool_result', tool_use_id: b.id, content: texto, is_error: !!r.isError });
    }
    mensajes.push({ role: 'user', content: resultados });
}
await mcp.close();
```

### 5.3 C# + Microsoft.Extensions.AI

En C#, cada `McpClientTool` **es** un `AIFunction` de `Microsoft.Extensions.AI`, así que puedes pasarlas directamente a cualquier `IChatClient` (OpenAI, Azure OpenAI, Ollama, Anthropic u otro proveedor con integración M.E.AI) y dejar que `UseFunctionInvocation()` ejecute el loop:

```csharp
using Microsoft.Extensions.AI;
using ModelContextProtocol.Client;

await using var mcp = await McpClient.CreateAsync(new StdioClientTransport(new()
{
    Name = "tareas", Command = "dotnet", Arguments = ["run", "--project", "../McpTareas"]
}));

IList<McpClientTool> tools = await mcp.ListToolsAsync();

IChatClient chat = /* tu proveedor: p. ej. new OpenAIClient(...).GetChatClient("modelo").AsIChatClient() */
    throw new NotImplementedException("Configura tu IChatClient");

IChatClient agente = new ChatClientBuilder(chat)
    .UseFunctionInvocation()          // ejecuta automáticamente las tool calls
    .Build();

var respuesta = await agente.GetResponseAsync(
    "Añade 'revisar PR' con prioridad alta y lista mis pendientes",
    new ChatOptions { Tools = [.. tools] });

Console.WriteLine(respuesta.Text);
```

---

## Errores comunes

- No cerrar el cliente → procesos de servidor huérfanos.
- Bucles sin límite de iteraciones en tu agente.
- Pasar resultados enormes de tools al LLM sin recortar.
- Ignorar `is_error`/`isError`.
- Ejecutar tools destructivas sin confirmación humana en tu agente.

## Ejercicios

1. Escribe el cliente stdio en los **tres** lenguajes contra el **mismo** servidor (p. ej. el de Python).
   - ✅ Éxito: los tres listan las mismas tools y crean tareas en el mismo archivo.
2. Ejecuta el agente de la sección 5.1 y añade confirmación por consola antes de cualquier tool cuyo nombre empiece por `eliminar_` o `completar_`.
3. Conecta tu agente a **dos** servidores MCP (tareas + `@modelcontextprotocol/server-everything`) y fusiona sus tools (prefija nombres para evitar colisiones).

## Checklist

- [ ] Sé crear clientes stdio y HTTP en Python, Node y C#.
- [ ] Entiendo cómo convertir tools MCP al formato de un LLM.
- [ ] Construí un agente mínimo con límite de iteraciones y confirmaciones.

---

⬅️ [05.4](04-mcp-servidor-csharp.md) · ➡️ [05.6 · Configurar MCP en clientes](06-mcp-configuracion-en-clientes.md)
