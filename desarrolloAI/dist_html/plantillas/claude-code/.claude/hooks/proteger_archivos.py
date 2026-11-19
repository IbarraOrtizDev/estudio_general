#!/usr/bin/env python3
"""Hook PreToolUse: bloquea ediciones de archivos protegidos (exit 2 = bloquear)."""
import json
import sys

PROTEGIDOS = (".env", "secrets/", "infra/prod/", ".git/", "package-lock.json", "pnpm-lock.yaml")

datos = json.load(sys.stdin)
ruta = str(datos.get("tool_input", {}).get("file_path", "")).replace("\\", "/")

if any(p in ruta for p in PROTEGIDOS):
    print(f"Bloqueado: '{ruta}' está protegido. Pide confirmación al usuario.", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
