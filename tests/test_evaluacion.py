"""Paso 3.7 · Objetivos medidos sobre el conjunto de evaluación (PRD §2 y §4).

La respuesta correcta sale del campo "caso" del JSON (metadato que el diagnóstico no ve).
Las causas y los eventos clave esperados están escritos acá, como en el PRD, no importados del código.
"""

import json

import pytest

from app.carga import RUTA_EVALUACION, cargar_operaciones
from app.diagnostico import Diagnostico, diagnosticar
from app.modelos import Evento, Operacion

# PRD §3, columna "Causa".
CAUSA_ESPERADA = {
    "fondos insuficientes": "fondos insuficientes",
    "cuenta incorrecta": "cuenta incorrecta",
    "timeout con reversa": "timeout",
    "timeout sin reversa": "timeout",
    "trace incompleto": "no concluyente",
}

# PRD §3, evento clave (en negrita) de cada caso con causa.
EVENTO_CLAVE = {
    "fondos insuficientes": "rechazo en origen, código AM04",
    "cuenta incorrecta": "rechazo del banco destino, código AC01",
    "timeout con reversa": "rechazo por timeout, código AB05",
    "timeout sin reversa": "rechazo por timeout, código AB05",
}

CASO_DE = {registro["id"]: registro["caso"] for registro in json.loads(RUTA_EVALUACION.read_text(encoding="utf-8"))}
OPERACIONES = cargar_operaciones(RUTA_EVALUACION)
CON_TRACE_COMPLETO = [op for op in OPERACIONES if CASO_DE[op.id] != "trace incompleto"]
CON_TRACE_INCOMPLETO = [op for op in OPERACIONES if CASO_DE[op.id] == "trace incompleto"]


def describir(evento: Evento) -> str:
    """El evento como lo escribe el PRD, ej.: 'rechazo en origen, código AM04'."""
    if evento.codigo is None:
        return evento.tipo.value
    return f"{evento.tipo.value}, código {evento.codigo.value}"


def diagnostico_de(operacion: Operacion) -> Diagnostico:
    resultado = diagnosticar(operacion, operacion.hora_referencia)
    assert isinstance(resultado, Diagnostico)
    return resultado


def por_id(operacion: Operacion) -> str:
    return operacion.id


def test_el_conjunto_tiene_20_con_trace_completo_y_5_incompletos():
    assert (len(CON_TRACE_COMPLETO), len(CON_TRACE_INCOMPLETO)) == (20, 5)


# OBJ-4 · Causa correcta: 100 % con la causa que corresponde al caso generado.
@pytest.mark.parametrize("operacion", OPERACIONES, ids=por_id)
def test_obj4_causa_correcta(operacion):
    assert diagnostico_de(operacion).causa == CAUSA_ESPERADA[CASO_DE[operacion.id]]


# OBJ-2 · Diagnósticos con evidencia: citan exactamente un evento, el evento clave de su caso.
@pytest.mark.parametrize("operacion", CON_TRACE_COMPLETO, ids=por_id)
def test_obj2_cita_exactamente_el_evento_clave_de_su_caso(operacion):
    [evento_clave] = [e for e in operacion.trace if describir(e) == EVENTO_CLAVE[CASO_DE[operacion.id]]]

    assert diagnostico_de(operacion).eventos_citados == [evento_clave.id]


# OBJ-3 · No inventar: los traces incompletos terminan como "no concluyente", sin eventos citados.
@pytest.mark.parametrize("operacion", CON_TRACE_INCOMPLETO, ids=por_id)
def test_obj3_trace_incompleto_es_no_concluyente_sin_eventos(operacion):
    diagnostico = diagnostico_de(operacion)

    assert diagnostico.causa == "no concluyente"
    assert diagnostico.eventos_citados == []


# RNF-04 · Consistencia: 5 pedidos del diagnóstico de la misma operación, vía API, dan lo mismo.
@pytest.mark.parametrize("operacion", OPERACIONES, ids=por_id)
def test_rnf04_cinco_pedidos_dan_el_mismo_resultado(cliente_con_evaluacion, operacion):
    respuestas = [cliente_con_evaluacion.post(f"/operaciones/{operacion.id}/diagnostico") for _ in range(5)]

    assert [r.status_code for r in respuestas] == [200] * 5
    cuerpos = [r.json() for r in respuestas]
    assert all(cuerpo == cuerpos[0] for cuerpo in cuerpos)
    assert cuerpos[0]["causa"] == CAUSA_ESPERADA[CASO_DE[operacion.id]]
