from datetime import datetime, timedelta, timezone

import pytest

from app.modelos import Evento
from app.simulador import Caso, generar

AHORA = datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc)


def describir(evento: Evento) -> str:
    """El evento como lo escribe el PRD, ej.: 'rechazo en origen, código AM04'."""
    if evento.codigo is None:
        return evento.tipo.value
    return f"{evento.tipo.value}, código {evento.codigo.value}"


# AC-01 (RF-01) · Generar una operación de cada caso
@pytest.mark.parametrize(
    "caso, estado, evento, ultimo_evento",
    [
        ("OK", "OK", "acreditación en destino", "acreditación en destino"),
        ("fondos insuficientes", "fallida", "rechazo en origen, código AM04", "rechazo en origen, código AM04"),
        ("cuenta incorrecta", "fallida", "rechazo del banco destino, código AC01", "reversa del débito"),
        ("timeout con reversa", "fallida", "rechazo por timeout, código AB05", "reversa del débito"),
        ("timeout sin reversa", "fallida", "rechazo por timeout, código AB05", "rechazo por timeout, código AB05"),
        ("trace incompleto", "pendiente", "débito en origen", "débito en origen"),
    ],
)
def test_ac01_generar_una_operacion_de_cada_caso(caso, estado, evento, ultimo_evento):
    operacion = generar(Caso(caso), "OP-0001", AHORA)

    assert operacion.estado == estado
    assert evento in [describir(e) for e in operacion.trace]
    assert describir(operacion.trace[-1]) == ultimo_evento


# AC-13 (RF-01) · El trace incompleto se genera con el plazo de espera vencido
def test_ac13_trace_incompleto_con_plazo_de_espera_vencido():
    operacion = generar(Caso.TRACE_INCOMPLETO, "OP-0001", AHORA)

    assert AHORA - operacion.trace[-1].momento > timedelta(minutes=10)


@pytest.mark.parametrize(
    "caso, eventos",
    [
        (Caso.OK, ["orden enviada", "débito en origen", "aceptación del proveedor", "acreditación en destino"]),
        (Caso.FONDOS_INSUFICIENTES, ["orden enviada", "rechazo en origen, código AM04"]),
        (
            Caso.CUENTA_INCORRECTA,
            ["orden enviada", "débito en origen", "rechazo del banco destino, código AC01", "reversa del débito"],
        ),
        (
            Caso.TIMEOUT_CON_REVERSA,
            [
                "orden enviada",
                "débito en origen",
                "envío al proveedor",
                "rechazo por timeout, código AB05",
                "reversa del débito",
            ],
        ),
        (
            Caso.TIMEOUT_SIN_REVERSA,
            ["orden enviada", "débito en origen", "envío al proveedor", "rechazo por timeout, código AB05"],
        ),
        (Caso.TRACE_INCOMPLETO, ["orden enviada", "débito en origen"]),
    ],
)
def test_el_trace_sigue_la_tabla_de_casos(caso, eventos):
    operacion = generar(caso, "OP-0001", AHORA)

    assert [describir(e) for e in operacion.trace] == eventos


@pytest.mark.parametrize("caso", list(Caso))
def test_los_eventos_estan_en_orden_cronologico(caso):
    operacion = generar(caso, "OP-0001", AHORA)
    momentos = [e.momento for e in operacion.trace]

    assert momentos == sorted(momentos)
    assert len(set(momentos)) == len(momentos)


@pytest.mark.parametrize("caso", list(Caso))
def test_los_ids_de_evento_son_correlativos_dentro_de_la_operacion(caso):
    operacion = generar(caso, "OP-0042", AHORA)

    assert operacion.id == "OP-0042"
    assert [e.id for e in operacion.trace] == [f"OP-0042-E{n}" for n in range(1, len(operacion.trace) + 1)]


@pytest.mark.parametrize("caso", [c for c in Caso if c is not Caso.TRACE_INCOMPLETO])
def test_ningun_evento_queda_despues_de_ahora(caso):
    operacion = generar(caso, "OP-0001", AHORA)

    assert operacion.trace[-1].momento == AHORA


def test_emisores_de_cada_tipo_de_evento():
    esperado = {
        "orden enviada": "origen",
        "débito en origen": "origen",
        "envío al proveedor": "origen",
        "rechazo en origen": "origen",
        "reversa del débito": "origen",
        "aceptación del proveedor": "proveedor",
        "rechazo por timeout": "proveedor",
        "acreditación en destino": "banco destino",
        "rechazo del banco destino": "banco destino",
    }
    emisores = {e.tipo.value: e.emisor.value for caso in Caso for e in generar(caso, "OP-0001", AHORA).trace}

    assert emisores == esperado


@pytest.mark.parametrize("caso", list(Caso))
def test_generar_es_determinista(caso):
    assert generar(caso, "OP-0001", AHORA) == generar(caso, "OP-0001", AHORA)


def test_generar_rechaza_un_ahora_sin_zona_horaria():
    ahora_sin_zona = datetime(2026, 11, 4, 10, 0)

    with pytest.raises(ValueError):
        generar(Caso.OK, "OP-0001", ahora_sin_zona)
