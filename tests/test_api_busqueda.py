from datetime import timedelta

import pytest

from app.modelos import Emisor, Estado, Evento, Operacion, TipoEvento
from tests.conftest import AHORA


# AC-03 (RF-03) · Buscar un ID que existe
def test_ac03_buscar_un_id_que_existe(cliente):
    cliente.post("/operaciones", json={"caso": "OK"})

    respuesta = cliente.get("/operaciones/buscar", params={"id": "OP-0001"})

    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == "OP-0001"


# AC-04 (RF-03) · Buscar un ID que no existe
def test_ac04_buscar_un_id_que_no_existe(cliente):
    respuesta = cliente.get("/operaciones/buscar", params={"id": "OP-9999"})

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detail": "Operación no encontrada"}


# AC-05 (RF-04) · Ver el trace en orden
def test_ac05_ver_el_trace_en_orden(cliente):
    cliente.post("/operaciones", json={"caso": "cuenta incorrecta"})

    trace = cliente.get("/operaciones/buscar", params={"id": "OP-0001"}).json()["trace"]

    assert [e["tipo"] for e in trace] == [
        "orden enviada",
        "débito en origen",
        "rechazo del banco destino",
        "reversa del débito",
    ]
    momentos = [e["momento"] for e in trace]
    assert momentos == sorted(momentos)


def test_el_trace_se_muestra_en_orden_aunque_este_guardado_desordenado(cliente, store):
    def evento(numero: int, tipo: TipoEvento, segundos: int) -> Evento:
        return Evento(
            id=f"OP-0001-E{numero}",
            momento=AHORA + timedelta(seconds=segundos),
            tipo=tipo,
            emisor=Emisor.ORIGEN,
        )

    store.agregar(
        Operacion(
            id="OP-0001",
            estado=Estado.PENDIENTE,
            trace=[evento(2, TipoEvento.DEBITO_EN_ORIGEN, 2), evento(1, TipoEvento.ORDEN_ENVIADA, 0)],
        )
    )

    trace = cliente.get("/operaciones/buscar", params={"id": "OP-0001"}).json()["trace"]

    assert [e["id"] for e in trace] == ["OP-0001-E1", "OP-0001-E2"]


# AC-11 (RF-03) · Buscar un ID vacío o mal escrito
@pytest.mark.parametrize("id_buscado", ["op1", "op-0001", ""])
def test_ac11_buscar_un_id_vacio_o_mal_escrito(cliente, id_buscado):
    cliente.post("/operaciones", json={"caso": "OK"})  # existe OP-0001: no tiene que aparecer

    respuesta = cliente.get("/operaciones/buscar", params={"id": id_buscado})

    assert respuesta.status_code == 400
    assert respuesta.json() == {"detail": "Ingresá un ID con formato OP-0000"}


def test_buscar_sin_parametro_id_pide_el_formato(cliente):
    respuesta = cliente.get("/operaciones/buscar")

    assert respuesta.status_code == 400
    assert respuesta.json() == {"detail": "Ingresá un ID con formato OP-0000"}
