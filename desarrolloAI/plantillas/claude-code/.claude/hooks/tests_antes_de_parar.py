#!/usr/bin/env python3
"""Hook Stop: impide terminar si los tests fallan. Ajusta COMANDO a tu stack."""
import json
import subprocess
import sys

COMANDO = ["pnpm", "test", "--silent"]   # p. ej. ["dotnet", "test"] o ["uv", "run", "pytest", "-q"]

datos = json.load(sys.stdin)
if datos.get("stop_hook_active"):        # evita bucles infinitos
    sys.exit(0)

r = subprocess.run(COMANDO, capture_output=True, text=True, shell=(sys.platform == "win32"))
if r.returncode != 0:
    salida = (r.stdout + r.stderr)[-3000:]
    print("Los tests fallan. Corrígelos antes de terminar:\n" + salida, file=sys.stderr)
    sys.exit(2)
sys.exit(0)
