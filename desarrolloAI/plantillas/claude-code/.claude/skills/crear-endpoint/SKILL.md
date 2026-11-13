---
name: crear-endpoint
description: >
  Crea un endpoint REST nuevo siguiendo la arquitectura del proyecto, con validación y tests.
  Úsala cuando pidan crear, añadir o exponer un endpoint o ruta HTTP. No la uses para GraphQL.
---

# Crear endpoint REST

## Pasos
1. Lee los endpoints existentes del mismo módulo para copiar el estilo.
2. Crea DTOs de entrada/salida (nunca expongas entidades de dominio).
3. Implementa la lógica en la capa de aplicación con su validador.
4. Registra la ruta (kebab-case, plural): `/api/<recurso>`.
5. Tests: caso feliz, validación (400), no encontrado (404), no autorizado (401/403).
6. Ejecuta tests y lint; corrige hasta verde.

## Reglas
- Respuestas de error con formato ProblemDetails (RFC 9457).
- Paginación por cursor en listados (`cursor`, `limit` ≤ 100).
