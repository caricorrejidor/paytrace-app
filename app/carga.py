"""Carga de operaciones desde archivos de datos fijos (PRD §1)."""

import json
from pathlib import Path

from app.modelos import Operacion
from app.store import Store

DIRECTORIO_DATOS = Path(__file__).parent / "datos"
RUTA_EVALUACION = DIRECTORIO_DATOS / "evaluacion.json"


def cargar_operaciones(ruta: Path) -> list[Operacion]:
    """Lee un archivo de datos fijo y devuelve sus operaciones.

    El campo "caso" de cada registro es un metadato (la respuesta correcta conocida
    para medir el acierto) y no entra en Operacion: las reglas no conocen el caso.
    """
    registros = json.loads(ruta.read_text(encoding="utf-8"))
    return [
        Operacion.model_validate({clave: valor for clave, valor in registro.items() if clave != "caso"})
        for registro in registros
    ]


def crear_store_con_evaluacion() -> Store:
    """Un store con el conjunto de evaluación ya cargado (AC-14)."""
    store = Store()
    for operacion in cargar_operaciones(RUTA_EVALUACION):
        store.agregar(operacion)
    return store
