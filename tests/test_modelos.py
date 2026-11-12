from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.modelos import CodigoMotivo, Emisor, Estado, Evento, Operacion, TipoEvento

MOMENTO = datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc)


def test_un_rechazo_lleva_codigo_de_motivo():
    evento = Evento(
        id="OP-0001-E2",
        momento=MOMENTO,
        tipo=TipoEvento.RECHAZO_EN_ORIGEN,
        emisor=Emisor.ORIGEN,
        codigo=CodigoMotivo.AM04,
    )

    assert evento.codigo == "AM04"


def test_un_rechazo_sin_codigo_es_invalido():
    with pytest.raises(ValidationError):
        Evento(
            id="OP-0001-E2",
            momento=MOMENTO,
            tipo=TipoEvento.RECHAZO_EN_ORIGEN,
            emisor=Emisor.ORIGEN,
        )


def test_un_evento_que_no_es_rechazo_no_lleva_codigo():
    with pytest.raises(ValidationError):
        Evento(
            id="OP-0001-E1",
            momento=MOMENTO,
            tipo=TipoEvento.ORDEN_ENVIADA,
            emisor=Emisor.ORIGEN,
            codigo=CodigoMotivo.AM04,
        )


def test_un_codigo_fuera_del_mvp_es_invalido():
    with pytest.raises(ValidationError):
        Evento(
            id="OP-0001-E2",
            momento=MOMENTO,
            tipo=TipoEvento.RECHAZO_EN_ORIGEN,
            emisor=Emisor.ORIGEN,
            codigo="AM02",
        )


@pytest.mark.parametrize("id_operacion", ["op-0001", "OP-001", "OP-00001", "OP0001", "op1", ""])
def test_un_id_de_operacion_mal_escrito_es_invalido(id_operacion):
    with pytest.raises(ValidationError):
        Operacion(id=id_operacion, estado=Estado.OK, trace=[])


@pytest.mark.parametrize("id_evento", ["OP-0001", "OP-0001-E0", "OP-0001-e1", "OP-001-E1", "E1"])
def test_un_id_de_evento_mal_escrito_es_invalido(id_evento):
    with pytest.raises(ValidationError):
        Evento(
            id=id_evento,
            momento=MOMENTO,
            tipo=TipoEvento.ORDEN_ENVIADA,
            emisor=Emisor.ORIGEN,
        )


def test_un_momento_sin_zona_horaria_es_invalido():
    with pytest.raises(ValidationError):
        Evento(
            id="OP-0001-E1",
            momento=datetime(2026, 11, 4, 10, 0),
            tipo=TipoEvento.ORDEN_ENVIADA,
            emisor=Emisor.ORIGEN,
        )
