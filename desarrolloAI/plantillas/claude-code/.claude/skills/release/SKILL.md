---
name: release
description: Prepara una release (changelog, versión y notas)
disable-model-invocation: true
argument-hint: "[major|minor|patch]"
allowed-tools: Bash(git log *) Bash(git describe *) Bash(npm version *)
---

Prepara una release de tipo $ARGUMENTS.

Commits desde el último tag:
!`git log $(git describe --tags --abbrev=0)..HEAD --oneline`

1. Agrupa los commits en Features, Fixes y Otros (en español).
2. Actualiza CHANGELOG.md.
3. Ejecuta `npm version $ARGUMENTS --no-git-tag-version`.
4. Muestra el resumen. NO hagas push ni crees tags.
