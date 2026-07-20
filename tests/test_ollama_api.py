from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.api.routes.ollama import router


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@patch("core.api.routes.ollama.inspect_ollama")
def test_ollama_status_route_returns_adapter_contract(inspect_ollama):
    inspect_ollama.return_value = {
        "service": "ollama",
        "installed": True,
        "running": True,
        "healthy": True,
        "status": "ONLINE",
        "endpoint": "http://127.0.0.1:11434",
        "health_endpoint": "http://127.0.0.1:11434/api/tags",
        "http_status": 200,
        "latency_ms": 1,
        "model_count": 0,
        "models": [],
        "error": None,
    }

    response = build_client().get("/api/services/ollama")

    assert response.status_code == 200
    assert response.json()["service"] == "ollama"
    assert response.json()["healthy"] is True
    assert response.json()["model_count"] == 0
    inspect_ollama.assert_called_once_with()


@patch("core.api.routes.ollama.inspect_ollama")
def test_ollama_status_route_preserves_normalized_failure(inspect_ollama):
    inspect_ollama.return_value = {
        "service": "ollama",
        "installed": True,
        "running": False,
        "healthy": False,
        "status": "UNAVAILABLE",
        "endpoint": "http://127.0.0.1:11434",
        "health_endpoint": "http://127.0.0.1:11434/api/tags",
        "latency_ms": 2,
        "model_count": 0,
        "models": [],
        "error": {
            "type": "connection_error",
            "message": "connection refused",
        },
    }

    response = build_client().get("/api/services/ollama")

    assert response.status_code == 200
    assert response.json()["healthy"] is False
    assert response.json()["status"] == "UNAVAILABLE"
    assert response.json()["error"]["type"] == "connection_error"
