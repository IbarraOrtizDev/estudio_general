---
description: Analiza y arregla un issue de GitHub
agent: build
---

Arregla el issue #$1:

!`gh issue view $1`

1. Entiende el problema y localiza el código relacionado.
2. Escribe un test que reproduzca el fallo y confirma que falla.
3. Arregla el código sin modificar el test.
4. Ejecuta la suite completa y el lint.
5. Resume los cambios y propone un mensaje de commit (Conventional Commits).
