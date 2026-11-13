# 05.3 · Servidor MCP en Node.js (TypeScript)

## Objetivos

- Crear el servidor "tareas" con el **SDK oficial de TypeScript v2** (`@modelcontextprotocol/server`).
- Registrar tools con Zod (entrada y salida estructurada), resources y prompts.
- Servirlo por stdio y por Streamable HTTP (Node `http`) con validación de Host/Origin.
- Probarlo con MCP Inspector y con Vitest.

---

## 1. v1 vs v2 (léelo antes de copiar tutoriales)

| | v1 (mantenimiento) | **v2 (actual)** |
|---|---|---|
| Paquetes | `@modelcontextprotocol/sdk` (uno solo) | `@modelcontextprotocol/server`, `@modelcontextprotocol/client` + adaptadores (`/node`, `/express`, `/hono`, `/fastify`) |
| Importar servidor | `@modelcontextprotocol/sdk/server/mcp.js` | `@modelcontextprotocol/server` |
| Registrar tool | `server.tool(...)` / `registerTool` con *raw shape* | `server.registerTool(name, config, handler)` con `inputSchema: z.object(...)` |
| stdio | `new StdioServerTransport()` + `connect` | `serveStdio(() => server)` desde `@modelcontextprotocol/server/stdio` |
| Requisitos | Node 18+ | **Node 20+**, **solo ESM**, **Zod v4** (`zod/v4`) |
| Spec | hasta 2025-11-25 | 2026-07-28 (y compatibilidad con anteriores) |

---

## 2. Preparar el proyecto

```bash
mkdir mcp-tareas-node && cd mcp-tareas-node
npm init -y
npm pkg set type=module
npm install @modelcontextprotocol/server @modelcontextprotocol/node zod
npm install -D typescript tsx @types/node vitest @modelcontextprotocol/client
mkdir src tests
```

`tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "outDir": "dist",
    "rootDir": "src",
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

Scripts en `package.json`:
```json
{
  "scripts": {
    "dev": "tsx src/stdio.ts",
    "http": "tsx src/http.ts",
    "build": "tsc",
    "inspect": "npx @modelcontextprotocol/inspector npx tsx src/stdio.ts",
    "test": "vitest run"
  }
}
```

Estructura:
```
src/
├── almacen.ts     ← lógica de negocio
├── servidor.ts    ← createServer(): define tools/resources/prompts
├── stdio.ts       ← punto de entrada stdio
└── http.ts        ← punto de entrada Streamable HTTP
tests/
└── servidor.test.ts
```

---

## 3. Lógica de negocio

`src/almacen.ts`
```ts
import { existsSync, readFileSync, writeFileSync } from 'node:fs';

export type Prioridad = 'alta' | 'media' | 'baja';

export interface Tarea {
    id: number;
    titulo: string;
    prioridad: Prioridad;
    completada: boolean;
    creada: string;
}

export class Almacen {
    constructor(private readonly ruta: string) {
        if (!existsSync(ruta)) writeFileSync(ruta, '[]', 'utf-8');
    }

    private leer(): Tarea[] {
        return JSON.parse(readFileSync(this.ruta, 'utf-8')) as Tarea[];
    }

    private guardar(tareas: Tarea[]): void {
        writeFileSync(this.ruta, JSON.stringify(tareas, null, 2), 'utf-8');
    }

    agregar(titulo: string, prioridad: Prioridad = 'media'): Tarea {
        const tareas = this.leer();
        const nueva: Tarea = {
            id: Math.max(0, ...tareas.map(t => t.id)) + 1,
            titulo: titulo.trim(),
            prioridad,
            completada: false,
            creada: new Date().toISOString()
        };
        tareas.push(nueva);
        this.guardar(tareas);
        return nueva;
    }

    listar(soloPendientes = false): Tarea[] {
        const tareas = this.leer();
        return soloPendientes ? tareas.filter(t => !t.completada) : tareas;
    }

    obtener(id: number): Tarea | undefined {
        return this.leer().find(t => t.id === id);
    }

    completar(id: number): Tarea | undefined {
        const tareas = this.leer();
        const tarea = tareas.find(t => t.id === id);
        if (!tarea) return undefined;
        tarea.completada = true;
        this.guardar(tareas);
        return tarea;
    }
}
```

---

## 4. Definición del servidor

`src/servidor.ts`
```ts
import { McpServer, ResourceTemplate } from '@modelcontextprotocol/server';
import * as z from 'zod/v4';
import { Almacen } from './almacen.js';

const PrioridadSchema = z.enum(['alta', 'media', 'baja']);

const TareaSchema = z.object({
    id: z.number(),
    titulo: z.string(),
    prioridad: PrioridadSchema,
    completada: z.boolean(),
    creada: z.string()
});

export function createServer(rutaDatos = process.env.TAREAS_ARCHIVO ?? 'tareas.json'): McpServer {
    const almacen = new Almacen(rutaDatos);
    const server = new McpServer({ name: 'tareas', version: '1.0.0' });

    // ───────────── TOOLS ─────────────
    server.registerTool(
        'agregar_tarea',
        {
            title: 'Agregar tarea',
            description:
                'Crea una tarea nueva. Úsala cuando el usuario quiera apuntar, añadir o crear un pendiente.',
            inputSchema: z.object({
                titulo: z.string().min(1).max(200).describe('Texto corto de la tarea'),
                prioridad: PrioridadSchema.default('media').describe('alta | media | baja')
            }),
            outputSchema: TareaSchema
        },
        async ({ titulo, prioridad }) => {
            const tarea = almacen.agregar(titulo, prioridad);
            console.error(`[tareas] creada #${tarea.id}`); // stderr, nunca stdout
            return {
                content: [{ type: 'text', text: `Tarea #${tarea.id} creada: ${tarea.titulo}` }],
                structuredContent: tarea
            };
        }
    );

    server.registerTool(
        'listar_tareas',
        {
            title: 'Listar tareas',
            description: 'Lista las tareas (por defecto solo pendientes). Úsala para consultar el estado.',
            inputSchema: z.object({
                solo_pendientes: z.boolean().default(true)
            }),
            outputSchema: z.object({ total: z.number(), tareas: z.array(TareaSchema) }),
            annotations: { readOnlyHint: true }
        },
        async ({ solo_pendientes }) => {
            const tareas = almacen.listar(solo_pendientes);
            const texto = tareas.map(t => `#${t.id} [${t.prioridad}] ${t.titulo}`).join('\n') || 'Sin tareas.';
            return {
                content: [{ type: 'text', text: texto }],
                structuredContent: { total: tareas.length, tareas }
            };
        }
    );

    server.registerTool(
        'completar_tarea',
        {
            title: 'Completar tarea',
            description: 'Marca una tarea como completada por su id. Si no conoces el id, usa antes listar_tareas.',
            inputSchema: z.object({ tarea_id: z.number().int().positive() })
        },
        async ({ tarea_id }) => {
            const tarea = almacen.completar(tarea_id);
            if (!tarea) {
                return {
                    content: [{ type: 'text', text: `No existe la tarea ${tarea_id}. Usa listar_tareas.` }],
                    isError: true
                };
            }
            return { content: [{ type: 'text', text: `Tarea #${tarea.id} completada.` }] };
        }
    );

    // ─────────── RESOURCES ───────────
    server.registerResource(
        'pendientes',
        'tareas://pendientes',
        { title: 'Tareas pendientes', description: 'Lista legible de pendientes', mimeType: 'text/plain' },
        async uri => ({
            contents: [{
                uri: uri.href,
                text: almacen.listar(true).map(t => `- [${t.prioridad}] #${t.id} ${t.titulo}`).join('\n') || 'Nada pendiente.'
            }]
        })
    );

    server.registerResource(
        'tarea',
        new ResourceTemplate('tareas://{tareaId}', { list: undefined }),
        { title: 'Detalle de tarea', description: 'Una tarea en JSON', mimeType: 'application/json' },
        async (uri, { tareaId }) => ({
            contents: [{
                uri: uri.href,
                mimeType: 'application/json',
                text: JSON.stringify(almacen.obtener(Number(tareaId)) ?? null)
            }]
        })
    );

    // ──────────── PROMPTS ────────────
    // Nota: en v2 los argumentos del prompt se definen con Zod; consulta la página
    // "Prompts" de la doc v2 si tu versión espera otra forma.
    server.registerPrompt(
        'planificar_dia',
        {
            title: 'Planificar el día',
            description: 'Plan del día con las tareas pendientes',
            argsSchema: z.object({ horas: z.string().default('8') })
        },
        ({ horas }) => ({
            messages: [{
                role: 'user',
                content: {
                    type: 'text',
                    text: `Tengo ${horas} horas. Usa listar_tareas y propón un plan ordenado por prioridad con estimaciones.`
                }
            }]
        })
    );

    return server;
}
```

---

## 5. Punto de entrada stdio

`src/stdio.ts`
```ts
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import { createServer } from './servidor.js';

void serveStdio(() => createServer());
console.error('Servidor MCP "tareas" escuchando por stdio');
```

```bash
npm run dev       # se queda esperando: es normal
npm run inspect   # abre MCP Inspector
```

---

## 6. Punto de entrada Streamable HTTP

`src/http.ts`
```ts
import { createServer as createHttpServer } from 'node:http';
import { toNodeHandler, localhostHostValidation, localhostOriginValidation } from '@modelcontextprotocol/node';
import { createMcpHandler } from '@modelcontextprotocol/server';
import { createServer } from './servidor.js';

// Fábrica: el SDK v2 crea el servidor por petición (modelo stateless de 2026-07-28)
const handler = createMcpHandler(() => createServer());
const nodeHandler = toNodeHandler(handler);

// Protección contra DNS rebinding: valida Host y Origin
const validateHost = localhostHostValidation();
const validateOrigin = localhostOriginValidation();

const httpServer = createHttpServer((req, res) => {
    if (!validateHost(req, res) || !validateOrigin(req, res)) return;
    void nodeHandler(req, res);
}).listen(3000, '127.0.0.1', () => {
    console.error('MCP "tareas" en http://127.0.0.1:3000/mcp');
});

process.on('SIGINT', async () => {
    await handler.close();
    httpServer.close();
    process.exit(0);
});
```

```bash
npm run http
npx @modelcontextprotocol/inspector   # conecta con "Streamable HTTP" a http://127.0.0.1:3000/mcp
```

> El handler **no** autentica. En producción añade autenticación (OAuth o tokens) delante, TLS y límites de tasa. También hay adaptadores para **Express**, **Hono**, **Fastify** y runtimes *web-standard* (Workers, Deno, Bun).

---

## 7. Conectar a clientes

```bash
# Claude Code, stdio
claude mcp add tareas-node -- npx tsx /ruta/absoluta/mcp-tareas-node/src/stdio.ts

# Claude Code, HTTP
claude mcp add --transport http tareas-http http://127.0.0.1:3000/mcp
```
```jsonc
// OpenCode
{
  "mcp": {
    "servers": {
      "tareas-node": { "type": "local", "command": ["npx", "tsx", "/ruta/absoluta/mcp-tareas-node/src/stdio.ts"] },
      "tareas-http": { "type": "remote", "url": "http://127.0.0.1:3000/mcp", "oauth": false }
    }
  }
}
```

Para distribuirlo por npm: compila (`npm run build`), añade `"bin": { "mcp-tareas": "dist/stdio.js" }` con `#!/usr/bin/env node` al inicio del archivo, y los usuarios lo ejecutarán con `npx -y mcp-tareas`.

---

## 8. Tests con Vitest (cliente real)

`tests/servidor.test.ts`
```ts
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

describe('servidor MCP tareas', () => {
    const client = new Client({ name: 'test', version: '1.0.0' });

    beforeAll(async () => {
        const dir = mkdtempSync(join(tmpdir(), 'tareas-'));
        const transport = new StdioClientTransport({
            command: 'npx',
            args: ['tsx', 'src/stdio.ts'],
            env: { ...process.env, TAREAS_ARCHIVO: join(dir, 't.json') } as Record<string, string>
        });
        await client.connect(transport);
    }, 30_000);

    afterAll(async () => { await client.close(); });

    it('expone las tools esperadas', async () => {
        const { tools } = await client.listTools();
        expect(tools.map(t => t.name)).toEqual(
            expect.arrayContaining(['agregar_tarea', 'listar_tareas', 'completar_tarea'])
        );
    });

    it('crea y lista una tarea', async () => {
        const r = await client.callTool({ name: 'agregar_tarea', arguments: { titulo: 'Test', prioridad: 'alta' } });
        expect(r.isError).toBeFalsy();
        expect(r.structuredContent).toMatchObject({ titulo: 'Test', prioridad: 'alta' });
    });

    it('devuelve isError para ids inexistentes', async () => {
        const r = await client.callTool({ name: 'completar_tarea', arguments: { tarea_id: 999 } });
        expect(r.isError).toBe(true);
    });

    it('rechaza argumentos inválidos', async () => {
        const r = await client.callTool({ name: 'agregar_tarea', arguments: { titulo: '' } }).catch(e => e);
        // El SDK valida contra el schema antes de llamar al handler
        expect(r instanceof Error || r.isError).toBe(true);
    });
});
```
```bash
npm test
```

---

## Errores comunes

- `console.log` en el servidor stdio (usa `console.error`).
- Olvidar `"type": "module"` → errores de importación (el SDK v2 es solo ESM).
- Importar `zod` v3 en lugar de `zod/v4`.
- Copiar código v1 (`@modelcontextprotocol/sdk/...`) en un proyecto v2.
- Exponer el servidor HTTP en `0.0.0.0` sin autenticación ni validación de Host/Origin.

## Ejercicios

1. Implementa el servidor y pruébalo en Inspector por stdio y por HTTP.
2. Añade una tool `buscar_tareas(texto)` con `annotations: { readOnlyHint: true }` y su test.
3. Despliega la versión HTTP en un contenedor Docker y conéctala desde Claude Code con `--transport http`.
4. Conecta a la vez el servidor Python (05.2) y el Node; pide al agente que compare ambos listados.
   - ✅ Éxito: el agente usa tools de los dos servidores en la misma conversación.

## Checklist

- [ ] Uso el SDK v2 (`@modelcontextprotocol/server`).
- [ ] Defino entrada y salida con Zod v4.
- [ ] Sirvo por stdio y por HTTP con validación de Host/Origin.
- [ ] Tengo tests de integración con un cliente real.

---

⬅️ [05.2](02-mcp-servidor-python.md) · ➡️ [05.4 · Servidor MCP en C#](04-mcp-servidor-csharp.md)
