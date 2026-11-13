# 07.1 · Pruebas unitarias con IA (Python, TypeScript, C# y en el navegador)

## Objetivos

- Usar agentes para escribir tests **útiles** (no solo cobertura).
- Aplicar TDD con agentes y evitar que "hagan trampa".
- Ejemplos completos con **pytest**, **Vitest** y **xUnit**.
- Ejecutar pruebas unitarias/de componentes **en un navegador real** con Vitest Browser Mode + Playwright.
- Medir la calidad de los tests (cobertura y mutation testing).

---

## 1. Por qué los tests son el centro del desarrollo agéntico

Los tests son el **mecanismo de verificación** del agente: le dicen si su cambio funciona sin que tú revises cada línea. Un repo con buena suite + comandos claros en `AGENTS.md` multiplica la calidad del trabajo agéntico.

```
Especificación (OpenSpec / prompt) → Tests (contrato) → Implementación (agente) → Verificación automática
```

---

## 2. Pirámide de tests en contexto agéntico

| Nivel | Herramientas | Velocidad | Papel con agentes |
|---|---|---|---|
| Unitarias | pytest, Vitest/Jest, xUnit/NUnit | ms | Feedback inmediato en cada paso |
| Componente (navegador) | Vitest Browser Mode, Playwright CT | ~s | UI aislada en navegador real |
| Integración | pytest + BD de test, WebApplicationFactory, Testcontainers | s | Contratos entre capas |
| E2E | Playwright | s–min | Flujos de usuario reales (07.2, 07.3) |

---

## 3. Reglas para tests generados por IA (ponlas en `AGENTS.md`)

```markdown
## Reglas de testing
- Nunca modifiques ni borres un test existente para que pase sin pedirme permiso.
- Nunca uses skip/xfail/only ni condicionales para "saltar" tests.
- Cada test verifica comportamiento observable, no detalles internos.
- Nombres descriptivos: `deberia_<resultado>_cuando_<condicion>`.
- Patrón Arrange-Act-Assert. Un comportamiento por test.
- Cubre: caso feliz, bordes (vacío, nulo, límites), errores.
- No hagas mocks de lo que no posees sin necesidad; prefiere fakes simples.
- Ejecuta la suite completa antes de dar la tarea por terminada.
```

### Anti-patrones típicos de tests escritos por IA
| Anti-patrón | Ejemplo | Cómo detectarlo |
|---|---|---|
| Test tautológico | Calcula el valor esperado con la misma fórmula que el código | Valores esperados literales |
| Solo "no lanza excepción" | `assert resultado is not None` | Revisión; mutation testing |
| Mock de todo | El test solo verifica que se llamó al mock | Exceso de `assert_called` |
| Ajustar el test al bug | Cambia el esperado para que pase | Revisa diffs en `tests/` |
| Casos especiales en producción | `if input == "caso_del_test": return ...` | Revisión del diff |

---

## 4. Prompts eficaces

**Cobertura de un módulo existente**
```text
Analiza src/descuentos.py y escribe tests pytest en tests/test_descuentos.py.
Primero lista los comportamientos y casos borde que vas a cubrir y espera mi OK.
Usa valores esperados literales (no recalcules con la lógica del código).
```

**TDD**
```text
Vamos a hacer TDD de `parsear_duracion("1h30m") -> int (minutos)`.
Escribe SOLO los tests (incluye "", "90m", "2h", "1h30m", "abc" → ValueError, negativos).
Ejecútalos y confirma que fallan. No implementes todavía.
```

**Desde una spec OpenSpec**
```text
Para cada Scenario de openspec/changes/agregar-paginacion/specs/tareas/spec.md
crea un test de integración. Usa el nombre del escenario como nombre del test.
```

---

## 5. Python · pytest

```bash
uv add --dev pytest pytest-cov
```

`src/descuentos.py`
```python
def calcular_descuento(total: float, premium: bool = False) -> float:
    """10% si total > 100; 15% si además es premium; máximo 50."""
    if total < 0:
        raise ValueError("El total no puede ser negativo")
    if total <= 100:
        return 0.0
    porcentaje = 0.15 if premium else 0.10
    return round(min(total * porcentaje, 50.0), 2)
```

`tests/test_descuentos.py`
```python
import pytest
from src.descuentos import calcular_descuento


@pytest.mark.parametrize(
    ("total", "premium", "esperado"),
    [
        (100, False, 0.0),      # límite: no aplica
        (100.01, False, 10.0),  # justo por encima
        (200, False, 20.0),
        (200, True, 30.0),
        (1000, True, 50.0),     # tope
    ],
)
def test_deberia_calcular_descuento(total, premium, esperado):
    assert calcular_descuento(total, premium) == pytest.approx(esperado, abs=0.01)


def test_deberia_fallar_con_total_negativo():
    with pytest.raises(ValueError, match="negativo"):
        calcular_descuento(-1)
```
```bash
uv run pytest --cov=src --cov-report=term-missing
```

---

## 6. TypeScript · Vitest

```bash
npm install -D vitest @vitest/coverage-v8
```

`src/duracion.ts`
```ts
export function parsearDuracion(texto: string): number {
    const m = /^(?:(\d+)h)?(?:(\d+)m)?$/.exec(texto.trim());
    if (!texto.trim() || !m || (!m[1] && !m[2])) throw new Error(`Duración inválida: "${texto}"`);
    return Number(m[1] ?? 0) * 60 + Number(m[2] ?? 0);
}
```

`src/duracion.test.ts`
```ts
import { describe, expect, it } from 'vitest';
import { parsearDuracion } from './duracion';

describe('parsearDuracion', () => {
    it.each([
        ['90m', 90],
        ['2h', 120],
        ['1h30m', 90],
        [' 1h ', 60],
    ])('convierte %s en %i minutos', (entrada, esperado) => {
        expect(parsearDuracion(entrada)).toBe(esperado);
    });

    it.each(['', 'abc', '1x', '-1h', 'h'])('lanza error con "%s"', entrada => {
        expect(() => parsearDuracion(entrada)).toThrow(/inválida/);
    });
});
```
```bash
npx vitest            # modo watch (ideal mientras el agente trabaja)
npx vitest run --coverage
```

---

## 7. C# · xUnit

```bash
dotnet new xunit -n Tareas.Tests
dotnet add Tareas.Tests reference Tareas.Core
```

`Tareas.Core/Descuentos.cs`
```csharp
namespace Tareas.Core;

public static class Descuentos
{
    public static decimal Calcular(decimal total, bool premium = false)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(total);
        if (total <= 100m) return 0m;
        var porcentaje = premium ? 0.15m : 0.10m;
        return Math.Round(Math.Min(total * porcentaje, 50m), 2);
    }
}
```

`Tareas.Tests/DescuentosTests.cs`
```csharp
using Tareas.Core;

public class DescuentosTests
{
    [Theory]
    [InlineData(100, false, 0)]
    [InlineData(100.01, false, 10)]
    [InlineData(200, false, 20)]
    [InlineData(200, true, 30)]
    [InlineData(1000, true, 50)]
    public void Deberia_CalcularDescuento(decimal total, bool premium, decimal esperado)
        => Assert.Equal(esperado, Descuentos.Calcular(total, premium));

    [Fact]
    public void Deberia_Fallar_CuandoTotalEsNegativo()
        => Assert.Throws<ArgumentOutOfRangeException>(() => Descuentos.Calcular(-1));
}
```
```bash
dotnet test --collect:"XPlat Code Coverage"
```
Para integración de APIs ASP.NET Core usa `WebApplicationFactory<Program>` (paquete `Microsoft.AspNetCore.Mvc.Testing`) y, para bases de datos reales, **Testcontainers**.

---

## 8. Pruebas unitarias en el navegador: Vitest Browser Mode + Playwright

Simular el DOM (jsdom) no siempre basta: eventos reales, CSS, APIs del navegador. **Vitest Browser Mode** ejecuta tus tests unitarios/de componentes en un navegador real usando **Playwright** como proveedor.

```bash
npm install -D vitest @vitest/browser-playwright playwright vitest-browser-react
npx playwright install chromium
```

`vitest.config.ts`
```ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { playwright } from '@vitest/browser-playwright';

export default defineConfig({
    plugins: [react()],
    test: {
        browser: {
            enabled: true,
            provider: playwright(),
            headless: true,
            instances: [{ browser: 'chromium' }, { browser: 'firefox' }]
        }
    }
});
```

`src/Contador.tsx`
```tsx
import { useState } from 'react';

export function Contador({ inicial = 0 }: { inicial?: number }) {
    const [n, setN] = useState(inicial);
    return (
        <div>
            <p>Valor: {n}</p>
            <button onClick={() => setN(n + 1)}>Incrementar</button>
        </div>
    );
}
```

`src/Contador.browser.test.tsx`
```tsx
import { expect, test } from 'vitest';
import { render } from 'vitest-browser-react';
import { Contador } from './Contador';

test('incrementa al hacer clic (navegador real)', async () => {
    const screen = await render(<Contador inicial={1} />);
    await screen.getByRole('button', { name: 'Incrementar' }).click();
    await expect.element(screen.getByText('Valor: 2')).toBeVisible();
});
```
```bash
npx vitest run
```
> Los localizadores (`getByRole`, `getByText`) siguen la misma filosofía que Playwright. Hay paquetes equivalentes para Vue (`vitest-browser-vue`) y Svelte. Verifica las rutas de importación en la doc de tu versión de Vitest (Browser Mode es estable desde Vitest 4).
>
> Alternativa: **Playwright Component Testing** (`@playwright/experimental-ct-react`), aún experimental.

---

## 9. Medir la calidad de los tests

- **Cobertura** (`--cov`, `--coverage`, Coverlet): necesaria pero no suficiente.
- **Mutation testing**: introduce bugs artificiales y mira si los tests fallan.
  - Python: `mutmut` · JS/TS: **Stryker** · .NET: **Stryker.NET**
- Prompt útil: *"Ejecuta Stryker sobre src/descuentos y escribe tests para los mutantes que sobreviven."*

---

## 10. Automatizar la verificación del agente

- Comandos de test en `AGENTS.md`.
- Hook `PostToolUse` que ejecuta los tests relacionados con el archivo editado.
- Hook `Stop` que exige suite verde (04.3).
- Subagente `test-writer` con permisos solo sobre `tests/**` (04.2).
- CI que bloquea merges con tests rojos o cobertura decreciente.

---

## Ejercicios

1. Pide a un agente tests para un módulo sin cobertura; revisa con la tabla de anti-patrones y corrige al menos 2 problemas.
2. Haz TDD de `parsearDuracion` (o equivalente) en los tres lenguajes.
   - ✅ Éxito: primero ves tests en rojo, luego en verde, sin que se modifiquen los tests.
3. Configura Vitest Browser Mode y prueba un componente en Chromium y Firefox.
4. Ejecuta mutation testing y sube el *mutation score* al menos un 10% con ayuda del agente.

## Checklist

- [ ] Tengo reglas de testing en `AGENTS.md`.
- [ ] Detecto tests tautológicos o con trampas.
- [ ] Escribo tests con pytest, Vitest y xUnit.
- [ ] Ejecuto tests de componentes en navegador real.
- [ ] Mido calidad con cobertura y mutation testing.

---

⬅️ [06.1](../06-spec-driven/01-openspec.md) · ➡️ [07.2 · Playwright E2E: fundamentos](02-playwright-e2e-fundamentos.md)
