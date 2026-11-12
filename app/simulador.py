"""Genera operaciones simuladas según la tabla de casos del PRD (§3).

Es determinista: con el mismo caso, el mismo ID y el mismo `ahora`, da la misma
operación. No lee el reloj: quien lo llama pasa `ahora`.
"""

from datetime import datetime, timedelta
from enum import StrEnum

from app.modelos import CodigoMotivo, Emisor, Estado, Evento, Operacion, TipoEvento


class Caso(StrEnum):
    OK = "OK"
    FONDOS_INSUFICIENTES = "fondos insuficientes"
    CUENTA_INCORRECTA = "cuenta incorrecta"
    TIMEOUT_CON_REVERSA = "timeout con reversa"
    TIMEOUT_SIN_REVERSA = "timeout sin reversa"
    TRACE_INCOMPLETO = "trace incompleto"


# Un paso del trace: (tipo, emisor, código de motivo o None).
Paso = tuple[TipoEvento, Emisor, CodigoMotivo | None]

ORDEN_ENVIADA: Paso = (TipoEvento.ORDEN_ENVIADA, Emisor.ORIGEN, None)
DEBITO_EN_ORIGEN: Paso = (TipoEvento.DEBITO_EN_ORIGEN, Emisor.ORIGEN, None)
ENVIO_AL_PROVEEDOR: Paso = (TipoEvento.ENVIO_AL_PROVEEDOR, Emisor.ORIGEN, None)
ACEPTACION_DEL_PROVEEDOR: Paso = (TipoEvento.ACEPTACION_DEL_PROVEEDOR, Emisor.PROVEEDOR, None)
ACREDITACION_EN_DESTINO: Paso = (TipoEvento.ACREDITACION_EN_DESTINO, Emisor.BANCO_DESTINO, None)
RECHAZO_AM04: Paso = (TipoEvento.RECHAZO_EN_ORIGEN, Emisor.ORIGEN, CodigoMotivo.AM04)
RECHAZO_AC01: Paso = (TipoEvento.RECHAZO_DEL_BANCO_DESTINO, Emisor.BANCO_DESTINO, CodigoMotivo.AC01)
RECHAZO_AB05: Paso = (TipoEvento.RECHAZO_POR_TIMEOUT, Emisor.PROVEEDOR, CodigoMotivo.AB05)
REVERSA_DEL_DEBITO: Paso = (TipoEvento.REVERSA_DEL_DEBITO, Emisor.ORIGEN, None)

CASOS: dict[Caso, tuple[Estado, list[Paso]]] = {
    Caso.OK: (
        Estado.OK,
        [ORDEN_ENVIADA, DEBITO_EN_ORIGEN, ACEPTACION_DEL_PROVEEDOR, ACREDITACION_EN_DESTINO],
    ),
    Caso.FONDOS_INSUFICIENTES: (
        Estado.FALLIDA,
        [ORDEN_ENVIADA, RECHAZO_AM04],
    ),
    Caso.CUENTA_INCORRECTA: (
        Estado.FALLIDA,
        [ORDEN_ENVIADA, DEBITO_EN_ORIGEN, RECHAZO_AC01, REVERSA_DEL_DEBITO],
    ),
    Caso.TIMEOUT_CON_REVERSA: (
        Estado.FALLIDA,
        [ORDEN_ENVIADA, DEBITO_EN_ORIGEN, ENVIO_AL_PROVEEDOR, RECHAZO_AB05, REVERSA_DEL_DEBITO],
    ),
    Caso.TIMEOUT_SIN_REVERSA: (
        Estado.FALLIDA,
        [ORDEN_ENVIADA, DEBITO_EN_ORIGEN, ENVIO_AL_PROVEEDOR, RECHAZO_AB05],
    ),
    Caso.TRACE_INCOMPLETO: (
        Estado.PENDIENTE,
        [ORDEN_ENVIADA, DEBITO_EN_ORIGEN],
    ),
}

# Una transferencia inmediata se resuelve en segundos (PRD §1, plazo de espera).
SEPARACION_ENTRE_EVENTOS = timedelta(seconds=2)
# Para el trace incompleto, el último evento queda más de 10 minutos antes de `ahora` (AC-13).
ANTIGUEDAD_TRACE_INCOMPLETO = timedelta(minutes=15)


def generar(caso: Caso, id_operacion: str, ahora: datetime) -> Operacion:
    if ahora.tzinfo is None or ahora.utcoffset() is None:
        raise ValueError("'ahora' tiene que tener zona horaria (UTC)")
    estado, pasos = CASOS[caso]

    ultimo_momento = ahora
    if caso is Caso.TRACE_INCOMPLETO:
        ultimo_momento = ahora - ANTIGUEDAD_TRACE_INCOMPLETO
    primer_momento = ultimo_momento - SEPARACION_ENTRE_EVENTOS * (len(pasos) - 1)

    trace = [
        Evento(
            id=f"{id_operacion}-E{numero}",
            momento=primer_momento + SEPARACION_ENTRE_EVENTOS * (numero - 1),
            tipo=tipo,
            emisor=emisor,
            codigo=codigo,
        )
        for numero, (tipo, emisor, codigo) in enumerate(pasos, start=1)
    ]
    return Operacion(id=id_operacion, estado=estado, trace=trace)
