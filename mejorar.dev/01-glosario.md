# 📖 Glosario

> Términos en inglés (como se usan en la industria) con su explicación en español.
> Etiquetas: **[P]** Patrones · **[A]** Arquitectura · **[O]** Observabilidad · **[G]** Gobernabilidad · **[C]** CI/CD · **[E]** Entra / Identidad · **[R]** Redes · **[.NET]** específico de .NET

[⬅ Volver al índice](README.md)

**Saltar a:** [A](#a) · [B](#b) · [C](#c) · [D](#d) · [E](#e) · [F](#f) · [G](#g) · [H](#h) · [I](#i) · [J](#j) · [K](#k) · [L](#l) · [M](#m) · [N](#n) · [O](#o) · [P](#p) · [Q](#q) · [R](#r) · [S](#s) · [T](#t) · [U](#u) · [V](#v) · [W](#w) · [Y](#y) · [Z](#z)

---

## A
- **Access token** [E] — Token (normalmente JWT) que una app presenta a una API para demostrar que tiene permiso. Vida corta (≈ 1 h).
- **Activity / ActivitySource** [O][.NET] — Implementación .NET de un *span* de OpenTelemetry. `ActivitySource` crea `Activity`s.
- **Adapter** [P] — Patrón que convierte la interfaz de una clase en otra que el cliente espera.
- **ADR (Architecture Decision Record)** [G] — Documento corto que registra una decisión de arquitectura, su contexto y consecuencias.
- **Agent pool** [C] — Conjunto de máquinas (agents) que ejecutan los jobs de un pipeline. *Microsoft-hosted* o *self-hosted*.
- **Aggregate / Aggregate Root** [A] — En DDD, grupo de objetos que se tratan como una unidad de consistencia; solo se accede a ellos a través de la raíz.
- **Anemic Domain Model** [A] — Antipatrón: entidades con solo propiedades y toda la lógica en "servicios".
- **Anti-Corruption Layer (ACL)** [A] — Capa que traduce entre tu modelo y el de un sistema externo para que este no "contamine" tu dominio.
- **API Gateway** [A] — Punto de entrada único que enruta, autentica y limita peticiones hacia servicios internos.
- **APIM (Azure API Management)** [G] — Servicio de Azure para publicar, proteger, versionar y gobernar APIs.
- **App registration** [E] — Registro de una aplicación en Entra ID; define su identidad (client ID), permisos y URLs.
- **App roles** [E] — Roles definidos en una app registration que se asignan a usuarios, grupos o aplicaciones; llegan en el claim `roles`.
- **Application Gateway** [R] — Balanceador regional de capa 7 de Azure con WAF, enrutamiento por path/host y terminación TLS.
- **Application Insights** [O] — Componente de Azure Monitor para telemetría de aplicaciones (APM).
- **Approval / Check** [C] — Condición que debe cumplirse antes de que un stage despliegue a un environment (aprobación humana, horario, query a Azure Monitor…).
- **ARP** [R] — Protocolo que traduce direcciones IP a direcciones MAC dentro de una red local.
- **Artifact** [C] — Resultado de un build (binarios, paquetes, imágenes) que se publica para usarlo en etapas posteriores.
- **Aspire** [A][.NET] — Plataforma de Microsoft (antes ".NET Aspire") para orquestar, observar y desplegar aplicaciones distribuidas en desarrollo local y la nube.
- **At-least-once delivery** [A] — Garantía de mensajería: cada mensaje llega una o más veces. Exige consumidores idempotentes.
- **Audience (`aud`)** [E] — Claim del token que indica para qué API fue emitido. La API debe validarlo.
- **Authentication (AuthN)** [E] — Verificar **quién eres**.
- **Authorization (AuthZ)** [E] — Decidir **qué puedes hacer**.
- **Authorization Code Flow + PKCE** [E] — Flujo OAuth recomendado para apps con usuario (web, SPA, móvil).
- **Autoscaling** [A] — Ajustar automáticamente el número de instancias según la carga.
- **Azure Policy** [G] — Servicio que evalúa y obliga reglas sobre recursos Azure (ej. "solo se permite East US").
- **Azure RBAC** [E][G] — Control de acceso basado en roles sobre recursos de Azure (Owner, Contributor, Reader, roles específicos de datos).

## B
- **Backpressure** [A] — Mecanismo para que un consumidor lento frene a un productor rápido.
- **Bandwidth (ancho de banda)** [R] — Cantidad de datos que se pueden transmitir por unidad de tiempo. No confundir con latencia.
- **Bicep** [C] — Lenguaje declarativo de Microsoft para infraestructura como código en Azure (compila a ARM JSON).
- **Blue-Green deployment** [C] — Dos entornos idénticos; se despliega en el inactivo y se cambia el tráfico de golpe.
- **Bounded Context** [A] — En DDD, frontera explícita dentro de la cual un modelo y su lenguaje tienen un significado único.
- **Branch policy** [C][G] — Reglas sobre una rama en Azure Repos: revisores mínimos, build validation, work items vinculados.
- **Builder** [P] — Patrón que construye objetos complejos paso a paso.
- **Bulkhead** [A] — Aislar recursos (hilos, conexiones) para que un fallo no consuma todo el sistema.

## C
- **Cache-aside** [A] — Patrón: la app busca en caché; si no está, lee la base de datos y guarda en caché.
- **Canary release** [C] — Liberar a un porcentaje pequeño de usuarios antes del 100 %.
- **CAP theorem** [A] — En presencia de particiones de red, un sistema distribuido elige entre Consistencia y Disponibilidad.
- **Cardinality (alta)** [O] — Muchos valores distintos en una etiqueta de métrica (ej. `userId`); dispara costos y degrada el backend.
- **Central Package Management (CPM)** [G][.NET] — Gestión de versiones NuGet en un único `Directory.Packages.props`.
- **Chain of Responsibility** [P] — Pasar una petición por una cadena de manejadores; cada uno decide procesarla o pasarla. El middleware de ASP.NET Core es un ejemplo.
- **Choreography** [A] — Coordinación de servicios mediante eventos, sin un orquestador central.
- **CIDR** [R] — Notación `IP/prefijo` (ej. `10.0.1.0/24`) que indica cuántos bits son de red; base del subnetting.
- **Circuit Breaker** [A] — Deja de llamar a un servicio que falla repetidamente durante un tiempo, para darle respiro y fallar rápido.
- **Claim** [E] — Dato dentro de un token (ej. `name`, `oid`, `roles`).
- **Clean Architecture** [A] — Arquitectura en capas concéntricas donde las dependencias apuntan hacia el dominio.
- **Client Credentials Flow** [E] — Flujo OAuth para app-a-app sin usuario (daemons, jobs).
- **Cohesion** [P] — Qué tan relacionadas están las responsabilidades de un módulo. Se busca alta cohesión.
- **Command** [P][A] — (Patrón) encapsular una petición como objeto. (CQRS) operación que cambia estado.
- **Composite** [P] — Tratar objetos individuales y composiciones de forma uniforme (árboles).
- **Conditional Access** [E] — Motor de políticas de Entra: "si X condición, entonces exigir Y" (MFA, dispositivo administrado, bloquear).
- **Connection pooling** [R][.NET] — Reutilizar conexiones abiertas (TCP, BD) en lugar de crear una por operación.
- **Consumer-Driven Contracts** [G] — Pruebas de contrato donde el consumidor define lo que espera de la API (ej. Pact).
- **Context Map** [A] — Diagrama DDD de cómo se relacionan los bounded contexts.
- **Correlation ID** [O] — Identificador que viaja con una petición entre servicios para relacionar sus logs. Con OpenTelemetry se usa el `TraceId`.
- **Coupling** [P] — Grado de dependencia entre módulos. Se busca bajo acoplamiento.
- **CQRS (Command Query Responsibility Segregation)** [A] — Separar el modelo de escritura (commands) del de lectura (queries).

## D
- **DDoS** [R] — Ataque de denegación de servicio distribuido. Azure DDoS Protection lo mitiga.
- **Dead Letter Queue (DLQ)** [A] — Cola donde terminan los mensajes que no pudieron procesarse tras varios intentos.
- **Decorator** [P] — Envolver un objeto para añadirle comportamiento sin modificarlo.
- **DefaultAzureCredential** [E][.NET] — Credencial de Azure.Identity que prueba varias fuentes (variables de entorno, Managed Identity, Visual Studio, Azure CLI…).
- **Delegated permissions** [E] — Permisos que una app ejerce **en nombre de un usuario** (llegan en `scp`).
- **Dependency Injection (DI)** [P][.NET] — Las dependencias se entregan desde fuera en lugar de crearse dentro.
- **Dependency Inversion Principle (DIP)** [P] — Depender de abstracciones, no de implementaciones concretas.
- **Deployment job** [C] — Job especial de Azure Pipelines asociado a un environment, con historial y estrategias (runOnce, rolling, canary).
- **Deployment slot** [C] — Copia de un App Service (ej. `staging`) que permite desplegar y luego hacer *swap* con producción.
- **Distributed tracing** [O] — Seguir una petición a través de múltiples servicios.
- **DNS** [R] — Sistema que traduce nombres (`api.orderflow.com`) a direcciones IP. Registros A, AAAA, CNAME, TXT, MX, NS.
- **Domain Event** [A] — Algo relevante que ocurrió en el dominio (ej. `OrderPlaced`).
- **DORA metrics** [C][G] — Frecuencia de despliegue, lead time, tasa de fallos en cambios y tiempo de recuperación.
- **DRY** [P] — *Don't Repeat Yourself*: no duplicar conocimiento.

## E
- **Egress / Ingress** [R] — Tráfico saliente / entrante de una red o servicio.
- **Entra External ID** [E] — Solución de Entra para identidades de clientes/externos (CIAM); sucesora de Azure AD B2C para clientes nuevos.
- **Entra ID (Microsoft Entra ID)** [E] — Servicio de identidad en la nube de Microsoft (antes Azure Active Directory).
- **Environment (Azure DevOps)** [C] — Destino de despliegue con historial, approvals y checks.
- **Error budget** [O] — Margen de fallos permitido por un SLO (si el SLO es 99,9 %, el presupuesto es 0,1 %).
- **Event Sourcing** [A] — Guardar el estado como secuencia de eventos en lugar de solo el estado actual.
- **Event-Driven Architecture (EDA)** [A] — Componentes que se comunican emitiendo y reaccionando a eventos.
- **Eventual consistency** [A] — Los datos se vuelven consistentes después de un tiempo, no inmediatamente.
- **Exemplar** [O] — Enlace desde un punto de una métrica a una traza concreta.
- **ExpressRoute** [R] — Conexión privada dedicada entre on-premise y Azure, sin pasar por internet.
- **Extends template** [C][G] — Template de Azure Pipelines del que un pipeline debe heredar; permite imponer pasos obligatorios.

## F
- **Facade** [P] — Interfaz simplificada sobre un subsistema complejo.
- **Factory Method / Abstract Factory** [P] — Delegar la creación de objetos a métodos o familias de fábricas.
- **Feature flag / toggle** [C] — Activar o desactivar funcionalidades sin desplegar (ej. Azure App Configuration).
- **Federated credential** [E][C] — Relación de confianza que permite a un sistema externo (ej. Azure DevOps, GitHub) obtener tokens de Entra sin secretos.
- **Fitness function** [G] — Prueba automatizada que verifica una característica arquitectónica (ej. "Domain no referencia Infrastructure").
- **Forwarded headers** [R][.NET] — `X-Forwarded-For`/`X-Forwarded-Proto`: transmiten la IP y el esquema originales cuando hay un proxy en medio.
- **Front Door (Azure)** [R] — Punto de entrada global de capa 7 con CDN, WAF y enrutamiento/failover multi-región.

## G
- **Golden signals** [O] — Latencia, tráfico, errores y saturación (Google SRE).
- **Governance** [G] — Conjunto de reglas, procesos y controles que aseguran que la tecnología se usa de forma consistente, segura y alineada al negocio.
- **gRPC** [R][.NET] — Framework RPC de alto rendimiento sobre HTTP/2 con contratos Protobuf; ideal entre servicios.
- **Guard clause** [P] — Validación al inicio de un método que sale temprano si algo no es válido.

## H
- **Handshake** [R] — Intercambio inicial para establecer una conexión (TCP: SYN/SYN-ACK/ACK; TLS: negociación de claves y certificado).
- **Health check** [O] — Endpoint que indica si la app (y sus dependencias) están sanas.
- **Hexagonal Architecture (Ports & Adapters)** [A] — El núcleo define *ports* (interfaces) y el exterior provee *adapters*.
- **Horizontal scaling (scale out)** [A] — Agregar más instancias.
- **HSTS** [R] — Header que obliga al navegador a usar siempre HTTPS con un dominio.
- **HTTP/2 / HTTP/3** [R] — HTTP/2 multiplexa streams en una conexión TCP; HTTP/3 corre sobre QUIC (UDP) y evita el head-of-line blocking de TCP.
- **Hub-and-spoke** [R] — Topología de red: una VNet central (hub) con servicios compartidos y VNets de cargas de trabajo (spokes) conectadas por peering.
- **HybridCache** [A][.NET] — API de caché de .NET (desde .NET 9) que combina caché en memoria (L1) y distribuida (L2) con protección contra *stampede*.

## I
- **IaC (Infrastructure as Code)** [C] — Definir infraestructura en archivos versionados (Bicep, Terraform).
- **ICMP** [R] — Protocolo de mensajes de control (lo usan `ping` y `traceroute`); a menudo bloqueado en la nube.
- **ID token** [E] — Token OIDC que describe al usuario autenticado; lo consume el cliente, **no** se envía a APIs.
- **Idempotency** [A] — Ejecutar una operación varias veces produce el mismo resultado que una sola vez.
- **IHttpClientFactory** [.NET] — Fábrica para crear `HttpClient` correctamente (evita socket exhaustion, permite resiliencia).
- **Interface Segregation Principle (ISP)** [P] — Muchas interfaces pequeñas mejor que una grande.
- **IOptions / Options pattern** [P][.NET] — Configuración fuertemente tipada y validada.
- **Issuer (`iss`)** [E] — Claim que indica quién emitió el token.

## J
- **JWT (JSON Web Token)** [E] — Formato de token: header.payload.signature, codificado en Base64URL.
- **JWKS** [E] — Conjunto de claves públicas para validar firmas de JWT.

## K
- **KQL (Kusto Query Language)** [O] — Lenguaje de consultas de Azure Monitor / Log Analytics.
- **Key Vault** [E][C] — Servicio de Azure para guardar secretos, claves y certificados.

## L
- **Landing Zone** [G] — Entorno Azure preconfigurado (red, identidad, políticas) listo para alojar cargas de trabajo.
- **Latency (latencia)** [R][O] — Tiempo que tarda un dato en ir y/o volver. Se mide en percentiles (p50, p95, p99).
- **Layered Architecture** [A] — Arquitectura en capas horizontales (presentación, negocio, datos).
- **Liskov Substitution Principle (LSP)** [P] — Una subclase debe poder sustituir a su clase base sin romper el comportamiento.
- **Liveness / Readiness probe** [O] — *Liveness*: ¿el proceso está vivo? *Readiness*: ¿puede recibir tráfico?
- **Load Balancer (Azure)** [R] — Balanceador de capa 4 (TCP/UDP) de alto rendimiento.
- **Log Analytics workspace** [O] — Almacén de logs de Azure Monitor consultable con KQL.
- **LoggerMessage (source generator)** [O][.NET] — Atributo que genera código de logging de alto rendimiento.

## M
- **Managed Identity** [E] — Identidad administrada por Azure para un recurso; permite obtener tokens sin secretos. *System-assigned* o *user-assigned*.
- **Mediator** [P] — Objeto que centraliza la comunicación entre otros para reducir acoplamiento.
- **Meter / Counter / Histogram** [O][.NET] — API `System.Diagnostics.Metrics` para emitir métricas.
- **MFA** [E] — Autenticación multifactor.
- **Microservices** [A] — Servicios pequeños, desplegables de forma independiente, cada uno dueño de sus datos.
- **Microsoft.Identity.Web** [E][.NET] — Librería que integra ASP.NET Core con Entra ID.
- **Modular Monolith** [A] — Un solo despliegue organizado en módulos con fronteras estrictas.
- **MSAL** [E] — Microsoft Authentication Library: obtiene tokens de Entra.
- **mTLS (mutual TLS)** [R][E] — TLS en el que cliente y servidor presentan certificados.
- **MTU** [R] — Tamaño máximo de paquete en un enlace (~1500 bytes en Ethernet).

## N
- **NAT / SNAT** [R] — Traducción de direcciones privadas a públicas. *SNAT port exhaustion*: agotar los puertos de salida disponibles por no reutilizar conexiones.
- **NAT Gateway** [R] — Servicio de Azure para salida a internet con IPs estáticas y muchos puertos SNAT.
- **NetArchTest / ArchUnitNET** [G][.NET] — Librerías para escribir tests de reglas de arquitectura.
- **Network Watcher** [R] — Herramientas de diagnóstico de red de Azure (connection troubleshoot, IP flow verify, flow logs).
- **NSG (Network Security Group)** [R] — Firewall de capa 4 de Azure asociado a subnets o NICs (reglas por IP, puerto, protocolo).
- **NuGet Audit** [G][.NET] — Verificación de vulnerabilidades conocidas en paquetes durante `restore`.
- **Null Object** [P] — Objeto que implementa la interfaz sin hacer nada, evitando comprobaciones de `null`.

## O
- **OAuth 2.0** [E] — Protocolo de **autorización** delegada.
- **Observability** [O] — Capacidad de entender el estado interno de un sistema a partir de sus salidas (logs, métricas, trazas).
- **Observer** [P] — Un objeto notifica cambios a sus suscriptores.
- **OIDC (OpenID Connect)** [E] — Capa de **autenticación** sobre OAuth 2.0.
- **On-Behalf-Of (OBO)** [E] — Flujo donde una API llama a otra API en nombre del usuario original.
- **Open/Closed Principle (OCP)** [P] — Abierto a extensión, cerrado a modificación.
- **OpenTelemetry (OTel)** [O] — Estándar abierto y vendor-neutral para telemetría.
- **Orchestration** [A] — Coordinación de un proceso por un componente central.
- **OSI model** [R] — Modelo de 7 capas para describir la comunicación en redes (física → aplicación).
- **OTLP** [O] — Protocolo de exportación de OpenTelemetry.
- **Outbox pattern** [A] — Guardar el evento a publicar en la misma transacción que los datos; un proceso aparte lo publica.

## P
- **Pagination (offset / cursor)** [A] — Dividir resultados en páginas. Cursor (keyset) escala mejor que offset.
- **Partitioning / Sharding** [A] — Dividir datos en particiones para escalar.
- **Peering (VNet peering)** [R] — Conexión privada entre dos VNets de Azure.
- **PIM (Privileged Identity Management)** [E] — Acceso privilegiado *just-in-time* y con aprobación.
- **Pipeline (YAML)** [C] — Definición como código de los pasos de build y despliegue.
- **Polly** [A][.NET] — Librería de resiliencia (retry, circuit breaker, timeout, hedging).
- **Port (puerto)** [R] — Número (0–65535) que identifica un servicio en un host. Efímeros: los que usa el cliente para salir.
- **Primitive Obsession** [P] — Antipatrón: usar `string`/`decimal` donde debería haber un tipo (`Email`, `Money`).
- **Principle of Least Privilege** [E][G] — Conceder solo los permisos mínimos necesarios.
- **Private DNS Zone** [R] — Zona DNS privada de Azure (ej. `privatelink.database.windows.net`) que resuelve servicios a IPs privadas.
- **Private Endpoint / Private Link** [R] — Interfaz con IP privada de tu VNet para acceder a un servicio PaaS sin exponerlo a internet.
- **Proxy** [P] — Sustituto que controla el acceso a otro objeto.

## Q
- **Query** [A] — En CQRS, operación que lee sin cambiar estado.
- **Queue-based load leveling** [A] — Usar una cola para absorber picos de carga.
- **QUIC** [R] — Protocolo de transporte sobre UDP con TLS integrado; base de HTTP/3.

## R
- **Rate limiting** [A] — Limitar cuántas peticiones acepta un sistema por unidad de tiempo.
- **Redirect URI** [E] — URL a la que Entra devuelve al usuario tras autenticarse.
- **Refresh token** [E] — Token de larga duración para obtener nuevos access tokens.
- **Repository** [P] — Abstracción tipo colección para acceder a aggregates.
- **Resilience** [A] — Capacidad de recuperarse de fallos y seguir funcionando.
- **Result pattern** [P] — Devolver éxito/fallo explícito en lugar de lanzar excepciones para errores esperados.
- **Retry with exponential backoff + jitter** [A] — Reintentar con esperas crecientes y aleatorizadas.
- **Rolling deployment** [C] — Actualizar instancias por lotes.
- **RTT (Round-Trip Time)** [R] — Tiempo de ida y vuelta de un paquete entre dos puntos.

## S
- **Saga** [A] — Secuencia de transacciones locales con acciones compensatorias para procesos distribuidos.
- **Sampling** [O] — Enviar solo una fracción de las trazas para controlar costos.
- **Scope (`scp`)** [E] — Permiso delegado expuesto por una API (ej. `Orders.Read`).
- **Service connection** [C] — Credencial configurada en Azure DevOps para conectarse a servicios externos (Azure, Docker…).
- **Service Endpoint** [R] — Extiende la identidad de una subnet hacia un servicio PaaS por el backbone de Azure; el servicio conserva IP pública.
- **Service Principal** [E] — Instancia de una aplicación en un tenant; es la identidad que recibe permisos.
- **Service tag** [R] — Nombre que representa los rangos IP de un servicio de Azure (ej. `AzureMonitor`) para usar en reglas NSG.
- **Single Responsibility Principle (SRP)** [P] — Una clase debe tener una sola razón para cambiar.
- **Singleton** [P] — Garantizar una sola instancia. En .NET se prefiere el lifetime `Singleton` de DI.
- **SLA / SLO / SLI** [O] — *Agreement* (contrato), *Objective* (meta interna), *Indicator* (la medición).
- **SNI** [R] — Extensión TLS donde el cliente indica el hostname, permitiendo varios certificados en una misma IP.
- **Socket exhaustion** [R][.NET] — Agotar puertos/sockets locales por crear y desechar conexiones (ej. `new HttpClient()` por petición).
- **Span** [O] — Unidad de trabajo dentro de una traza (con inicio, fin y atributos).
- **Specification** [P] — Encapsular una regla/criterio de consulta reutilizable.
- **Stage / Job / Step / Task** [C] — Jerarquía de Azure Pipelines: stages contienen jobs, jobs contienen steps; una task es un step predefinido.
- **State** [P] — El objeto cambia su comportamiento según su estado interno.
- **Stateless** [A] — El servicio no guarda estado de sesión en memoria local; cualquier instancia puede atender cualquier petición.
- **Strangler Fig** [A] — Migrar un sistema legado reemplazándolo pieza a pieza.
- **Strategy** [P] — Familia de algoritmos intercambiables.
- **Structured logging** [O] — Logs con campos con nombre (no solo texto), consultables.
- **Subnet** [R] — Segmento de una red IP (en Azure, segmento de una VNet).

## T
- **TCP / UDP** [R] — TCP: transporte confiable, ordenado y orientado a conexión. UDP: sin conexión, sin garantías, mínimo overhead.
- **Technical debt** [G] — Costo futuro de atajos tomados hoy.
- **Template (pipeline)** [C] — Fragmento YAML reutilizable (stages, jobs, steps o variables).
- **Template Method** [P] — Esqueleto de un algoritmo en una clase base con pasos que las subclases redefinen.
- **Tenant** [E] — Instancia dedicada de Entra ID de una organización.
- **Throttling** [A] — Rechazar o ralentizar peticiones cuando se supera un límite.
- **TIME_WAIT** [R] — Estado en que queda un socket TCP tras cerrarse, ocupando el puerto durante un tiempo.
- **TLS** [R][E] — Protocolo que cifra y autentica comunicaciones (la «S» de HTTPS).
- **Trace** [O] — Árbol de spans que representa una petición de extremo a extremo.
- **Trunk-based development** [C] — Ramas de vida corta que se integran frecuentemente a `main`.
- **TTL (DNS)** [R] — Tiempo que una respuesta DNS puede cachearse.
- **Twelve-Factor App** [A] — Doce principios para apps cloud-native (config en entorno, procesos stateless…).

## U
- **Ubiquitous Language** [A] — Lenguaje común entre negocio y desarrollo dentro de un bounded context.
- **UDR (User Defined Route)** [R] — Ruta personalizada en Azure, típicamente para forzar el tráfico a través de un firewall.
- **Unit of Work** [P] — Agrupar cambios y confirmarlos en una sola transacción (`DbContext` ya lo es).

## V
- **Value Object** [A] — Objeto definido por sus valores, inmutable y sin identidad (ej. `Money`).
- **Variable group** [C] — Conjunto de variables compartidas entre pipelines; puede vincularse a Key Vault.
- **Vertical scaling (scale up)** [A] — Dar más recursos a la misma máquina.
- **Vertical Slice Architecture** [A] — Organizar el código por funcionalidad (feature) en lugar de por capa técnica.
- **VNet (Virtual Network)** [R] — Red privada aislada en Azure.
- **VNet Integration** [R] — Permite que App Service/Functions envíen tráfico **saliente** hacia una VNet.
- **VPN (Site-to-Site / Point-to-Site)** [R] — Túnel cifrado sobre internet entre redes, o entre un equipo y una red.

## W
- **WAF (Web Application Firewall)** [R] — Firewall de capa 7 que filtra ataques web (OWASP Top 10). Disponible en Front Door y Application Gateway.
- **WebSockets** [R] — Canal bidireccional persistente sobre una conexión HTTP actualizada (SignalR).
- **Workload Identity Federation (WIF)** [E][C] — Usar federated credentials (OIDC) para que Azure DevOps/GitHub se autentiquen en Azure sin secretos.
- **Workload Identity** [E] — Identidad de software (apps, service principals, managed identities) en contraste con identidades humanas.

## Y
- **YAGNI** [P] — *You Aren't Gonna Need It*: no construyas lo que aún no necesitas.

## Z
- **Zero Trust** [E] — Modelo de seguridad: "nunca confíes, siempre verifica"; asume brecha y aplica mínimo privilegio.
- **Zero-downtime deployment** [C] — Desplegar sin interrumpir el servicio.
