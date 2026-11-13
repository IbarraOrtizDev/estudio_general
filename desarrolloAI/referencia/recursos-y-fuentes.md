# Recursos y fuentes oficiales

Verificados en noviembre de 2026. Ante cualquier discrepancia, **la documentación oficial manda**.

## Claude Code
- Documentación: https://code.claude.com/docs
  - Skills: https://code.claude.com/docs/en/skills
  - Subagentes: https://code.claude.com/docs/en/sub-agents
  - Hooks: https://code.claude.com/docs/en/hooks
- Changelog: https://github.com/anthropics/claude-code/releases
- Documentación de la API de Claude y Agent SDK: https://docs.claude.com

## OpenCode
- Documentación: https://opencode.ai/docs
  - Agentes: https://opencode.ai/docs/agents/
  - Skills: https://opencode.ai/docs/skills/
  - Comandos: https://opencode.ai/docs/commands/
  - Permisos: https://opencode.ai/docs/permissions/
  - MCP: https://opencode.ai/docs/mcp-servers
  - Migrar de V1: https://opencode.ai/docs/migrate-v1/
- Esquema de configuración: https://opencode.ai/config.json

## Aislamiento, evaluación, observabilidad, RAG y memoria
- Sandbox de Claude Code: https://code.claude.com/docs/en/sandboxing
- Dev Containers con Claude Code: https://code.claude.com/docs/en/devcontainer
- Monitorización con OpenTelemetry: https://code.claude.com/docs/en/monitoring-usage
- Memoria de Claude Code: https://code.claude.com/docs/en/memory
- Memory tool (API de Claude): https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
- Docker Sandboxes: https://docs.docker.com/ai/sandboxes/
- Especificación Dev Containers: https://containers.dev
- promptfoo: https://www.promptfoo.dev · Langfuse: https://langfuse.com · OpenTelemetry: https://opentelemetry.io
- Chroma: https://docs.trychroma.com · Ragas: https://docs.ragas.io

## AGENTS.md
- Estándar abierto: https://agents.md

## Model Context Protocol
- Sitio y especificación: https://modelcontextprotocol.io (spec actual: `/specification/2026-07-28`)
- Blog oficial (novedades de la spec y SDKs): https://blog.modelcontextprotocol.io
- SDK Python (v2): https://py.sdk.modelcontextprotocol.io · repo `modelcontextprotocol/python-sdk`
- SDK TypeScript (v2): https://ts.sdk.modelcontextprotocol.io/v2/ · repo `modelcontextprotocol/typescript-sdk`
- SDK C#: repo `modelcontextprotocol/csharp-sdk` · NuGet `ModelContextProtocol`
  - Anuncio v2.0: https://devblogs.microsoft.com/dotnet/announcing-v20-of-the-official-mcp-csharp-sdk/
- MCP Inspector: `npx @modelcontextprotocol/inspector`
- Playwright MCP: repo `microsoft/playwright-mcp`

## OpenSpec
- Sitio y docs: https://openspec.dev/docs/getting-started
- Repositorio: https://github.com/Fission-AI/OpenSpec
- Cómo funcionan los comandos: https://openspec.dev/docs/how-commands-work

## Playwright
- Documentación: https://playwright.dev/docs/intro
- Test Agents: https://playwright.dev/docs/test-agents
- Localizadores: https://playwright.dev/docs/locators
- Buenas prácticas: https://playwright.dev/docs/best-practices
- Python: https://playwright.dev/python/ · .NET: https://playwright.dev/dotnet/

## Testing
- Vitest (incl. Browser Mode): https://vitest.dev
- pytest: https://docs.pytest.org
- xUnit: https://xunit.net
- Stryker (mutation testing JS/.NET): https://stryker-mutator.io

## Cómo mantener esta guía al día
1. Revisa los changelogs de Claude Code, OpenCode, OpenSpec, Playwright y los SDK de MCP una vez al mes.
2. Tras actualizar Playwright: `npx playwright init-agents --loop=...`.
3. Tras actualizar OpenSpec: `openspec update`.
4. Pide a tu agente: *"Compara la sección X de esta guía con la documentación oficial actual y señala diferencias"* (con WebFetch o Context7 MCP).
