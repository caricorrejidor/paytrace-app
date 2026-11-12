"""Integridad del conjunto de evaluación (app/datos/evaluacion.json) contra el PRD.

La tabla de casos está escrita acá, a partir de PRD §3, y no se toma de app.simulador:
así el test detecta si los datos fijos o el simulador se apartan del PRD.
"""

import json
from collections import Counter
from datetime import timedelta

import pytest

from app.carga import RUTA_EVALUACION, cargar_operaciones
from app.modelos import Evento, Operacion

# PRD §3, tabla "Casos que se pueden generar", sin el caso OK.
# caso: (estado, secuencia de eventos del trace, evento clave)
TABLA_DE_CASOS = {
    "fondos insuficientes": (
        "fallida",
        ["orden enviada", "rechazo en origen, código AM04"],
        "rechazo en origen, código AM04",
    ),
    "cuenta incorrecta": (
        "fallida",
        ["orden enviada", "débito en origen", "rechazo del banco destino, código AC01", "reversa del débito"],
        "rechazo del banco destino, código AC01",
    ),
    "timeout con reversa": (
        "fallida",
        [
            "orden enviada",
            "débito en origen",
            "envío al proveedor",
            "rechazo por timeout, código AB05",
            "reversa del débito",
        ],
        "rechazo por timeout, código AB05",
    ),
    "timeout sin reversa": (
        "fallida",
        ["orden enviada", "débito en origen", "envío al proveedor", "rechazo por timeout, código AB05"],
        "rechazo por timeout, código AB05",
    ),
    # Sin evento clave: la causa esperada es "no concluyente".
    "trace incompleto": (
        "pendiente",
        ["orden enviada", "débito en origen"],
        None,
    ),
}

PLAZO_DE_ESPERA = timedelta(minutes=10)

REGISTROS = json.loads(RUTA_EVALUACION.read_text(encoding="utf-8"))
OPERACIONES = cargar_operaciones(RUTA_EVALUACION)
CASO_DE = {registro["id"]: registro["caso"] for registro in REGISTROS}


def describir(evento: Evento) -> str:
    """El evento como lo escribe el PRD, ej.: 'rechazo en origen, código AM04'."""
    if evento.codigo is None:
        return evento.tipo.value
    return f"{evento.tipo.value}, código {evento.codigo.value}"


def test_son_25_operaciones():
    assert len(OPERACIONES) == 25


def test_hay_5_operaciones_de_cada_caso_con_fallo_y_ninguna_ok():
    assert Counter(CASO_DE.values()) == {caso: 5 for caso in TABLA_DE_CASOS}


def test_los_ids_de_operacion_son_unicos():
    ids = [operacion.id for operacion in OPERACIONES]

    assert len(set(ids)) == len(ids)


def test_ningun_id_es_op_9xxx():
    assert not [operacion.id for operacion in OPERACIONES if operacion.id.startswith("OP-9")]


def test_los_ids_de_evento_son_unicos_en_todo_el_conjunto():
    ids = [evento.id for operacion in OPERACIONES for evento in operacion.trace]

    assert len(set(ids)) == len(ids)


@pytest.mark.parametrize("operacion", OPERACIONES, ids=lambda operacion: operacion.id)
def test_los_eventos_pertenecen_a_su_operacion_y_estan_en_orden(operacion: Operacion):
    assert [evento.id for evento in operacion.trace] == [
        f"{operacion.id}-E{numero}" for numero in range(1, len(operacion.trace) + 1)
    ]
    momentos = [evento.momento for evento in operacion.trace]
    assert momentos == sorted(momentos)
    assert len(set(momentos)) == len(momentos)


@pytest.mark.parametrize("operacion", OPERACIONES, ids=lambda operacion: operacion.id)
def test_cada_operacion_coincide_con_la_tabla_de_su_caso(operacion: Operacion):
    estado, secuencia, evento_clave = TABLA_DE_CASOS[CASO_DE[operacion.id]]
    descripciones = [describir(evento) for evento in operacion.trace]

    assert operacion.estado == estado
    assert descripciones == secuencia
    if evento_clave is not None:
        assert descripciones.count(evento_clave) == 1


@pytest.mark.parametrize(
    "operacion",
    [operacion for operacion in OPERACIONES if CASO_DE[operacion.id] == "trace incompleto"],
    ids=lambda operacion: operacion.id,
)
def test_trace_incompleto_con_mas_de_10_minutos_hasta_la_hora_de_referencia(operacion: Operacion):
    ultimo_evento = max(evento.momento for evento in operacion.trace)

    assert operacion.hora_referencia - ultimo_evento > PLAZO_DE_ESPERA
