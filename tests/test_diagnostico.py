"""F3 · Diagnóstico (RF-05 a RF-10): criterios de aceptación contra diagnosticar().

Interfaz que fijan estos tests (app/diagnostico.py):
- diagnosticar(operacion, ahora) es pura: "ahora" se pasa desde afuera.
- Devuelve un Diagnostico (causa, eventos_citados, recomendacion) o un Aviso (mensaje).
  El Aviso no tiene causa, eventos citados ni recomendación (AC-10, AC-12, AC-15).

Los textos esperados están copiados del PRD (tabla de §3 y §5), no del código.
"""

from datetime import timedelta

import pytest

from app.carga import cargar_operaciones
from app.diagnostico import Aviso, Diagnostico, diagnosticar
from app.modelos import Evento, Operacion
from app.simulador import Caso, generar
from tests.conftest import AHORA, RUTA_PRUEBA_PLAZO

ID = "OP-0026"

# PRD §3, columna "Causa".
CAUSAS = {"fondos insuficientes", "cuenta incorrecta", "timeout"}

# PRD §3, columna "Recomendación".
RECOMENDACIONES = {
    "fondos insuficientes": "Avisar al cliente que no tenía saldo. No se debitó nada",
    "cuenta incorrecta": "Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó",
    "timeout con reversa": "El débito ya se devolvió: se puede reintentar la transferencia",
    "timeout sin reversa": (
        "El débito todavía no se devolvió: pedir la reversa antes de reintentar. "
        "Si se reintenta antes, se cobra dos veces"
    ),
    "trace incompleto": "Pedir los logs del proveedor desde el último evento conocido",
}


def describir(evento: Evento) -> str:
    """El evento como lo escribe el PRD, ej.: 'rechazo en origen, código AM04'."""
    if evento.codigo is None:
        return evento.tipo.value
    return f"{evento.tipo.value}, código {evento.codigo.value}"


def diagnosticar_generada(caso: str):
    """'Dado que se generó una operación del caso X / Cuando el analista pide el diagnóstico'.

    "Ahora" es el momento de la generación: el trace incompleto ya nace con el plazo vencido (AC-13).
    """
    operacion = generar(Caso(caso), ID, AHORA)
    return operacion, diagnosticar(operacion, AHORA)


def operacion_de_prueba_plazo(id_operacion: str) -> Operacion:
    return {op.id: op for op in cargar_operaciones(RUTA_PRUEBA_PLAZO)}[id_operacion]


# AC-06 (RF-05) · Causa correcta por caso
@pytest.mark.parametrize(
    "caso, causa",
    [
        ("fondos insuficientes", "fondos insuficientes"),
        ("cuenta incorrecta", "cuenta incorrecta"),
        ("timeout con reversa", "timeout"),
        ("timeout sin reversa", "timeout"),
    ],
)
def test_ac06_causa_correcta_por_caso(caso, causa):
    _, resultado = diagnosticar_generada(caso)

    assert isinstance(resultado, Diagnostico)
    assert resultado.causa == causa


# AC-07 (RF-06) · Evidencia del trace
@pytest.mark.parametrize(
    "caso, evento_clave",
    [
        ("fondos insuficientes", "rechazo en origen, código AM04"),
        ("cuenta incorrecta", "rechazo del banco destino, código AC01"),
        ("timeout con reversa", "rechazo por timeout, código AB05"),
        ("timeout sin reversa", "rechazo por timeout, código AB05"),
    ],
)
def test_ac07_cita_solo_el_evento_clave_del_trace(caso, evento_clave):
    operacion, resultado = diagnosticar_generada(caso)
    [evento] = [e for e in operacion.trace if describir(e) == evento_clave]

    assert isinstance(resultado, Diagnostico)
    assert resultado.eventos_citados == [evento.id]


# AC-08 (RF-07) · Recomendación según la causa
@pytest.mark.parametrize(
    "caso",
    [
        "fondos insuficientes",
        "cuenta incorrecta",
        "timeout con reversa",
        "timeout sin reversa",
        "trace incompleto",
    ],
)
def test_ac08_recomendacion_segun_la_tabla_de_casos(caso):
    _, resultado = diagnosticar_generada(caso)

    assert isinstance(resultado, Diagnostico)
    assert resultado.recomendacion == RECOMENDACIONES[caso]


# AC-09 (RF-08) · No concluyente
def test_ac09_trace_incompleto_es_no_concluyente_sin_eventos_citados():
    _, resultado = diagnosticar_generada("trace incompleto")

    assert isinstance(resultado, Diagnostico)
    assert resultado.causa == "no concluyente"
    textos = f"{resultado.causa} {resultado.recomendacion}"
    assert not [causa for causa in CAUSAS if causa in textos]
    assert resultado.eventos_citados == []


# RF-08 · Límite del plazo de espera: un segundo después de los 10 minutos ya está vencido
def test_trace_incompleto_a_10_minutos_y_1_segundo_es_no_concluyente():
    operacion = generar(Caso.TRACE_INCOMPLETO, ID, AHORA)
    ahora = operacion.trace[-1].momento + timedelta(minutes=10, seconds=1)

    resultado = diagnosticar(operacion, ahora)

    assert isinstance(resultado, Diagnostico)
    assert resultado.causa == "no concluyente"
    assert resultado.eventos_citados == []


# AC-10 (RF-09) · Operación OK
def test_ac10_operacion_ok_no_tiene_fallo_para_investigar():
    _, resultado = diagnosticar_generada("OK")

    assert isinstance(resultado, Aviso)
    assert resultado.model_dump() == {"mensaje": "La operación no tiene un fallo para investigar"}


# AC-12 (RF-10) · Operación pendiente dentro del plazo de espera (último evento a 2 min)
def test_ac12_pendiente_dentro_del_plazo_sigue_en_curso():
    operacion = operacion_de_prueba_plazo("OP-0101")

    resultado = diagnosticar(operacion, operacion.hora_referencia)

    assert isinstance(resultado, Aviso)
    assert resultado.model_dump() == {"mensaje": "La operación sigue en curso"}


# AC-15 (RF-10) · Operación pendiente justo en el límite del plazo de espera (exactamente 10 min)
def test_ac15_pendiente_en_el_limite_del_plazo_sigue_en_curso():
    operacion = operacion_de_prueba_plazo("OP-0102")

    resultado = diagnosticar(operacion, operacion.hora_referencia)

    assert isinstance(resultado, Aviso)
    assert resultado.model_dump() == {"mensaje": "La operación sigue en curso"}
