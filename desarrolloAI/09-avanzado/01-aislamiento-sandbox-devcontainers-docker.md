# 09.1 · Aislamiento serio: sandbox, Dev Containers y Docker Sandboxes

## Objetivos

- Entender por qué los permisos no bastan cuando das autonomía real a un agente.
- Configurar el **sandbox de Bash** de Claude Code (sistema de archivos, red y credenciales).
- Ejecutar agentes dentro de **Dev Containers** con firewall de salida y políticas gestionadas.
- Usar **Docker Sandboxes** (microVM) para agentes sin supervisión.
- Elegir el nivel de aislamiento adecuado, también en **Windows**.

> Prerrequisito: [02.2 · Seguridad y buenas prácticas](../02-flujos-de-trabajo/02-seguridad-y-buenas-practicas.md).

---

## 1. Por qué hace falta aislamiento "de verdad"

Los **permisos** (allow/ask/deny) y las **instrucciones** se aplican dentro del propio agente. Si un comando permitido (por ejemplo `npm test`) ejecuta un script malicioso de una dependencia, ese script corre con **tus** privilegios: lee `~/.ssh`, tus tokens y puede enviar datos fuera.

El aislamiento añade una **frontera impuesta por el sistema operativo, el contenedor o una VM** que no depende de que el modelo "se porte bien".

```
Más autonomía ─────────────────────────────────────────────────────► Más aislamiento
 default/ask      accept edits      auto mode      sandbox Bash     Dev Container     microVM / VM / nube
 (preguntas)      (rama propia)     (clasificador) (SO limita FS    (contenedor +     (kernel propio,
                                                    y red)           firewall)         desechable)
```

**Regla:** si vas a usar `--dangerously-skip-permissions` (o el equivalente), hazlo **solo** dentro de un contenedor, microVM o VM desechable, sin credenciales de producción y con la red restringida.

---

## 2. Nivel 1 · Sandbox de Bash de Claude Code

### 2.1 Qué es
Una frontera impuesta por el sistema operativo alrededor de los comandos de shell que ejecuta Claude (Bash, PowerShell, Monitor) y de los procesos que lanzan. Como el SO impone los límites, Claude puede ejecutar comandos dentro del sandbox **sin pedirte aprobación uno a uno**. Está **desactivado por defecto**.

| Sistema | Tecnología | Notas |
|---|---|---|
| macOS | Seatbelt (incluido en el SO) | Funciona sin instalar nada |
| Linux / **WSL2** | `bubblewrap` + `socat` | `sudo apt-get install bubblewrap socat` |
| **Windows nativo** | — | **No hay sandbox**: usa WSL2 |

### 2.2 Activarlo
```text
/sandbox
```
O en un archivo de settings:
```json
{ "sandbox": { "enabled": true } }
```
O solo para una sesión:
```bash
claude --settings '{"sandbox": {"enabled": true, "allowUnsandboxedCommands": false}}'
```

### 2.3 Sistema de archivos
- **Escritura** permitida por defecto en el directorio de trabajo, un temporal por usuario y los directorios añadidos. Rutas protegidas como los settings de `.claude`, los hooks, `.mcp.json` y los archivos de arranque del shell siguen sin poder escribirse.
- **Lectura** permitida en casi toda la máquina por defecto, **incluidos `~/.ssh` y `~/.aws/credentials`**. Restríngelo:

```json
{
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "denyRead": ["~/"],
      "allowRead": ["."],
      "allowWrite": ["/tmp/build"]
    }
  }
}
```

### 2.4 Red
Los comandos del sandbox **no tienen ruta directa a la red**: el tráfico pasa por un proxy local que compara cada dominio con `allowedDomains` (vacío al inicio). Las herramientas que ignoran el proxy (ssh plano, muchos drivers de bases de datos) no podrán conectar.

```json
{
  "sandbox": {
    "enabled": true,
    "network": {
      "allowedDomains": ["github.com", "*.npmjs.org", "pypi.org", "files.pythonhosted.org", "api.nuget.org"]
    },
    "excludedCommands": ["docker compose *"]
  }
}
```

### 2.5 Credenciales
```json
{
  "sandbox": {
    "enabled": true,
    "credentials": {
      "files": [
        { "path": "~/.aws/credentials", "mode": "deny" },
        { "path": "~/.ssh", "mode": "deny" }
      ],
      "envVars": [
        { "name": "GITHUB_TOKEN", "mode": "deny" },
        { "name": "NPM_TOKEN", "mode": "deny" }
      ]
    }
  }
}
```
También existe el modo *mask*, en el que el proxy sustituye el valor real solo hacia hosts permitidos (requiere configuración adicional; consulta la documentación).

### 2.6 Configuración estricta (sin escapes)
```json
{
  "sandbox": {
    "enabled": true,
    "failIfUnavailable": true,
    "allowUnsandboxedCommands": false
  }
}
```
- `allowUnsandboxedCommands: false` impide que Claude reintente fuera del sandbox cuando un comando falla.
- `failIfUnavailable: true` evita que se ejecuten comandos sin sandbox si este no puede arrancar.
- Una organización puede imponerlo vía *managed settings*.

### 2.7 Limitaciones (importante)
- Las herramientas de archivos de Claude, los **servidores MCP**, los **hooks** y **WebFetch** se ejecutan **fuera** del sandbox (se rigen por permisos).
- `excludedCommands` corre con acceso total: no es una frontera de seguridad.
- El proxy por defecto no inspecciona TLS; el sandbox no cubre UDP/ICMP.
- Los comandos que escribes con `!` normalmente se ejecutan fuera del sandbox.

> Conclusión: el sandbox es excelente para **trabajo diario con menos interrupciones**, pero para autonomía total usa contenedor o microVM.

---

## 3. Nivel 2 · Dev Containers

Un **Dev Container** define un entorno idéntico y aislado (Docker) para todo el equipo. Los comandos de Claude se ejecutan **dentro del contenedor**; tus archivos del proyecto se montan y los cambios aparecen en tu repo local. Funciona con VS Code, GitHub Codespaces, IDEs JetBrains, etc.

### 3.1 Añadir Claude Code a un Dev Container
`.devcontainer/devcontainer.json`
```json
{
  "name": "taskflow",
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
  "features": {
    "ghcr.io/devcontainers/features/node:1": {},
    "ghcr.io/devcontainers/features/python:1": {},
    "ghcr.io/devcontainers/features/dotnet:2": {},
    "ghcr.io/anthropics/devcontainer-features/claude-code:1.0": {}
  },
  "remoteUser": "vscode",
  "mounts": [
    "source=claude-code-config-${devcontainerId},target=/home/vscode/.claude,type=volume"
  ],
  "containerEnv": {
    "CLAUDE_CONFIG_DIR": "/home/vscode/.claude"
  },
  "postCreateCommand": "npm ci && npx playwright install --with-deps chromium"
}
```
Luego: **Dev Containers: Rebuild Container** y ejecuta `claude` en la terminal del contenedor.

- El volumen + `CLAUDE_CONFIG_DIR` conserva la autenticación y la configuración entre reconstrucciones.
- Los servidores MCP del proyecto se definen en `.mcp.json` (y sus binarios se instalan en la imagen).

### 3.2 OpenCode en el mismo contenedor
Añade la instalación de OpenCode al `postCreateCommand` o a un `Dockerfile` (consulta el método de instalación actual en su documentación) y pasa las claves de proveedor como variables de entorno o secretos de Codespaces, **no** montando archivos de credenciales del host.

### 3.3 Restringir la salida de red (firewall)
El contenedor de referencia de Anthropic incluye un script `init-firewall.sh` que limita el tráfico saliente a los destinos permitidos; necesita las capacidades `NET_ADMIN` y `NET_RAW`:
```json
{
  "runArgs": ["--cap-add=NET_ADMIN", "--cap-add=NET_RAW"],
  "postStartCommand": "sudo /usr/local/bin/init-firewall.sh"
}
```
Úsalo como ejemplo (repo `anthropics/claude-code`, carpeta `.devcontainer/`) y adapta la lista de dominios: API del modelo, GitHub, registros de paquetes y nada más.

### 3.4 Políticas de equipo
Claude Code lee `/etc/claude-code/managed-settings.json` en Linux con la máxima prioridad:
```dockerfile
RUN mkdir -p /etc/claude-code
COPY managed-settings.json /etc/claude-code/managed-settings.json
```
```json
{
  "permissions": {
    "deny": ["Read(./.env*)", "Bash(git push --force:*)"],
    "disableBypassPermissionsMode": "disable"
  },
  "sandbox": { "enabled": true, "failIfUnavailable": true }
}
```
> Cualquiera con acceso de escritura al repo puede cambiar el Dockerfile. Para políticas que no se puedan saltar, usa *server-managed settings* o tu MDM.

### 3.5 Modo sin preguntas dentro del contenedor
Como el contenedor ejecuta Claude con un usuario **no root** y confina los comandos, puedes usar:
```bash
claude --dangerously-skip-permissions
```
(La CLI rechaza este flag si se ejecuta como root.) Aun así: Claude puede modificar todo lo montado del workspace y alcanzar lo que permita la red. Combínalo **siempre** con el firewall. Si prefieres menos preguntas sin desactivar controles, usa *auto mode*.

### 3.6 Advertencias
- Un proyecto malicioso con `--dangerously-skip-permissions` puede exfiltrar todo lo accesible dentro del contenedor, **incluidas las credenciales de Claude** en `~/.claude`.
- No montes `~/.ssh` ni archivos de credenciales cloud; usa tokens de corta duración y con alcance de repositorio.
- Úsalo solo con repositorios de confianza y monitoriza la actividad (ver [09.2](02-evaluacion-y-observabilidad.md)).

---

## 4. Nivel 3 · Docker Sandboxes (microVM)

Un contenedor normal **comparte el kernel** del host, y montar `/var/run/docker.sock` para que el agente use Docker le entrega toda la máquina. **Docker Sandboxes** ejecuta cada agente en una **microVM con su propio kernel y su propio Docker Engine**, compartiendo solo el directorio del proyecto.

Características:
- Soporta Claude Code, Codex, Copilot CLI, Gemini CLI, **OpenCode**, Kiro y más.
- El agente puede construir y ejecutar contenedores **dentro** de la microVM sin acceso al Docker del host.
- Las claves de API pueden quedarse en el host e inyectarse vía proxy (no aparecen dentro).
- Presets de red: abierto, equilibrado (deny por defecto + sitios de desarrollo comunes) o bloqueado.
- Se destruye y recrea en segundos: si el agente rompe algo, el host no se entera.

### Uso básico (CLI `sbx`)
```bash
cd ~/mi-proyecto
sbx run claude            # o: sbx run opencode / codex / copilot ...
# Con suscripción de Claude: escribe /login dentro de Claude Code la primera vez
```
Modo "clon" (el agente trabaja sobre una copia privada del repo, no sobre tu carpeta):
```bash
sbx run --clone --name proyecto-claude claude ~/ruta/al/proyecto
```
> Requisitos y comandos cambian rápido: la versión microVM requiere macOS o Windows (experimental en Windows) y existía una integración antigua `docker sandbox run` en Docker Desktop, ya deprecada. Verifica en `docs.docker.com/ai/sandboxes/`.

### Flujo recomendado para trabajo autónomo
1. Rama nueva + `sbx run --clone ... claude`.
2. Dentro: modo autónomo con una tarea bien especificada (idealmente una spec OpenSpec).
3. El agente hace commits en su clon.
4. Tú revisas el diff/PR desde fuera y decides el merge.
5. Destruyes el sandbox.

---

## 5. Otras opciones

| Opción | Cuándo |
|---|---|
| **GitHub Codespaces** | Dev Container en la nube; nada toca tu PC |
| **Agentes en la nube** (Claude Code en la web, agentes en CI) | Tareas asíncronas en entornos gestionados |
| **VM local** (Hyper-V, VirtualBox, UTM) | Máximo control, más pesado |
| **Runner de CI efímero** | Agentes headless con permisos mínimos y secretos acotados |

---

## 6. Windows: recomendaciones concretas

1. **WSL2** como base del trabajo agéntico: tendrás el sandbox de Bash (bubblewrap) y compatibilidad con los hooks POSIX.
2. **Docker Desktop + Dev Containers** con el backend WSL2.
3. **Docker Sandboxes** si tu versión de Windows está soportada.
4. Evita trabajar con autonomía alta en Windows nativo: no hay sandbox de shell.
5. Guarda los repos dentro del sistema de archivos de WSL (`~/proyectos`) para mejor rendimiento.

---

## 7. Matriz de decisión

| Situación | Aislamiento mínimo recomendado |
|---|---|
| Aprender / explorar un repo, con supervisión | Permisos + rama |
| Trabajo diario con menos interrupciones | **Sandbox de Bash** + permisos |
| Equipo que quiere entornos idénticos | **Dev Container** |
| Agente sin supervisión en tu máquina | **Dev Container con firewall** o **Docker Sandbox** |
| Repos o dependencias no confiables | **Docker Sandbox / VM**, red bloqueada |
| Automatización en CI | Runner efímero + tokens de corta duración |

---

## Errores comunes

- Creer que el sandbox de Bash protege a los servidores MCP o hooks (no lo hace).
- Montar `~/.ssh`, `~/.aws` o el socket de Docker dentro del contenedor.
- Usar `--dangerously-skip-permissions` como root o en el host.
- `allowedDomains` con `*` "para que funcione".
- No persistir `~/.claude` → iniciar sesión en cada reconstrucción.

## Ejercicios

1. Activa el sandbox con `denyRead: ["~/"]` y `allowRead: ["."]`. Pide a Claude que lea `~/.ssh` (sin claves reales) y verifica el bloqueo.
2. Configura `allowedDomains` mínimo y comprueba que `npm install` funciona pero `curl https://example.com` no.
3. Crea un Dev Container para el proyecto TaskFlow con Claude Code, Node, Python y .NET, con el volumen persistente.
   - ✅ Éxito: reconstruyes el contenedor y no tienes que volver a iniciar sesión.
4. Añade el firewall de referencia y ejecuta una tarea en modo autónomo dentro del contenedor.
5. (Si tu sistema lo soporta) ejecuta la misma tarea con `sbx run --clone ... claude` y compara.

## Checklist

- [ ] Entiendo la diferencia entre permisos, sandbox, contenedor y microVM.
- [ ] Configuré el sandbox de Bash (FS, red, credenciales).
- [ ] Tengo un Dev Container con configuración persistente y red restringida.
- [ ] Sé cuándo usar Docker Sandboxes o una VM.
- [ ] Nunca uso modo autónomo sin aislamiento.

---

⬅️ [08 · Proyecto integrador](../08-proyecto-integrador/01-proyecto-integrador.md) · ➡️ [09.2 · Evaluación y observabilidad](02-evaluacion-y-observabilidad.md)
