from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

# PRD §1: "OP-" seguido de 4 dígitos, en mayúscula (ej.: OP-0001).
PATRON_ID_OPERACION = r"^OP-[0-9]{4}$"
# ID de evento: el de su operación + "-E" + número de orden desde 1 (ej.: OP-0001-E1).
PATRON_ID_EVENTO = r"^OP-[0-9]{4}-E[1-9][0-9]*$"


class Estado(StrEnum):
    OK = "OK"
    FALLIDA = "fallida"
    PENDIENTE = "pendiente"


class Emisor(StrEnum):
    ORIGEN = "origen"
    PROVEEDOR = "proveedor"
    BANCO_DESTINO = "banco destino"


class TipoEvento(StrEnum):
    ORDEN_ENVIADA = "orden enviada"
    DEBITO_EN_ORIGEN = "débito en origen"
    ENVIO_AL_PROVEEDOR = "envío al proveedor"
    ACEPTACION_DEL_PROVEEDOR = "aceptación del proveedor"
    ACREDITACION_EN_DESTINO = "acreditación en destino"
    RECHAZO_EN_ORIGEN = "rechazo en origen"
    RECHAZO_DEL_BANCO_DESTINO = "rechazo del banco destino"
    RECHAZO_POR_TIMEOUT = "rechazo por timeout"
    REVERSA_DEL_DEBITO = "reversa del débito"


class CodigoMotivo(StrEnum):
    """Códigos de motivo ISO 20022 que usa el MVP (PRD §7)."""

    AM04 = "AM04"  # fondos insuficientes
    AC01 = "AC01"  # la cuenta no existe en el banco destino
    AB05 = "AB05"  # timeout del banco destino


TIPOS_RECHAZO = {
    TipoEvento.RECHAZO_EN_ORIGEN,
    TipoEvento.RECHAZO_DEL_BANCO_DESTINO,
    TipoEvento.RECHAZO_POR_TIMEOUT,
}


class Evento(BaseModel):
    # Un campo desconocido (ej.: mal escrito en un archivo de datos) es un error, no se ignora.
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=PATRON_ID_EVENTO)
    momento: AwareDatetime
    tipo: TipoEvento
    emisor: Emisor
    codigo: CodigoMotivo | None = None

    @model_validator(mode="after")
    def codigo_solo_en_rechazos(self) -> "Evento":
        es_rechazo = self.tipo in TIPOS_RECHAZO
        if es_rechazo and self.codigo is None:
            raise ValueError(f"El evento '{self.tipo}' es un rechazo y necesita código de motivo")
        if not es_rechazo and self.codigo is not None:
            raise ValueError(f"El evento '{self.tipo}' no es un rechazo y no lleva código de motivo")
        return self


class Operacion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=PATRON_ID_OPERACION)
    estado: Estado
    trace: list[Evento]
    # "Ahora" fijo para calcular el plazo de espera en los datos fijos (PRD §1).
    # None en las operaciones generadas: para ellas "ahora" es la hora del sistema.
    hora_referencia: AwareDatetime | None = None
