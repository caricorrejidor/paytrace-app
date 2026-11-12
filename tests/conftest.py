from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app, obtener_ahora, obtener_store
from app.store import Store

AHORA = datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc)


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
