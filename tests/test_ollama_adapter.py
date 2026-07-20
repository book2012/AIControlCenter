import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import URLError

from core.integrations.ollama import inspect_ollama


class FakeResponse:
    def __init__(self, payload: object, status: int = 200):
        self.status = status
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return BytesIO(self._body).read()


@patch("core.integrations.ollama.urlopen")
def test_empty_inventory_is_online(urlopen):
    urlopen.return_value = FakeResponse({"models": []})

    result = inspect_ollama()

    assert result["healthy"] is True
    assert result["running"] is True
    assert result["status"] == "ONLINE"
    assert result["model_count"] == 0
    assert result["models"] == []
    assert result["error"] is None


@patch("core.integrations.ollama.urlopen")
def test_model_inventory_is_normalized(urlopen):
    urlopen.return_value = FakeResponse({
        "models": [
            {
                "name": "example:latest",
                "model": "example:latest",
                "modified_at": "2026-07-21T00:00:00Z",
                "size": 123,
                "digest": "sha256:test",
                "details": {"family": "example"},
            }
        ]
    })

    result = inspect_ollama()

    assert result["model_count"] == 1
    assert result["models"][0]["name"] == "example:latest"
    assert result["models"][0]["size"] == 123


@patch("core.integrations.ollama.urlopen")
def test_connection_failure_is_normalized(urlopen):
    urlopen.side_effect = URLError("connection refused")

    result = inspect_ollama(timeout_seconds=0.1)

    assert result["healthy"] is False
    assert result["running"] is False
    assert result["status"] == "UNAVAILABLE"
    assert result["model_count"] == 0
    assert result["error"]["type"] == "connection_error"


@patch("core.integrations.ollama.urlopen")
def test_invalid_models_contract_is_normalized(urlopen):
    urlopen.return_value = FakeResponse({"models": "invalid"})

    result = inspect_ollama()

    assert result["healthy"] is False
    assert result["error"]["type"] == "invalid_response"
