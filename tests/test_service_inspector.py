from pathlib import Path
from unittest.mock import patch

from core.deployment.inspect import (
    inspect_manifest,
    inspect_service,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/services/mac-standalone-production.json"


def test_unknown_service_returns_structured_error():
    result = inspect_manifest(MANIFEST, "missing-service")

    assert result["valid"] is False
    assert result["read_only"] is True
    assert result["service_count"] == 0
    assert result["errors"] == [
        "service not found: missing-service"
    ]


@patch("core.deployment.inspect.http_health")
@patch("core.deployment.inspect.port_listening")
@patch("core.deployment.inspect.command_available")
def test_ollama_not_installed_is_structured(
    command_available,
    port_listening,
    http_health,
):
    command_available.return_value = False
    port_listening.return_value = False
    http_health.return_value = {
        "checked": True,
        "url": "http://127.0.0.1:11434/api/tags",
        "status_code": None,
        "healthy": False,
        "error": {"type": "URLError", "message": "unavailable"},
    }

    service = {
        "service_id": "ollama",
        "required": False,
        "production_status": "NOT_RUNNING",
        "runtime": "native-macos",
        "supervisor": "UNASSIGNED",
        "listen_host": "127.0.0.1",
        "port": 11434,
        "health_endpoint": "/api/tags",
    }

    result = inspect_service(service)

    assert result["installed"] is False
    assert result["running"] is False
    assert result["listening"] is False
    assert result["healthy"] is False
    assert result["command"]["name"] == "ollama"

@patch("core.deployment.inspect.http_health")
@patch("core.deployment.inspect.port_listening")
@patch("core.deployment.inspect.inspect_launchd")
def test_launchdaemon_service_can_be_healthy(
    inspect_launchd,
    port_listening,
    http_health,
):
    inspect_launchd.return_value = {
        "checked": True,
        "label": "com.aicontrolcenter.api.shadow",
        "available": True,
        "running": True,
        "pid": 123,
        "error": None,
    }
    port_listening.return_value = True
    http_health.return_value = {
        "checked": True,
        "url": "http://127.0.0.1:18100/health",
        "status_code": 200,
        "healthy": True,
        "error": None,
    }

    service = {
        "service_id": "aicontrolcenter-api",
        "required": True,
        "production_status": "PRODUCTION",
        "runtime": "python-immutable-venv",
        "supervisor": "system-launchdaemon",
        "launchd_label": "com.aicontrolcenter.api.shadow",
        "listen_host": "127.0.0.1",
        "port": 18100,
        "health_endpoint": "/health",
    }

    result = inspect_service(service)

    assert result["installed"] is True
    assert result["running"] is True
    assert result["listening"] is True
    assert result["healthy"] is True
    assert result["supervisor"]["inspection"]["pid"] == 123
