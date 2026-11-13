# 05.4 · Servidor MCP en C# (.NET)

## Objetivos

- Crear el servidor "tareas" con el **SDK oficial de C#** (`ModelContextProtocol` 2.x).
- Usar atributos (`[McpServerTool]`, `[McpServerResource]`, `[McpServerPrompt]`) e inyección de dependencias.
- Servir por stdio (consola) y por Streamable HTTP (ASP.NET Core).
- Probarlo con MCP Inspector y xUnit.

---

## 1. Paquetes del SDK

El SDK es mantenido por el proyecto MCP junto con Microsoft. Versión estable: **2.x** (alineada con la spec 2026-07-28; soporta `net8.0`, `net9.0`, `net10.0` y `netstandard2.0`).

| Paquete | Cuándo |
|---|---|
| `ModelContextProtocol` | **Empieza aquí.** Hosting, DI, descubrimiento por atributos, stdio |
| `ModelContextProtocol.AspNetCore` | Servidores remotos por HTTP (`WithHttpTransport()` + `MapMcp()`) |
| `ModelContextProtocol.Core` | Solo cliente o escenarios de bajo nivel sin `Microsoft.Extensions.*` |

Cambios clave de v2 respecto a 1.x:
- HTTP **stateless por defecto** (`HttpServerTransportOptions.Stateless = true`).
- Roots, Sampling y logging por MCP marcados `[Obsolete]` (aviso `MCP9005`).
- Elicitation mediante *Multi Round-Trip Requests*.

---

## 2. Opción rápida: plantilla oficial

```bash
dotnet new install Microsoft.McpServer.ProjectTemplates
dotnet new mcpserver -n McpTareas
```

Para aprender, haremos el proyecto a mano.

---

## 3. Proyecto paso a paso (stdio)

```bash
dotnet new console -n McpTareas
cd McpTareas
dotnet add package ModelContextProtocol
dotnet add package Microsoft.Extensions.Hosting
```

Estructura:
```
McpTareas/
├── McpTareas.csproj
├── Program.cs
├── Dominio/AlmacenTareas.cs
├── Herramientas/TareasTools.cs
├── Recursos/TareasResources.cs
└── Prompts/TareasPrompts.cs
```

### 3.1 Dominio

`Dominio/AlmacenTareas.cs`
```csharp
using System.Text.Json;
using System.Text.Json.Serialization;

namespace McpTareas.Dominio;

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum Prioridad { Alta, Media, Baja }

public sealed record Tarea(int Id, string Titulo, Prioridad Prioridad, bool Completada, DateTimeOffset Creada);

public sealed class AlmacenTareas
{
    private readonly string _ruta;
    private readonly Lock _lock = new();
    private static readonly JsonSerializerOptions Json = new(JsonSerializerDefaults.Web) { WriteIndented = true };

    public AlmacenTareas(string ruta)
    {
        _ruta = ruta;
        if (!File.Exists(_ruta)) File.WriteAllText(_ruta, "[]");
    }

    private List<Tarea> Leer() =>
        JsonSerializer.Deserialize<List<Tarea>>(File.ReadAllText(_ruta), Json) ?? [];

    private void Guardar(List<Tarea> tareas) =>
        File.WriteAllText(_ruta, JsonSerializer.Serialize(tareas, Json));

    public Tarea Agregar(string titulo, Prioridad prioridad)
    {
        lock (_lock)
        {
            var tareas = Leer();
            var nueva = new Tarea(tareas.Count == 0 ? 1 : tareas.Max(t => t.Id) + 1,
                                  titulo.Trim(), prioridad, false, DateTimeOffset.UtcNow);
            tareas.Add(nueva);
            Guardar(tareas);
            return nueva;
        }
    }

    public IReadOnlyList<Tarea> Listar(bool soloPendientes) =>
        Leer().Where(t => !soloPendientes || !t.Completada).ToList();

    public Tarea? Obtener(int id) => Leer().FirstOrDefault(t => t.Id == id);

    public Tarea? Completar(int id)
    {
        lock (_lock)
        {
            var tareas = Leer();
            var idx = tareas.FindIndex(t => t.Id == id);
            if (idx < 0) return null;
            tareas[idx] = tareas[idx] with { Completada = true };
            Guardar(tareas);
            return tareas[idx];
        }
    }
}
```
> `System.Threading.Lock` requiere .NET 9+. En .NET 8 usa `private readonly object _lock = new();`.

### 3.2 Tools

`Herramientas/TareasTools.cs`
```csharp
using System.ComponentModel;
using McpTareas.Dominio;
using ModelContextProtocol;
using ModelContextProtocol.Server;

namespace McpTareas.Herramientas;

[McpServerToolType]
public sealed class TareasTools(AlmacenTareas almacen)   // DI por constructor
{
    [McpServerTool(Name = "agregar_tarea", UseStructuredContent = true)]
    [Description("Crea una tarea nueva. Úsala cuando el usuario quiera apuntar, añadir o crear un pendiente.")]
    public Tarea Agregar(
        [Description("Texto corto de la tarea (máx. 200 caracteres)")] string titulo,
        [Description("Prioridad: Alta, Media o Baja")] Prioridad prioridad = Prioridad.Media)
    {
        if (string.IsNullOrWhiteSpace(titulo) || titulo.Length > 200)
            throw new McpException("El título debe tener entre 1 y 200 caracteres.");
        return almacen.Agregar(titulo, prioridad);
    }

    [McpServerTool(Name = "listar_tareas", ReadOnly = true, UseStructuredContent = true)]
    [Description("Lista las tareas (por defecto solo pendientes). Úsala para consultar el estado.")]
    public IReadOnlyList<Tarea> Listar(
        [Description("true para mostrar solo pendientes")] bool soloPendientes = true)
        => almacen.Listar(soloPendientes);

    [McpServerTool(Name = "completar_tarea")]
    [Description("Marca una tarea como completada por su id. Si no conoces el id, usa antes listar_tareas.")]
    public string Completar([Description("Id numérico de la tarea")] int tareaId)
    {
        var tarea = almacen.Completar(tareaId)
            ?? throw new McpException($"No existe la tarea {tareaId}. Usa listar_tareas para ver los ids.");
        return $"Tarea #{tarea.Id} completada.";
    }

    [McpServerTool(Name = "resumen")]
    [Description("Resumen numérico del estado de las tareas.")]
    public async Task<string> Resumen(IProgress<ProgressNotificationValue> progreso, CancellationToken ct)
    {
        progreso.Report(new() { Progress = 1, Total = 2, Message = "Leyendo tareas" });
        var todas = almacen.Listar(false);
        await Task.Delay(10, ct);
        progreso.Report(new() { Progress = 2, Total = 2, Message = "Listo" });
        var pendientes = todas.Count(t => !t.Completada);
        return $"Total: {todas.Count} · Pendientes: {pendientes}";
    }
}
```

**Puntos clave**
- `[Description]` en método y parámetros → descripción y JSON Schema generados.
- Los servicios registrados en DI (constructor o parámetros como `IProgress<>`, `CancellationToken`, `McpServer`) **no** aparecen en el schema.
- Lanzar `McpException` → el cliente recibe un resultado con `isError = true` y tu mensaje.
- `UseStructuredContent = true` → salida estructurada con `outputSchema`.
- `ReadOnly`, `Destructive`, `Idempotent` → anotaciones para el host.

### 3.3 Resources

`Recursos/TareasResources.cs`
```csharp
using System.ComponentModel;
using System.Text.Json;
using McpTareas.Dominio;
using ModelContextProtocol.Server;

namespace McpTareas.Recursos;

[McpServerResourceType]
public sealed class TareasResources(AlmacenTareas almacen)
{
    [McpServerResource(UriTemplate = "tareas://pendientes", Name = "pendientes", MimeType = "text/plain")]
    [Description("Lista legible de tareas pendientes")]
    public string Pendientes()
    {
        var lineas = almacen.Listar(true).Select(t => $"- [{t.Prioridad}] #{t.Id} {t.Titulo}");
        var texto = string.Join('\n', lineas);
        return texto.Length > 0 ? texto : "No hay tareas pendientes.";
    }

    [McpServerResource(UriTemplate = "tareas://{id}", Name = "tarea", MimeType = "application/json")]
    [Description("Detalle de una tarea en JSON")]
    public string Tarea(int id) =>
        JsonSerializer.Serialize(almacen.Obtener(id));
}
```

### 3.4 Prompts

`Prompts/TareasPrompts.cs`
```csharp
using System.ComponentModel;
using ModelContextProtocol.Server;

namespace McpTareas.Prompts;

[McpServerPromptType]
public static class TareasPrompts
{
    [McpServerPrompt(Name = "planificar_dia")]
    [Description("Plan del día con las tareas pendientes")]
    public static string PlanificarDia([Description("Horas disponibles")] int horas = 8) =>
        $"Tengo {horas} horas. Usa listar_tareas y propón un plan ordenado por prioridad con estimaciones.";
}
```

### 3.5 `Program.cs`

```csharp
using McpTareas.Dominio;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

var builder = Host.CreateApplicationBuilder(args);

// CRÍTICO: en stdio, stdout es el protocolo → todos los logs a stderr
builder.Logging.AddConsole(o => o.LogToStandardErrorThreshold = LogLevel.Trace);

var ruta = Environment.GetEnvironmentVariable("TAREAS_ARCHIVO") ?? "tareas.json";
builder.Services.AddSingleton(new AlmacenTareas(ruta));

builder.Services
    .AddMcpServer()
    .WithStdioServerTransport()
    .WithToolsFromAssembly()
    .WithResourcesFromAssembly()
    .WithPromptsFromAssembly();

await builder.Build().RunAsync();
```

### Ejecutar y probar
```bash
dotnet run                                   # espera en stdin: normal
npx @modelcontextprotocol/inspector dotnet run --project .
```

---

## 4. Versión HTTP con ASP.NET Core

```bash
dotnet new web -n McpTareas.Http
cd McpTareas.Http
dotnet add package ModelContextProtocol.AspNetCore
# reutiliza las clases de Dominio/Herramientas/Recursos/Prompts (proyecto compartido o referencia)
```

`Program.cs`
```csharp
using McpTareas.Dominio;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddSingleton(new AlmacenTareas(
    builder.Configuration["TareasArchivo"] ?? "tareas.json"));

builder.Services
    .AddMcpServer()
    .WithHttpTransport()          // v2: stateless por defecto (compatible con 2026-07-28)
    .WithToolsFromAssembly(typeof(AlmacenTareas).Assembly)
    .WithResourcesFromAssembly(typeof(AlmacenTareas).Assembly)
    .WithPromptsFromAssembly(typeof(AlmacenTareas).Assembly);

var app = builder.Build();

app.MapMcp("/mcp");   // endpoint MCP

app.Run("http://localhost:5050");
```

- Añade autenticación con el pipeline estándar de ASP.NET Core (`AddAuthentication`, `RequireAuthorization()` sobre `MapMcp`), CORS y rate limiting como en cualquier API.
- Como en v2 no hay sesiones de protocolo, puedes escalar horizontalmente detrás de un balanceador sin *sticky sessions*.

---

## 5. Conectar a clientes

```bash
# Claude Code (stdio)
claude mcp add tareas-cs -- dotnet run --project /ruta/absoluta/McpTareas
# Mejor rendimiento: publica y apunta al ejecutable
dotnet publish -c Release -o ./publish
claude mcp add tareas-cs -- /ruta/absoluta/McpTareas/publish/McpTareas

# Claude Code (HTTP)
claude mcp add --transport http tareas-cs-http http://localhost:5050/mcp
```
```jsonc
// OpenCode
{
  "mcp": {
    "servers": {
      "tareas-cs": { "type": "local", "command": ["dotnet", "run", "--project", "/ruta/absoluta/McpTareas"] }
    }
  }
}
```

> 💡 `dotnet run` compila en cada arranque (lento y puede exceder el *timeout* de arranque del cliente). Para uso diario, publica el ejecutable o empaquétalo como **.NET tool** (`PackAsTool`) y ejecútalo con `dnx` / `dotnet tool run`.

---

## 6. Tests con xUnit

```bash
dotnet new xunit -n McpTareas.Tests
cd McpTareas.Tests
dotnet add reference ../McpTareas/McpTareas.csproj
dotnet add package ModelContextProtocol
```

`AlmacenTests.cs` (unitario)
```csharp
using McpTareas.Dominio;

public class AlmacenTests
{
    private static AlmacenTareas Nuevo() => new(Path.Combine(Path.GetTempPath(), $"{Guid.NewGuid()}.json"));

    [Fact]
    public void Agregar_AsignaIdsIncrementales()
    {
        var a = Nuevo();
        Assert.Equal(1, a.Agregar("A", Prioridad.Media).Id);
        Assert.Equal(2, a.Agregar("B", Prioridad.Alta).Id);
    }

    [Fact]
    public void Completar_Inexistente_DevuelveNull() => Assert.Null(Nuevo().Completar(99));
}
```

`ServidorTests.cs` (integración por protocolo)
```csharp
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol;

public class ServidorTests
{
    [Fact]
    public async Task FlujoCompleto()
    {
        var transport = new StdioClientTransport(new StdioClientTransportOptions
        {
            Name = "tareas",
            Command = "dotnet",
            Arguments = ["run", "--project", "../../../../McpTareas"],
            EnvironmentVariables = new Dictionary<string, string?>
            {
                ["TAREAS_ARCHIVO"] = Path.Combine(Path.GetTempPath(), $"{Guid.NewGuid()}.json")
            }
        });

        await using var client = await McpClient.CreateAsync(transport);

        var tools = await client.ListToolsAsync();
        Assert.Contains(tools, t => t.Name == "agregar_tarea");

        var ok = await client.CallToolAsync("agregar_tarea",
            new Dictionary<string, object?> { ["titulo"] = "Probar", ["prioridad"] = "Alta" });
        Assert.NotEqual(true, ok.IsError);

        var error = await client.CallToolAsync("completar_tarea",
            new Dictionary<string, object?> { ["tareaId"] = 999 });
        Assert.True(error.IsError);
    }
}
```
> Los nombres de parámetros en el schema se derivan de C# (`tareaId`, `soloPendientes`). Compruébalos en el Inspector.

---

## Errores comunes

- `Console.WriteLine` en el servidor stdio → corrompe el protocolo.
- No configurar `LogToStandardErrorThreshold` → los logs de hosting van a stdout.
- Usar paquetes `0.x-preview` o tutoriales 1.x con defaults antiguos.
- Clases de tools sin `[McpServerToolType]` → no se descubren.
- `dotnet run` demasiado lento al arrancar → publica el binario.

## Ejercicios

1. Implementa el servidor stdio y pruébalo en el Inspector.
2. Crea la versión HTTP, protégela con una API key mediante middleware y conéctala desde Claude Code con una cabecera (`--header "X-Api-Key: ..."`).
3. Añade `eliminar_tarea` con `Destructive = true` y verifica que el host pide confirmación.
4. Ejecuta los tests de integración en CI (GitHub Actions con `setup-dotnet`).
   - ✅ Éxito: el pipeline compila, arranca el servidor y pasa los tests.

## Checklist

- [ ] Sé elegir el paquete correcto (`ModelContextProtocol` / `.AspNetCore` / `.Core`).
- [ ] Uso atributos y DI para tools, resources y prompts.
- [ ] Logs a stderr en stdio.
- [ ] Tengo versión stdio y HTTP con tests.

---

⬅️ [05.3](03-mcp-servidor-nodejs.md) · ➡️ [05.5 · Clientes MCP](05-mcp-clientes-python-node-csharp.md)
