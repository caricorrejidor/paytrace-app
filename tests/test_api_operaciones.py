import pytest

from tests.conftest import AHORA


# AC-01 (RF-01) · Generar una operación de cada caso, vía API
@pytest.mark.parametrize(
    "caso, estado, ultimo_tipo",
    [
        ("OK", "OK", "acreditación en destino"),
        ("fondos insuficientes", "fallida", "rechazo en origen"),
        ("cuenta incorrecta", "fallida", "reversa del débito"),
        ("timeout con reversa", "fallida", "reversa del débito"),
        ("timeout sin reversa", "fallida", "rechazo por timeout"),
        ("trace incompleto", "pendiente", "débito en origen"),
    ],
)
def test_post_operaciones_genera_el_caso_elegido(cliente, caso, estado, ultimo_tipo):
    respuesta = cliente.post("/operaciones", json={"caso": caso})

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["id"] == "OP-0001"
    assert cuerpo["estado"] == estado
    assert cuerpo["trace"][-1]["tipo"] == ultimo_tipo


def test_post_operaciones_guarda_la_operacion(cliente, store):
    cuerpo = cliente.post("/operaciones", json={"caso": "cuenta incorrecta"}).json()

    assert store.obtener(cuerpo["id"]) is not None


def test_post_operaciones_asigna_ids_correlativos(cliente):
    ids = [cliente.post("/operaciones", json={"caso": "OK"}).json()["id"] for _ in range(3)]

    assert ids == ["OP-0001", "OP-0002", "OP-0003"]


def test_post_operaciones_usa_la_hora_del_sistema_con_zona_utc(cliente):
    cuerpo = cliente.post("/operaciones", json={"caso": "OK"}).json()

    assert cuerpo["trace"][-1]["momento"] == AHORA.isoformat().replace("+00:00", "Z")


@pytest.mark.parametrize("cuerpo", [{"caso": "importe no permitido"}, {"caso": "ok"}, {}])
def test_post_operaciones_rechaza_un_caso_invalido(cliente, cuerpo):
    respuesta = cliente.post("/operaciones", json=cuerpo)

    assert respuesta.status_code == 422


# AC-02 (RF-02) · Ver el estado de cada operación
def test_ac02_la_lista_muestra_el_estado_de_cada_operacion(cliente):
    for caso in ("OK", "fondos insuficientes", "trace incompleto"):
        cliente.post("/operaciones", json={"caso": caso})

    respuesta = cliente.get("/operaciones")

    assert respuesta.status_code == 200
    assert respuesta.json() == [
        {"id": "OP-0001", "estado": "OK"},
        {"id": "OP-0002", "estado": "fallida"},
        {"id": "OP-0003", "estado": "pendiente"},
    ]


def test_la_lista_vacia_devuelve_una_lista_vacia(cliente):
    respuesta = cliente.get("/operaciones")

    assert respuesta.status_code == 200
    assert respuesta.json() == []
