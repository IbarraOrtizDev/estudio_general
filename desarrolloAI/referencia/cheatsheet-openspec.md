# Cheatsheet · OpenSpec 1.x

## Terminal
```bash
npm install -g @fission-ai/openspec@latest   # Node 20.19+
openspec init                 # elegir herramientas (Claude Code, OpenCode…)
openspec update               # tras actualizar el paquete
openspec list [--specs]
openspec view                 # dashboard
openspec show <cambio>
openspec validate <cambio>
openspec status --change <cambio>
openspec archive <cambio> --yes
openspec config profile       # core / expandido
```

## Chat del agente (perfil core)
```
/opsx:explore <idea>      pensar sin crear nada
/opsx:propose <nombre>    proposal + specs + design + tasks
/opsx:apply [nombre]      implementar tareas y marcarlas [x]
/opsx:archive [nombre]    fusionar deltas en specs/ y archivar
```
Perfil expandido: `/opsx:new`, `/opsx:continue`, `/opsx:ff`, `/opsx:verify`, `/opsx:sync`, `/opsx:bulk-archive`, `/opsx:onboard`.

Sintaxis según herramienta: Claude Code `/opsx:propose` · Cursor/Windsurf/Copilot `/opsx-propose` · Codex `$openspec-propose`.

## Estructura
```
openspec/
├── config.yaml
├── specs/<capacidad>/spec.md                 ← verdad actual
└── changes/<cambio>/
    ├── proposal.md · design.md · tasks.md
    └── specs/<capacidad>/spec.md             ← delta
```

## Formato de spec (delta)
```markdown
## ADDED Requirements
### Requirement: Nombre
El sistema SHALL ...
#### Scenario: caso
- **WHEN** ...
- **THEN** ...

## MODIFIED Requirements
## REMOVED Requirements
```

## Reglas rápidas
- Revisa SIEMPRE la propuesta antes de `apply`.
- Un comportamiento por requisito; escenarios con datos concretos; incluye errores.
- Comportamiento en specs; implementación en design.md.
- Un test por escenario.
- Archiva al terminar.
- Los comandos antiguos `/openspec:*` ya no existen.
