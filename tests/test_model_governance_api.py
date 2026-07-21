from fastapi.testclient import TestClient

from core.api.app import create_app


def test_model_governance_api_returns_empty_read_only_contract(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "core.api.routes.model_governance.inspect_ollama",
        lambda: {
            "service": "ollama",
            "healthy": True,
            "running": True,
            "status": "ONLINE",
            "model_count": 0,
            "models": [],
        },
    )

    client = TestClient(create_app())
    response = client.get("/api/governance/models")

    assert response.status_code == 200

    payload = response.json()

    assert payload["service"] == "model-governance"
    assert payload["mode"] == "read-only"
    assert payload["default_policy"] == "DENY"
    assert payload["healthy"] is True
    assert payload["approved_count"] == 0
    assert payload["observed_count"] == 0
    assert payload["compliant_count"] == 0
    assert payload["violation_count"] == 0
    assert payload["models"] == []
    assert payload["write_operations_allowed"] is False
    assert payload["runtime"] == {
        "service": "ollama",
        "healthy": True,
        "running": True,
        "status": "ONLINE",
    }


def test_model_governance_api_reports_unapproved_observed_model(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "core.api.routes.model_governance.inspect_ollama",
        lambda: {
            "service": "ollama",
            "healthy": True,
            "running": True,
            "status": "ONLINE",
            "model_count": 1,
            "models": [
                {
                    "name": "unknown:latest",
                    "digest": "sha256:unknown",
                    "size": 10,
                }
            ],
        },
    )

    client = TestClient(create_app())
    response = client.get("/api/governance/models")

    assert response.status_code == 200

    payload = response.json()

    assert payload["observed_count"] == 1
    assert payload["compliant_count"] == 0
    assert payload["violation_count"] == 1
    assert payload["models"][0]["runtime_name"] == "unknown:latest"
    assert payload["models"][0]["compliance_status"] == "UNAPPROVED"
    assert payload["models"][0]["available"] is False


def test_model_governance_api_reports_unhealthy_runtime(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "core.api.routes.model_governance.inspect_ollama",
        lambda: {
            "service": "ollama",
            "healthy": False,
            "running": False,
            "status": "OFFLINE",
            "model_count": 0,
            "models": [],
        },
    )

    client = TestClient(create_app())
    response = client.get("/api/governance/models")

    assert response.status_code == 200

    payload = response.json()

    assert payload["healthy"] is False
    assert payload["runtime"]["status"] == "OFFLINE"
    assert payload["write_operations_allowed"] is False
