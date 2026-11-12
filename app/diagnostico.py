"""Diagnóstico de una operación con reglas fijas (PRD §3, RF-05 a RF-10).

Es una función pura: no lee el reloj ni usa nada aleatorio. Quien la llama pasa
`ahora` (la hora_referencia en los datos fijos, la hora del sistema en las generadas).
Las reglas solo ven el trace y el estado: no conocen el caso con el que se generó.
"""

from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict

from app.modelos import CodigoMotivo, Estado, Evento, Operacion, TipoEvento

# PRD §1: el plazo vence solo con MÁS de 10 minutos sin eventos (exactamente 10 = en curso).
PLAZO_DE_ESPERA = timedelta(minutes=10)

MENSAJE_SIN_FALLO = "La operación no tiene un fallo para investigar"
MENSAJE_EN_CURSO = "La operación sigue en curso"

# PRD §3, columnas "Causa" y "Recomendación".
CAUSA_FONDOS_INSUFICIENTES = "fondos insuficientes"
CAUSA_CUENTA_INCORRECTA = "cuenta incorrecta"
CAUSA_TIMEOUT = "timeout"
NO_CONCLUYENTE = "no concluyente"

RECOMENDACION_FONDOS_INSUFICIENTES = "Avisar al cliente que no tenía saldo. No se debitó nada"
RECOMENDACION_CUENTA_INCORRECTA = (
    "Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó"
)
RECOMENDACION_TIMEOUT_CON_REVERSA = "El débito ya se devolvió: se puede reintentar la transferencia"
RECOMENDACION_TIMEOUT_SIN_REVERSA = (
    "El débito todavía no se devolvió: pedir la reversa antes de reintentar. "
    "Si se reintenta antes, se cobra dos veces"
)
RECOMENDACION_NO_CONCLUYENTE = "Pedir los logs del proveedor desde el último evento conocido"

# Evento clave de cada regla: (tipo, código de motivo) → causa.
EVENTOS_CLAVE: dict[tuple[TipoEvento, CodigoMotivo], str] = {
    (TipoEvento.RECHAZO_EN_ORIGEN, CodigoMotivo.AM04): CAUSA_FONDOS_INSUFICIENTES,
    (TipoEvento.RECHAZO_DEL_BANCO_DESTINO, CodigoMotivo.AC01): CAUSA_CUENTA_INCORRECTA,
    (TipoEvento.RECHAZO_POR_TIMEOUT, CodigoMotivo.AB05): CAUSA_TIMEOUT,
}


class Diagnostico(BaseModel):
    model_config = ConfigDict(extra="forbid")

    causa: str
    eventos_citados: list[str]
    recomendacion: str


class Aviso(BaseModel):
    """Respuesta sin diagnóstico: no lleva causa, eventos citados ni recomendación."""

    model_config = ConfigDict(extra="forbid")

    mensaje: str


def diagnosticar(operacion: Operacion, ahora: datetime) -> Diagnostico | Aviso:
    if ahora.tzinfo is None or ahora.utcoffset() is None:
        raise ValueError("'ahora' tiene que tener zona horaria")

    # RF-09: una operación OK no se diagnostica.
    if operacion.estado is Estado.OK:
        return Aviso(mensaje=MENSAJE_SIN_FALLO)

    trace = sorted(operacion.trace, key=lambda evento: evento.momento)

    # RF-05 a RF-07: una causa solo si el trace tiene exactamente un evento clave.
    claves = [evento for evento in trace if (evento.tipo, evento.codigo) in EVENTOS_CLAVE]
    if len(claves) == 1:
        return _diagnostico_con_causa(claves[0], trace)

    # RF-10: pendiente y todavía dentro del plazo de espera.
    if operacion.estado is Estado.PENDIENTE and trace and ahora - trace[-1].momento <= PLAZO_DE_ESPERA:
        return Aviso(mensaje=MENSAJE_EN_CURSO)

    # RF-08: la evidencia no alcanza (o es ambigua): no se inventa una causa.
    return Diagnostico(causa=NO_CONCLUYENTE, eventos_citados=[], recomendacion=RECOMENDACION_NO_CONCLUYENTE)


def _diagnostico_con_causa(clave: Evento, trace: list[Evento]) -> Diagnostico:
    causa = EVENTOS_CLAVE[(clave.tipo, clave.codigo)]
    if causa == CAUSA_FONDOS_INSUFICIENTES:
        recomendacion = RECOMENDACION_FONDOS_INSUFICIENTES
    elif causa == CAUSA_CUENTA_INCORRECTA:
        recomendacion = RECOMENDACION_CUENTA_INCORRECTA
    elif _hay_reversa_despues(clave, trace):
        recomendacion = RECOMENDACION_TIMEOUT_CON_REVERSA
    else:
        recomendacion = RECOMENDACION_TIMEOUT_SIN_REVERSA
    return Diagnostico(causa=causa, eventos_citados=[clave.id], recomendacion=recomendacion)


def _hay_reversa_despues(clave: Evento, trace: list[Evento]) -> bool:
    return any(
        evento.tipo is TipoEvento.REVERSA_DEL_DEBITO and evento.momento > clave.momento for evento in trace
    )
