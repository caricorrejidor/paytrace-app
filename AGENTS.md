# AGENTS.md — PayTrace

## Propósito
PayTrace: herramienta para analistas de pagos que diagnostica por qué falló o quedó pendiente una transferencia simulada.
Aplica reglas fijas al trace, cita el evento que prueba la causa y recomienda el próximo paso.

## Stack
- Backend: Python 3.12 + FastAPI (última estable), gestionado con uv. Operaciones en memoria, sin base de datos.
- Tests: pytest. Los escenarios Gherkin del PRD se traducen a tests comunes de pytest (sin behave ni pytest-bdd).

## Cómo correr
- Instalar: `uv sync`
- Backend: `uv run uvicorn app.main:app --reload` → http://localhost:8000
- Tests: `uv run pytest`

## Qué NO hacer
- No devolver una causa sin citar exactamente un evento clave por su ID. Si la evidencia no alcanza, responder "no concluyente" sin eventos citados.
  Tampoco diagnosticar operaciones OK.
- No usar LLM ni nada aleatorio en el diagnóstico: solo reglas fijas, y la misma operación siempre da el mismo resultado.
- No conectar con bancos, proveedores ni sistemas reales, y no usar datos personales reales: todo es simulado.
- No commitear sin mostrar antes el git diff y esperar mi OK.
