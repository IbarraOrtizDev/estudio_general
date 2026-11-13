# 6.2 App registrations y Microsoft.Identity.Web

[⬅ Anterior: Fundamentos](01-fundamentos-identidad.md) · [Índice](../README.md) · [Siguiente: Managed Identities ➡](03-managed-identities-rbac.md)

## 🎯 Objetivos
- Registrar una API y sus clientes en Entra ID (scopes y app roles).
- Proteger una API ASP.NET Core con Microsoft.Identity.Web.
- Autorizar por scopes, app roles y policies.
- Llamar a otra API (Microsoft Graph u otra propia) en nombre del usuario (OBO) o como aplicación.

---

## 1. Registrar la API (OrderFlow API)

*Entra admin center → Identity → Applications → App registrations → New registration*

1. **Name:** `OrderFlow API` · **Supported account types:** *Accounts in this organizational directory only* (single tenant).
2. **Expose an API:**
   - *Application ID URI:* `api://orderflow-api` (o `api://<client-id>`).
   - *Add a scope:* `Orders.Read` y `Orders.Write` (Who can consent: Admins and users / Admins only).
3. **App roles** (*App roles → Create app role*):
   | Display name | Value | Allowed member types | Uso |
   |--------------|-------|---------------------|-----|
   | Orders Admin | `Orders.Admin` | Users/Groups | Administradores humanos |
   | Orders Processor | `Orders.Process` | Applications | Workers/daemons (application permission) |
4. **Manifest:** `"requestedAccessTokenVersion": 2` (tokens v2.0).
5. (Opcional) *Enterprise applications → OrderFlow API → Properties → Assignment required = Yes* y asigna usuarios/grupos con sus roles.

### Registrar el cliente (ej. SPA)
1. New registration `OrderFlow Web` → Platform **Single-page application** → Redirect URI `https://localhost:5173`.
2. *API permissions → Add → My APIs → OrderFlow API → Delegated → Orders.Read, Orders.Write* → Grant admin consent (si aplica).

### Como código (recomendado para entornos repetibles)
- **Microsoft Graph Bicep extension** (`Microsoft.Graph/applications`) permite declarar app registrations en Bicep.
- O scripts con `az ad app create` / Microsoft Graph PowerShell en el pipeline de plataforma.

---

## 2. Proteger la API con Microsoft.Identity.Web

```bash
dotnet add package Microsoft.Identity.Web
```

### `appsettings.json`
```json
{
  "AzureAd": {
    "Instance": "https://login.microsoftonline.com/",
    "TenantId": "<tenant-id>",
    "ClientId": "<client-id-de-OrderFlow-API>",
    "Audience": "api://orderflow-api"
  }
}
```
> Ni `TenantId` ni `ClientId` son secretos, pero son configuración por entorno → variables de entorno / App Configuration.

### `Program.cs`
```csharp
using Microsoft.Identity.Web;

builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddMicrosoftIdentityWebApi(builder.Configuration.GetSection("AzureAd"));

builder.Services.AddAuthorizationBuilder()
    // Usuarios: scope delegado
    .AddPolicy("Orders.Read", p => p.RequireScopeOrAppPermission(
        allowedScopeValues: ["Orders.Read", "Orders.Write"],
        allowedAppPermissionValues: ["Orders.Process"]))
    .AddPolicy("Orders.Write", p => p.RequireScopeOrAppPermission(
        allowedScopeValues: ["Orders.Write"],
        allowedAppPermissionValues: ["Orders.Process"]))
    // Admins humanos: app role
    .AddPolicy("Orders.Admin", p => p.RequireRole("Orders.Admin"))
    // Seguro por defecto: todo endpoint requiere usuario autenticado salvo que diga lo contrario
    .SetFallbackPolicy(new AuthorizationPolicyBuilder().RequireAuthenticatedUser().Build());

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/orders", ListOrders.Handle).RequireAuthorization("Orders.Read");
app.MapPost("/orders", PlaceOrder.Handle).RequireAuthorization("Orders.Write");
app.MapPost("/orders/{id:guid}/refund", RefundOrder.Handle).RequireAuthorization("Orders.Admin");
app.MapHealthChecks("/alive").AllowAnonymous();
```

`AddMicrosoftIdentityWebApi` valida automáticamente: firma (con las claves del JWKS, cacheadas y rotadas), issuer, **audience**, expiración.

### Leer la identidad del usuario
```csharp
public sealed class CurrentUser(IHttpContextAccessor accessor) : ICurrentUser
{
    private ClaimsPrincipal User => accessor.HttpContext?.User ?? new();

    public Guid ObjectId => Guid.Parse(User.GetObjectId()!);   // claim oid — clave estable
    public Guid TenantId => Guid.Parse(User.GetTenantId()!);   // claim tid
    public string? Name => User.GetDisplayName();
    public bool IsAdmin => User.IsInRole("Orders.Admin");
}
```
> Guarda `oid` (+ `tid`) como referencia del usuario en tu base de datos; nunca el email.

### Autorización basada en recursos (¿es SU pedido?)
Los scopes/roles dicen "puede leer pedidos", no "puede leer **este** pedido".
```csharp
public sealed class OrderOwnerHandler : AuthorizationHandler<SameOwnerRequirement, Order>
{
    protected override Task HandleRequirementAsync(AuthorizationHandlerContext ctx,
        SameOwnerRequirement req, Order order)
    {
        if (order.CustomerId.ToString() == ctx.User.GetObjectId() || ctx.User.IsInRole("Orders.Admin"))
            ctx.Succeed(req);
        return Task.CompletedTask;
    }
}

// En el handler del endpoint:
var auth = await authorizationService.AuthorizeAsync(user, order, new SameOwnerRequirement());
if (!auth.Succeeded) return Results.Forbid();
```

### Grupos vs app roles
| | Grupos (`groups` claim) | App roles (`roles` claim) |
|--|------------------------|---------------------------|
| Significado | Estructura organizacional | Permisos **de tu app** |
| Límite en token | *Overage* > 200 grupos (hay que consultar Graph) | Sin ese problema |
| Portabilidad | IDs de grupos distintos por tenant | Valores definidos por ti |
| **Recomendación** | Asigna **grupos a app roles** en la Enterprise app | ✅ Autoriza por app roles |

---

## 3. Llamar a otras APIs desde tu API

### On-Behalf-Of (en nombre del usuario)
```csharp
builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddMicrosoftIdentityWebApi(builder.Configuration.GetSection("AzureAd"))
    .EnableTokenAcquisitionToCallDownstreamApi()
    .AddDownstreamApi("PaymentsApi", builder.Configuration.GetSection("PaymentsApi"))
    .AddMicrosoftGraph(builder.Configuration.GetSection("Graph"))   // paquete Microsoft.Identity.Web.GraphServiceClient
    .AddDistributedTokenCaches();                                   // cache en Redis/SQL (multi-instancia)
```
```json
{
  "AzureAd": {
    "Instance": "https://login.microsoftonline.com/",
    "TenantId": "<tenant-id>",
    "ClientId": "<client-id>",
    "Audience": "api://orderflow-api",
    "ClientCredentials": [
      {
        "SourceType": "SignedAssertionFromManagedIdentity",
        "ManagedIdentityClientId": "<client-id-de-la-user-assigned-MI>"
      }
    ]
  },
  "PaymentsApi": {
    "BaseUrl": "https://payments.internal/",
    "Scopes": [ "api://payments-api/Payments.Charge" ]
  },
  "Graph": { "Scopes": [ "User.Read" ] }
}
```
> ⭐ `SignedAssertionFromManagedIdentity` = la app registration confía en una **managed identity** mediante *federated identity credential*. **Cero secretos y cero certificados que rotar** para la credencial de la API. Para desarrollo local puedes usar un certificado o secreto en *user-secrets*.

```csharp
public sealed class PaymentsClient(IDownstreamApi api)
{
    // Obtiene token OBO para Payments.Charge y llama a la API
    public Task<PaymentDto?> ChargeAsync(ChargeRequest req, CancellationToken ct) =>
        api.PostForUserAsync<ChargeRequest, PaymentDto>("PaymentsApi", req,
            o => o.RelativePath = "charges", cancellationToken: ct);
}

public sealed class ProfileService(GraphServiceClient graph)
{
    public async Task<string?> GetJobTitleAsync() => (await graph.Me.GetAsync())?.JobTitle;
}
```

### Como aplicación (sin usuario: worker/daemon)
```csharp
// Worker que llama a OrderFlow API con permiso de aplicación Orders.Process
public sealed class OrdersApiCaller(IDownstreamApi api)
{
    public Task<IReadOnlyList<OrderDto>?> GetPendingAsync(CancellationToken ct) =>
        api.GetForAppAsync<IReadOnlyList<OrderDto>>("OrderFlowApi",
            o => o.RelativePath = "orders?status=pending", cancellationToken: ct);
}
// Config: "Scopes": [ "api://orderflow-api/.default" ]  ← client credentials siempre usa .default
```
O directamente con `Azure.Identity` + Managed Identity ([6.3](03-managed-identities-rbac.md)).

---

## 4. Web apps (login de usuarios)
```csharp
builder.Services.AddAuthentication(OpenIdConnectDefaults.AuthenticationScheme)
    .AddMicrosoftIdentityWebApp(builder.Configuration.GetSection("AzureAd"))
    .EnableTokenAcquisitionToCallDownstreamApi(["api://orderflow-api/Orders.Read"])
    .AddInMemoryTokenCaches();
builder.Services.AddRazorPages().AddMicrosoftIdentityUI();
```
Para SPAs: el frontend usa **MSAL.js** (`@azure/msal-browser` / `@azure/msal-react` / `@azure/msal-angular`) y envía el access token a la API. Alternativa con más seguridad: patrón **BFF** (Backend for Frontend) — el token vive en el servidor y el navegador solo tiene una cookie.

---

## 5. Probar localmente
- **Swagger/Scalar con OAuth:** configura el flujo Authorization Code + PKCE con un client registrado como SPA.
- **Token para pruebas rápidas:** `az account get-access-token --scope api://orderflow-api/Orders.Read` (requiere que Azure CLI esté preautorizado en la API o tener consentimiento).
- **Tests de integración:** reemplaza el esquema de autenticación por uno de prueba en `WebApplicationFactory` (no llames a Entra en tests automatizados).

```csharp
builder.ConfigureTestServices(s =>
    s.AddAuthentication("Test").AddScheme<AuthenticationSchemeOptions, TestAuthHandler>("Test", _ => { }));
```

## ⚠️ Errores comunes
| Síntoma | Causa probable |
|---------|----------------|
| `401` con `invalid_token` / `audience is invalid` | El token se pidió para otra API, o `Audience` mal configurado |
| `401` con `issuer is invalid` | Token v1 vs v2 (`requestedAccessTokenVersion`) o tenant distinto |
| `403` | Token válido pero sin el scope/role requerido |
| `AADSTS65001` | Falta consentimiento |
| `AADSTS50011` | Redirect URI no coincide |
| `AADSTS700016` | Client ID incorrecto o app en otro tenant |
| Funciona en local, falla en Azure | Forwarded headers/redirect HTTPS ([7.2](../modulo-07-redes/02-http-tls-dns.md)), o config de entorno faltante |

## ✅ Checklist
- [ ] Registré una API con scopes y app roles, y un cliente con permisos delegados.
- [ ] Mi API usa `AddMicrosoftIdentityWebApi` y una fallback policy segura.
- [ ] Autorizo con policies por scope/app role y por recurso.
- [ ] Sé implementar OBO y client credentials con Microsoft.Identity.Web.
- [ ] Mi API usa credenciales sin secreto (federación con managed identity).

## 🏋️ Ejercicio (OrderFlow)
1. Registra `OrderFlow API` (scopes `Orders.Read`, `Orders.Write`; roles `Orders.Admin`, `Orders.Process`) y `OrderFlow Web` (SPA).
2. Protege todos los endpoints con policies; agrega autorización por recurso al consultar un pedido.
3. Haz que el Worker llame a la API con el permiso de aplicación `Orders.Process`.
4. Escribe tests de integración con un `TestAuthHandler` que simule distintos roles.

## 📚 Profundiza
- [Microsoft.Identity.Web (GitHub wiki)](https://github.com/AzureAD/microsoft-identity-web/wiki).
- [Protected web API scenario](https://learn.microsoft.com/entra/identity-platform/scenario-protected-web-api-overview).
- [Add app roles and get them from a token](https://learn.microsoft.com/entra/identity-platform/howto-add-app-roles-in-apps).
