"""Paso 3.6 · POST /operaciones/{id}/diagnostico (RF-05 a RF-10 vía API)."""


def test_diagnostico_de_una_operacion_con_causa(cliente):
    cliente.post("/operaciones", json={"caso": "timeout sin reversa"})

    respuesta = cliente.post("/operaciones/OP-0001/diagnostico")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "causa": "timeout",
        "eventos_citados": ["OP-0001-E4"],
        "recomendacion": (
            "El débito todavía no se devolvió: pedir la reversa antes de reintentar. "
            "Si se reintenta antes, se cobra dos veces"
        ),
    }


def test_diagnostico_de_una_operacion_ok_es_un_aviso(cliente):
    cliente.post("/operaciones", json={"caso": "OK"})

    respuesta = cliente.post("/operaciones/OP-0001/diagnostico")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"mensaje": "La operación no tiene un fallo para investigar"}


def test_diagnostico_de_una_operacion_fija_usa_su_hora_de_referencia(cliente_con_evaluacion):
    # OP-0021 (trace incompleto): su último evento es del 06/11, después del reloj fijo de los
    # tests (04/11). Con la hora del sistema daría "sigue en curso"; con su hora de referencia
    # (11 min después del último evento) el plazo está vencido.
    respuesta = cliente_con_evaluacion.post("/operaciones/OP-0021/diagnostico")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "causa": "no concluyente",
        "eventos_citados": [],
        "recomendacion": "Pedir los logs del proveedor desde el último evento conocido",
    }


def test_diagnostico_con_un_id_mal_escrito_da_400(cliente):
    respuesta = cliente.post("/operaciones/op-0001/diagnostico")

    assert respuesta.status_code == 400
    assert respuesta.json() == {"detail": "Ingresá un ID con formato OP-0000"}


def test_diagnostico_de_un_id_que_no_existe_da_404(cliente):
    respuesta = cliente.post("/operaciones/OP-9999/diagnostico")

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detail": "Operación no encontrada"}
