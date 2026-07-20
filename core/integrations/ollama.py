"""Read-only Ollama health and model inventory adapter."""

from __future__ import annotations

import json
import socket
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_ENDPOINT = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT_SECONDS = 2.0


def _normalize_model(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    name = item.get("name")
    if not isinstance(name, str) or not name.strip():
        return None

    return {
        "name": name,
        "model": item.get("model"),
        "modified_at": item.get("modified_at"),
        "size": item.get("size"),
        "digest": item.get("digest"),
        "details": item.get("details"),
    }


def _failure(
    endpoint: str,
    error_type: str,
    message: str,
    latency_ms: int,
) -> dict[str, Any]:
    return {
        "service": "ollama",
        "installed": True,
        "running": False,
        "healthy": False,
        "status": "UNAVAILABLE",
        "endpoint": endpoint,
        "health_endpoint": f"{endpoint}/api/tags",
        "latency_ms": latency_ms,
        "model_count": 0,
        "models": [],
        "error": {
            "type": error_type,
            "message": message,
        },
    }


def inspect_ollama(
    endpoint: str = DEFAULT_ENDPOINT,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Return normalized read-only Ollama health and inventory JSON."""
    normalized_endpoint = endpoint.rstrip("/")
    url = f"{normalized_endpoint}/api/tags"
    started = time.monotonic()

    try:
        request = Request(
            url,
            method="GET",
            headers={"Accept": "application/json"},
        )
        with urlopen(request, timeout=timeout_seconds) as response:
            status_code = int(response.status)
            payload = json.loads(response.read().decode("utf-8"))

        if not isinstance(payload, dict):
            raise ValueError("response root must be a JSON object")

        raw_models = payload.get("models")
        if not isinstance(raw_models, list):
            raise ValueError("models must be a JSON array")

        models = [
            model
            for item in raw_models
            if (model := _normalize_model(item)) is not None
        ]

        latency_ms = round((time.monotonic() - started) * 1000)

        return {
            "service": "ollama",
            "installed": True,
            "running": True,
            "healthy": status_code == 200,
            "status": "ONLINE" if status_code == 200 else "DEGRADED",
            "endpoint": normalized_endpoint,
            "health_endpoint": url,
            "http_status": status_code,
            "latency_ms": latency_ms,
            "model_count": len(models),
            "models": models,
            "error": None,
        }

    except HTTPError as exc:
        latency_ms = round((time.monotonic() - started) * 1000)
        return _failure(
            normalized_endpoint,
            "http_error",
            f"HTTP {exc.code}",
            latency_ms,
        )
    except (URLError, socket.timeout, TimeoutError) as exc:
        latency_ms = round((time.monotonic() - started) * 1000)
        return _failure(
            normalized_endpoint,
            "connection_error",
            str(exc),
            latency_ms,
        )
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        latency_ms = round((time.monotonic() - started) * 1000)
        return _failure(
            normalized_endpoint,
            "invalid_response",
            str(exc),
            latency_ms,
        )
