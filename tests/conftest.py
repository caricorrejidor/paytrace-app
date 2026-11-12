from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.carga import crear_store_con_evaluacion
from app.main import app, obtener_ahora, obtener_store
from app.store import Store

AHORA = datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc)

# Archivo de prueba de plazo (PRD §1): solo para tests, base de AC-12 y AC-15.
RUTA_PRUEBA_PLAZO = Path(__file__).parent / "datos" / "prueba_plazo.json"


@pytest.fixture
def store() -> Store:
    return Store()


@pytest.fixture
def cliente(store):
    """Cliente de la API con un store vacío propio y un reloj fijo."""
    app.dependency_overrides[obtener_store] = lambda: store
    app.dependency_overrides[obtener_ahora] = lambda: AHORA
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def cliente_con_evaluacion():
    """Cliente de la API con un store propio que tiene el conjunto de evaluación cargado."""
    store = crear_store_con_evaluacion()
    app.dependency_overrides[obtener_store] = lambda: store
    app.dependency_overrides[obtener_ahora] = lambda: AHORA
    yield TestClient(app)
    app.dependency_overrides.clear()
