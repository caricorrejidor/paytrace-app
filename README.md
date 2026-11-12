# PayTrace

PayTrace: ayuda a analistas de pagos a investigar por qué falló una transferencia.

## Requisitos

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

## Cómo correrla

```bash
git clone https://github.com/caricorrejidor/paytrace-app.git
cd paytrace-app
uv sync
uv run pytest
uv run uvicorn app.main:app --reload
```

Después abrí http://localhost:8000/docs.

## Probalo en 3 pasos (desde /docs)

1. `POST /operaciones` con el body `{"caso": "timeout sin reversa"}` → crea la operación `OP-0026`.
2. `POST /operaciones/{id}/diagnostico` con el ID que devolvió el paso 1 (es `OP-0026` si es la primera operación que se crea después de arrancar el servidor) → causa `timeout`, citando el evento `OP-0026-E4`.
3. `POST /operaciones/OP-0021/diagnostico` → `no concluyente`, sin eventos citados.

## Qué incluye

- **F1 – Operaciones:** generar, listar y buscar operaciones simuladas.
- **F2 – Datos fijos:** las operaciones `OP-0001` a `OP-0025` vienen precargadas.
- **F3 – Diagnóstico:** reglas fijas que dan la causa, citan el evento que la prueba y recomiendan el próximo paso.

## Limitaciones

- Datos 100 % simulados: no conecta con bancos ni proveedores reales.
- Sin base de datos: todo vive en memoria y se pierde al reiniciar.
- Sin autenticación: pensada para uso local.
