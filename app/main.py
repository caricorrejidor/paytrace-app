import re
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel

from app.carga import crear_store_con_evaluacion
from app.diagnostico import Aviso, Diagnostico, diagnosticar
from app.modelos import PATRON_ID_OPERACION, Estado, Operacion
from app.simulador import Caso, generar
from app.store import SinIdsLibres, Store

app = FastAPI(title="PayTrace")

MENSAJE_FORMATO_INVALIDO = "Ingresá un ID con formato OP-0000"
MENSAJE_NO_ENCONTRADA = "Operación no encontrada"

# Al iniciar, la app ya tiene el conjunto de evaluación (OP-0001 a OP-0025);
# las operaciones generadas siguen desde OP-0026 (AC-14).
_store = crear_store_con_evaluacion()


def obtener_store() -> Store:
    return _store


def obtener_ahora() -> datetime:
    """Único lugar donde se lee el reloj del sistema. Los tests lo reemplazan."""
    return datetime.now(timezone.utc)


StoreDep = Annotated[Store, Depends(obtener_store)]
AhoraDep = Annotated[datetime, Depends(obtener_ahora)]


class PedidoGenerar(BaseModel):
    caso: Caso


class ResumenOperacion(BaseModel):
    id: str
    estado: Estado


@app.get("/salud")
def salud() -> dict[str, str]:
    return {"estado": "ok"}


@app.post("/operaciones", status_code=status.HTTP_201_CREATED)
def generar_operacion(pedido: PedidoGenerar, store: StoreDep, ahora: AhoraDep) -> Operacion:
    """RF-01: genera una operación simulada del caso elegido."""
    try:
        return store.crear(lambda id_operacion: generar(pedido.caso, id_operacion, ahora))
    except SinIdsLibres as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


@app.get("/operaciones")
def listar_operaciones(store: StoreDep) -> list[ResumenOperacion]:
    """RF-02: lista las operaciones con su estado, ordenadas por ID."""
    return [ResumenOperacion(id=op.id, estado=op.estado) for op in store.listar()]


def _obtener_operacion(store: Store, id_operacion: str) -> Operacion:
    """Valida el formato del ID y devuelve la operación (400 o 404 si no se puede)."""
    if not re.fullmatch(PATRON_ID_OPERACION, id_operacion):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, MENSAJE_FORMATO_INVALIDO)
    operacion = store.obtener(id_operacion)
    if operacion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, MENSAJE_NO_ENCONTRADA)
    return operacion


@app.get("/operaciones/buscar")
def buscar_operacion(store: StoreDep, id: str = "") -> Operacion:
    """RF-03 y RF-04: busca una operación por su ID y la devuelve con el trace en orden cronológico."""
    operacion = _obtener_operacion(store, id)
    trace_ordenado = sorted(operacion.trace, key=lambda evento: evento.momento)
    return operacion.model_copy(update={"trace": trace_ordenado})


@app.post("/operaciones/{id_operacion}/diagnostico")
def diagnosticar_operacion(id_operacion: str, store: StoreDep, ahora: AhoraDep) -> Diagnostico | Aviso:
    """RF-05 a RF-10: diagnostica la operación cuando el analista lo pide.

    "Ahora" es la hora de referencia en las operaciones fijas y la hora del sistema en las generadas.
    """
    operacion = _obtener_operacion(store, id_operacion)
    return diagnosticar(operacion, operacion.hora_referencia or ahora)
