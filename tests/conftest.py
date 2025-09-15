import pytest
from fastapi.testclient import TestClient

from soc_agent.webapp import app


@pytest.fixture(autouse=True)
def disable_side_effects(monkeypatch):
    monkeypatch.setenv("ENABLE_EMAIL", "0")
    monkeypatch.setenv("ENABLE_AUTOTASK", "0")
    yield


@pytest.fixture
def client():
    return TestClient(app)
