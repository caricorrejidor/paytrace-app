"""Archivo de prueba de plazo (PRD §1 Términos): 2 operaciones pendientes, aparte del
conjunto de evaluación, para AC-12 y AC-15. Se carga solo en los tests, no en la app."""

from datetime import timedelta
from pathlib import Path

import pytest

from app.carga import DIRECTORIO_DATOS, cargar_operaciones
from app.main import obtener_store
from app.modelos import Estado, Operacion

RUTA_PRUEBA_PLAZO = Path(__file__).parent / "datos" / "prueba_plazo.json"


@pytest.fixture
def operaciones_prueba_plazo() -> dict[str, Operacion]:
    return {op.id: op for op in cargar_operaciones(RUTA_PRUEBA_PLAZO)}


def antiguedad_del_ultimo_evento(operacion: Operacion) -> timedelta:
    ultimo = max(evento.momento for evento in operacion.trace)
    return operacion.hora_referencia - ultimo


def test_tiene_2_operaciones_pendientes_con_hora_de_referencia(operaciones_prueba_plazo):
    assert sorted(operaciones_prueba_plazo) == ["OP-0101", "OP-0102"]
    for operacion in operaciones_prueba_plazo.values():
        assert operacion.estado == Estado.PENDIENTE
        assert operacion.hora_referencia is not None


# Base de AC-12: el último evento es 2 minutos anterior a su hora de referencia.
def test_op_0101_tiene_el_ultimo_evento_a_2_minutos(operaciones_prueba_plazo):
    assert antiguedad_del_ultimo_evento(operaciones_prueba_plazo["OP-0101"]) == timedelta(minutes=2)


# Base de AC-15: el último evento es exactamente 10 minutos anterior a su hora de referencia.
def test_op_0102_tiene_el_ultimo_evento_a_exactamente_10_minutos(operaciones_prueba_plazo):
    assert antiguedad_del_ultimo_evento(operaciones_prueba_plazo["OP-0102"]) == timedelta(minutes=10)


def test_el_archivo_no_esta_entre_los_datos_de_la_app():
    assert not RUTA_PRUEBA_PLAZO.resolve().is_relative_to(DIRECTORIO_DATOS.resolve())


def test_la_app_no_carga_las_operaciones_de_prueba_de_plazo(operaciones_prueba_plazo):
    store_de_la_app = obtener_store()

    for id_operacion in operaciones_prueba_plazo:
        assert store_de_la_app.obtener(id_operacion) is None
