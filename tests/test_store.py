from datetime import datetime, timezone

import pytest

from app.modelos import Estado, Operacion
from app.simulador import Caso, generar
from app.store import OperacionDuplicada, SinIdsLibres, Store

AHORA = datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc)


def crear(store: Store, caso: Caso = Caso.OK) -> Operacion:
    return store.crear(lambda id_operacion: generar(caso, id_operacion, AHORA))


def test_la_primera_operacion_es_op_0001():
    assert crear(Store()).id == "OP-0001"


def test_los_ids_generados_son_correlativos():
    store = Store()

    ids = [crear(store).id for _ in range(3)]

    assert ids == ["OP-0001", "OP-0002", "OP-0003"]


def test_el_id_generado_sigue_al_mayor_existente():
    store = Store()
    store.agregar(Operacion(id="OP-0025", estado=Estado.OK, trace=[]))

    assert crear(store).id == "OP-0026"


def test_el_id_generado_no_repite_uno_existente():
    store = Store()
    for numero in (1, 2, 5):
        store.agregar(Operacion(id=f"OP-{numero:04d}", estado=Estado.OK, trace=[]))

    nueva = crear(store)

    assert nueva.id not in {"OP-0001", "OP-0002", "OP-0005"}


def test_nunca_genera_un_id_op_9xxx():
    store = Store()
    store.agregar(Operacion(id="OP-8999", estado=Estado.OK, trace=[]))

    with pytest.raises(SinIdsLibres):
        crear(store)
    assert store.obtener("OP-9000") is None


def test_no_se_puede_agregar_un_id_repetido():
    store = Store()
    store.agregar(Operacion(id="OP-0001", estado=Estado.OK, trace=[]))

    with pytest.raises(OperacionDuplicada):
        store.agregar(Operacion(id="OP-0001", estado=Estado.FALLIDA, trace=[]))


def test_obtener_devuelve_la_operacion_guardada_o_none():
    store = Store()
    operacion = crear(store, Caso.CUENTA_INCORRECTA)

    assert store.obtener("OP-0001") == operacion
    assert store.obtener("OP-0002") is None


def test_listar_devuelve_las_operaciones_ordenadas_por_id():
    store = Store()
    store.agregar(Operacion(id="OP-0003", estado=Estado.OK, trace=[]))
    store.agregar(Operacion(id="OP-0001", estado=Estado.OK, trace=[]))

    assert [op.id for op in store.listar()] == ["OP-0001", "OP-0003"]
