"""Operaciones en memoria, sin base de datos (AGENTS.md)."""

from collections.abc import Callable
from threading import Lock

from app.modelos import Operacion

# PRD §1: ninguna operación usa IDs OP-9xxx (AC-04 usa OP-9999 como ID inexistente).
ULTIMO_NUMERO_PERMITIDO = 8999


class SinIdsLibres(Exception):
    pass


class OperacionDuplicada(Exception):
    pass


def _numero(id_operacion: str) -> int:
    return int(id_operacion.removeprefix("OP-"))


class Store:
    def __init__(self) -> None:
        self._operaciones: dict[str, Operacion] = {}
        self._lock = Lock()

    def agregar(self, operacion: Operacion) -> None:
        with self._lock:
            self._agregar(operacion)

    def crear(self, construir: Callable[[str], Operacion]) -> Operacion:
        """Toma el siguiente ID libre, construye la operación con ese ID y la guarda.

        El lock evita que dos pedidos simultáneos tomen el mismo ID.
        """
        with self._lock:
            operacion = construir(self._siguiente_id())
            self._agregar(operacion)
            return operacion

    def obtener(self, id_operacion: str) -> Operacion | None:
        return self._operaciones.get(id_operacion)

    def listar(self) -> list[Operacion]:
        with self._lock:
            operaciones = list(self._operaciones.values())
        return sorted(operaciones, key=lambda op: op.id)

    def _agregar(self, operacion: Operacion) -> None:
        if operacion.id in self._operaciones:
            raise OperacionDuplicada(operacion.id)
        self._operaciones[operacion.id] = operacion

    def _siguiente_id(self) -> str:
        """El número siguiente al mayor ID existente; OP-0001 si no hay ninguna."""
        mayor = max((_numero(id_op) for id_op in self._operaciones), default=0)
        siguiente = mayor + 1
        if siguiente > ULTIMO_NUMERO_PERMITIDO:
            raise SinIdsLibres(f"No quedan IDs libres por debajo de OP-{ULTIMO_NUMERO_PERMITIDO + 1}")
        return f"OP-{siguiente:04d}"
