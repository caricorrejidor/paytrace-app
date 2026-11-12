import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.carga import RUTA_EVALUACION, cargar_operaciones, crear_store_con_evaluacion
from app.main import app, obtener_ahora, obtener_store
from app.modelos import Operacion
from app.simulador import Caso, generar
from tests.conftest import AHORA


def test_cargar_operaciones_devuelve_las_25_del_conjunto_de_evaluacion():
    operaciones = cargar_operaciones(RUTA_EVALUACION)

    assert len(operaciones) == 25
    assert [op.id for op in operaciones] == [f"OP-{n:04d}" for n in range(1, 26)]


def test_el_caso_es_un_metadato_del_archivo_y_no_entra_en_operacion():
    registros = json.loads(RUTA_EVALUACION.read_text(encoding="utf-8"))

    assert all("caso" in registro for registro in registros)
    assert "caso" not in Operacion.model_fields


REGISTRO_VALIDO = {
    "id": "OP-0001",
    "caso": "trace incompleto",
    "estado": "pendiente",
    "hora_referencia": "2026-11-06T09:14:02-03:00",
    "trace": [
        {"id": "OP-0001-E1", "momento": "2026-11-06T09:03:00-03:00", "tipo": "orden enviada", "emisor": "origen"},
    ],
}


def escribir(tmp_path, registros) -> Path:
    ruta = tmp_path / "datos.json"
    ruta.write_text(json.dumps(registros, ensure_ascii=False), encoding="utf-8")
    return ruta


def test_un_registro_valido_se_carga(tmp_path):
    [operacion] = cargar_operaciones(escribir(tmp_path, [REGISTRO_VALIDO]))

    assert operacion.hora_referencia is not None


def test_un_campo_desconocido_en_la_operacion_da_error_al_cargar(tmp_path):
    registro = {**REGISTRO_VALIDO}
    registro["hora_refrencia"] = registro.pop("hora_referencia")

    with pytest.raises(ValidationError, match="hora_refrencia"):
        cargar_operaciones(escribir(tmp_path, [registro]))


def test_un_campo_desconocido_en_un_evento_da_error_al_cargar(tmp_path):
    evento = {**REGISTRO_VALIDO["trace"][0], "codgo": "AM04"}
    registro = {**REGISTRO_VALIDO, "trace": [evento]}

    with pytest.raises(ValidationError, match="codgo"):
        cargar_operaciones(escribir(tmp_path, [registro]))


def test_las_operaciones_del_conjunto_tienen_hora_de_referencia_con_zona_horaria():
    for operacion in cargar_operaciones(RUTA_EVALUACION):
        assert operacion.hora_referencia is not None
        assert operacion.hora_referencia.utcoffset() is not None


def test_las_operaciones_generadas_no_tienen_hora_de_referencia():
    for caso in Caso:
        assert generar(caso, "OP-0026", AHORA).hora_referencia is None


def test_el_store_con_evaluacion_tiene_las_25_operaciones():
    assert len(crear_store_con_evaluacion().listar()) == 25


def test_la_app_inicia_con_el_conjunto_de_evaluacion_cargado():
    ids = [op.id for op in obtener_store().listar()]

    assert ids[:25] == [f"OP-{n:04d}" for n in range(1, 26)]


@pytest.fixture
def cliente_con_evaluacion():
    """Cliente de la API con un store propio que tiene el conjunto de evaluación cargado."""
    store = crear_store_con_evaluacion()
    app.dependency_overrides[obtener_store] = lambda: store
    app.dependency_overrides[obtener_ahora] = lambda: AHORA
    yield TestClient(app)
    app.dependency_overrides.clear()


# AC-14 (RF-01) · El ID generado no repite uno existente
@pytest.mark.parametrize("caso", [caso.value for caso in Caso])
def test_ac14_el_id_generado_no_repite_uno_existente(cliente_con_evaluacion, caso):
    existentes = {op["id"] for op in cliente_con_evaluacion.get("/operaciones").json()}

    nueva = cliente_con_evaluacion.post("/operaciones", json={"caso": caso}).json()

    assert nueva["id"] == "OP-0026"
    assert nueva["id"] not in existentes
    assert not nueva["id"].startswith("OP-9")
    assert nueva["hora_referencia"] is None


def test_las_generadas_siguen_correlativas_despues_del_conjunto(cliente_con_evaluacion):
    ids = [cliente_con_evaluacion.post("/operaciones", json={"caso": "OK"}).json()["id"] for _ in range(3)]

    assert ids == ["OP-0026", "OP-0027", "OP-0028"]


def test_buscar_una_operacion_del_conjunto_devuelve_su_hora_de_referencia(cliente_con_evaluacion):
    respuesta = cliente_con_evaluacion.get("/operaciones/buscar", params={"id": "OP-0021"})

    assert respuesta.status_code == 200
    assert respuesta.json()["hora_referencia"] == "2026-11-06T09:14:02-03:00"
