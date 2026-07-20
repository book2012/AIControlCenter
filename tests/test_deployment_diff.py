from pathlib import Path
from unittest.mock import patch

from core.deployment.diff import (
    build_deployment_diff,
    build_service_diff,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/services/mac-standalone-production.json"


def sample_plan() -> dict:
    return {
        "service_id": "ollama",
        "production_status": "NOT_RUNNING",
        "required_service": False,
        "health_endpoint": "/api/tags",
        "actions": [
            {"action": "validate", "write": False},
            {"action": "inspect", "write": False},
            {"action": "install", "write": True},
            {"action": "start", "write": True},
            {"action": "health", "write": False},
            {"action": "rollback", "write": True},
        ],
    }


def test_missing_ollama_requires_install_start_and_health():
    actual = {
        "installed": False,
        "running": False,
        "listening": False,
        "healthy": False,
    }

    result = build_service_diff(sample_plan(), actual)

    assert result["required_actions"] == [
        "install",
        "start",
        "health",
    ]
    assert result["write_required"] is True
    assert result["approval_required"] is True
    assert result["converged"] is False


def test_running_healthy_service_is_converged():
    actual = {
        "installed": True,
        "running": True,
        "listening": True,
        "healthy": True,
    }

    result = build_service_diff(sample_plan(), actual)

    assert result["required_actions"] == []
    assert result["write_required"] is False
    assert result["approval_required"] is False
    assert result["converged"] is True


@patch("core.deployment.diff.inspect_manifest")
def test_ollama_diff_returns_structured_json(inspect_manifest):
    inspect_manifest.return_value = {
        "valid": True,
        "read_only": True,
        "profile": "mac-standalone-production",
        "service_count": 1,
        "services": [
            {
                "service_id": "ollama",
                "installed": False,
                "running": False,
                "listening": False,
                "healthy": False,
            }
        ],
        "errors": [],
    }

    result = build_deployment_diff(
        MANIFEST,
        service_id="ollama",
    )

    assert result["valid"] is True
    assert result["read_only"] is True
    assert result["service_count"] == 1
    assert result["write_required"] is True
    assert result["errors"] == []

    diff = result["diffs"][0]
    assert diff["service_id"] == "ollama"
    assert diff["required_actions"] == [
        "install",
        "start",
        "health",
    ]


def test_unknown_service_returns_structured_error():
    result = build_deployment_diff(
        MANIFEST,
        service_id="missing-service",
    )

    assert result["valid"] is False
    assert result["service_count"] == 0
    assert result["write_required"] is False
    assert result["errors"] == [
        "service not found: missing-service"
    ]
