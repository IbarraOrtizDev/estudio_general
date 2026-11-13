# Cheatsheet · MCP (spec 2026-07-28, SDK v2)

## Conceptos
- **Host** (app con LLM) → **cliente** (1 por servidor) → **servidor**.
- Primitivas: **tools** (modelo), **resources** (app/usuario, URI), **prompts** (usuario).
- Transportes: **stdio** (local, subproceso) · **Streamable HTTP** (remoto). SSE = legado.
- 2026-07-28: sin `initialize`, sin sesiones, `server/discover`, MRTR; roots/sampling/logging deprecados.
- ⚠️ stdio: **nunca escribir en stdout**.

## Python (`mcp` 2.x)
```bash
uv add "mcp[cli]"
uv run mcp dev server.py                              # Inspector
uv run mcp run server.py --transport streamable-http
```
```python
from mcp.server import MCPServer
from mcp.server.mcpserver import Context
mcp = MCPServer("demo")

@mcp.tool()
def sumar(a: int, b: int) -> int:
    """Suma dos números."""
    return a + b

@mcp.resource("saludo://{nombre}")
def saludo(nombre: str) -> str: return f"Hola {nombre}"

@mcp.prompt()
def resumir(texto: str) -> str: return f"Resume: {texto}"

if __name__ == "__main__":
    mcp.run()   # o mcp.run(transport="streamable-http", port=8000)
```
Cliente: `async with Client(StdioServerParameters(...)) as c:` / `Client("http://localhost:8000/mcp")` → `list_tools()`, `call_tool()`, `read_resource()`.

## TypeScript (v2)
```bash
npm i @modelcontextprotocol/server zod     # servidor
npm i @modelcontextprotocol/client         # cliente
npx @modelcontextprotocol/inspector npx tsx src/index.ts
```
```ts
import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import * as z from 'zod/v4';

serveStdio(() => {
  const s = new McpServer({ name: 'demo', version: '1.0.0' });
  s.registerTool('sumar', { description: 'Suma', inputSchema: z.object({ a: z.number(), b: z.number() }) },
    async ({ a, b }) => ({ content: [{ type: 'text', text: String(a + b) }] }));
  return s;
});
```
HTTP: `createMcpHandler(() => server)` + `toNodeHandler` (`@modelcontextprotocol/node`) + validación Host/Origin.
Cliente: `new Client({...})`, `StdioClientTransport`, `connect`, `listTools`, `callTool`, `close`.

## C# (`ModelContextProtocol` 2.x)
```bash
dotnet add package ModelContextProtocol
dotnet add package Microsoft.Extensions.Hosting
# HTTP: ModelContextProtocol.AspNetCore
```
```csharp
var b = Host.CreateApplicationBuilder(args);
b.Logging.AddConsole(o => o.LogToStandardErrorThreshold = LogLevel.Trace);
b.Services.AddMcpServer().WithStdioServerTransport().WithToolsFromAssembly();
await b.Build().RunAsync();

[McpServerToolType]
public static class Herramientas
{
    [McpServerTool, Description("Suma dos números")]
    public static int Sumar(int a, int b) => a + b;
}
```
HTTP: `.WithHttpTransport()` + `app.MapMcp("/mcp")`. Cliente: `McpClient.CreateAsync(new StdioClientTransport(...))`, `ListToolsAsync`, `CallToolAsync`.

## Configuración en clientes
| Cliente | Archivo | Formato |
|---|---|---|
| Claude Code | `.mcp.json` | `{"mcpServers": {"n": {"command","args","env"} \| {"type":"http","url"}}}` |
| OpenCode | `opencode.json` | `{"mcp": {"servers": {"n": {"type":"local","command":[...]} \| {"type":"remote","url"}}}}` |
| VS Code | `.vscode/mcp.json` | `{"servers": {"n": {"type":"stdio"\|"http", ...}}}` |
| Claude Desktop | `claude_desktop_config.json` | `{"mcpServers": {...}}` |

## Diseño de tools
Verbo_sustantivo · descripción con "cuándo usarla" · schemas estrictos · pocas tools · respuestas compactas · `isError` con mensaje útil · anotaciones read-only/destructive · validar toda entrada.
