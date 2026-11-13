# 3.2 Logging estructurado en .NET

[⬅ Anterior: Fundamentos](01-fundamentos.md) · [Índice](../README.md) · [Siguiente: OpenTelemetry ➡](03-opentelemetry-dotnet.md)

## 🎯 Objetivos
- Escribir logs estructurados, consultables y de alto rendimiento con `ILogger`.
- Usar el source generator `[LoggerMessage]`, scopes y niveles correctamente.
- Proteger datos sensibles (redaction) y controlar costos.

---

## 1. Texto plano vs estructurado

```csharp
// ❌ Interpolación: se pierde la estructura, se asigna memoria aunque el nivel esté deshabilitado
logger.LogInformation($"Pedido {orderId} creado por {customerId} con total {total}");

// ✅ Message template: cada placeholder se convierte en un campo consultable
logger.LogInformation("Pedido {OrderId} creado por {CustomerId} con total {Total}", orderId, customerId, total);
```
El resultado en el backend:
```json
{
  "Timestamp": "2026-11-13T15:04:05Z",
  "Level": "Information",
  "MessageTemplate": "Pedido {OrderId} creado por {CustomerId} con total {Total}",
  "OrderId": "0193f2a1-...",
  "CustomerId": "c-42",
  "Total": 150000,
  "TraceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "SpanId": "00f067aa0ba902b7"
}
```
Ahora puedes consultar: "todos los logs del pedido X", "promedio de Total por hora", "todo lo que pasó en esta traza".

> 💡 Usa **PascalCase** y nombres consistentes para los campos (`OrderId` siempre igual en todo el sistema). Un diccionario de campos estándar es parte de la gobernanza.

---

## 2. `[LoggerMessage]` source generator ⭐ (la forma recomendada)

Genera en compilación código sin boxing ni parseo de templates en runtime. Además centraliza los mensajes y les asigna `EventId`.

```csharp
internal static partial class OrderingLog
{
    [LoggerMessage(EventId = 1001, Level = LogLevel.Information,
        Message = "Pedido {OrderId} creado para cliente {CustomerId} con {ItemCount} ítems")]
    public static partial void OrderCreated(this ILogger logger, Guid orderId, string customerId, int itemCount);

    [LoggerMessage(EventId = 1002, Level = LogLevel.Warning,
        Message = "Pago rechazado para pedido {OrderId}: {Reason}")]
    public static partial void PaymentDeclined(this ILogger logger, Guid orderId, string reason);

    [LoggerMessage(EventId = 1003, Level = LogLevel.Error,
        Message = "Error publicando mensaje de outbox {MessageId}")]
    public static partial void OutboxPublishFailed(this ILogger logger, Exception ex, Guid messageId);
}

// Uso
logger.OrderCreated(order.Id, order.CustomerId.ToString(), order.Items.Count);
logger.OutboxPublishFailed(ex, msg.Id);
```

---

## 3. Niveles de log: guía práctica

| Nivel | Cuándo | ¿En producción? |
|-------|--------|-----------------|
| `Trace` | Detalle extremo (payloads, pasos internos) | No |
| `Debug` | Información útil para desarrollo | No (o temporalmente) |
| `Information` | Eventos de negocio relevantes / ciclo de vida | Sí, con moderación |
| `Warning` | Algo inesperado pero recuperable (retry, fallback, validación de negocio fallida recurrente) | Sí |
| `Error` | Una operación falló | Sí |
| `Critical` | La app no puede continuar | Sí |

```json
// appsettings.json — controla verbosidad por categoría (namespace)
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning",
      "Microsoft.EntityFrameworkCore.Database.Command": "Warning",
      "OrderFlow": "Information"
    }
  }
}
```

> ⚠️ **No loguees y relances** la misma excepción en cada capa: tendrás 5 logs del mismo error. Loguea donde la manejas (o deja que el middleware global la registre).

---

## 4. Scopes: contexto que se hereda

```csharp
using (logger.BeginScope(new Dictionary<string, object>
{
    ["OrderId"] = command.OrderId,
    ["TenantId"] = tenant.Id
}))
{
    logger.LogInformation("Iniciando cobro");   // incluye OrderId y TenantId
    await gateway.ChargeAsync(...);
    logger.LogInformation("Cobro completado");  // también
}
```
Con OpenTelemetry, configura `IncludeScopes = true` para exportarlos.

---

## 5. Manejo global de errores (logs + ProblemDetails)

```csharp
builder.Services.AddProblemDetails(o =>
    o.CustomizeProblemDetails = ctx =>
        ctx.ProblemDetails.Extensions["traceId"] = Activity.Current?.TraceId.ToString());

builder.Services.AddExceptionHandler<GlobalExceptionHandler>();

internal sealed class GlobalExceptionHandler(ILogger<GlobalExceptionHandler> logger,
    IProblemDetailsService problemDetails) : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(HttpContext ctx, Exception ex, CancellationToken ct)
    {
        logger.LogError(ex, "Excepción no controlada en {Path}", ctx.Request.Path);
        ctx.Response.StatusCode = StatusCodes.Status500InternalServerError;
        return await problemDetails.TryWriteAsync(new()
        {
            HttpContext = ctx,
            ProblemDetails = { Title = "Error interno", Status = 500 },
            Exception = ex
        });
    }
}

app.UseExceptionHandler();
```
El cliente recibe un `traceId` que el soporte puede buscar directamente en Application Insights. 🎯

---

## 6. Datos sensibles y redaction

**Nunca** loguees: contraseñas, tokens, números de tarjeta, documentos de identidad completos, datos de salud. (Ley 1581 de 2012 en Colombia, GDPR, PCI-DSS).

### `Microsoft.Extensions.Compliance.Redaction`
```csharp
// 1. Clasifica datos
public static class DataTaxonomy
{
    public static DataClassification Pii => new("OrderFlow", "PII");
}
public sealed class PiiAttribute() : DataClassificationAttribute(DataTaxonomy.Pii);

// 2. En el log
[LoggerMessage(Level = LogLevel.Information, Message = "Cliente {Email} registrado")]
public static partial void CustomerRegistered(this ILogger logger, [Pii] string email);

// 3. Configura
builder.Logging.EnableRedaction();
builder.Services.AddRedaction(r =>
    r.SetRedactor<ErasingRedactor>(new DataClassificationSet(DataTaxonomy.Pii)));
```

---

## 7. Logging de requests HTTP

```csharp
builder.Services.AddHttpLogging(o =>
{
    o.LoggingFields = HttpLoggingFields.RequestMethod | HttpLoggingFields.RequestPath |
                      HttpLoggingFields.ResponseStatusCode | HttpLoggingFields.Duration;
    o.CombineLogs = true; // una sola línea por request
});
app.UseHttpLogging();
```
> Con OpenTelemetry ya tienes spans por request con método, ruta, status y duración; el HTTP logging suele ser redundante en producción. Úsalo en diagnóstico puntual.

---

## 8. ¿Serilog o el logging nativo?

| | `Microsoft.Extensions.Logging` + OpenTelemetry | Serilog |
|--|------------------------------------------------|---------|
| Estándar de la plataforma | ✅ | Proveedor sobre `ILogger` |
| Exportación OTLP / Azure Monitor | ✅ nativa | Vía sinks |
| Sinks (archivo, Seq, Elastic…) | Limitados | Ecosistema enorme |
| Enrichers, configuración avanzada | Básico | Muy rico |

**Recomendación 2026:** escribe siempre contra `ILogger<T>` (abstracción). Exporta con **OpenTelemetry**. Agrega Serilog solo si necesitas sinks/enrichers específicos — tu código no cambia.

---

## ✅ Checklist
- [ ] Cero logs con interpolación de strings.
- [ ] Uso `[LoggerMessage]` para logs frecuentes.
- [ ] Mis respuestas de error incluyen `traceId`.
- [ ] No logueo datos sensibles; sé configurar redaction.
- [ ] Configuro niveles por categoría.

## 🏋️ Ejercicio (OrderFlow)
1. Crea `OrderingLog` con 6 mensajes `[LoggerMessage]` y reemplaza todos los logs.
2. Implementa `GlobalExceptionHandler` con `traceId` en ProblemDetails.
3. Marca el email del cliente como `[Pii]` y verifica que sale redactado.
4. Agrega un analyzer que prohíba interpolación en logs (CA2254 ya lo advierte — súbelo a error).

## 📚 Profundiza
- [Logging in .NET](https://learn.microsoft.com/dotnet/core/extensions/logging).
- [Compile-time logging source generation](https://learn.microsoft.com/dotnet/core/extensions/logger-message-generator).
- [Data redaction in .NET](https://learn.microsoft.com/dotnet/core/extensions/data-redaction).
