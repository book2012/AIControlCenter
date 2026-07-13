from fastapi.testclient import TestClient

from core.api.shadow import app


def test_shadow_health_is_available() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_shadow_blocks_mutating_requests() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/__shadow_write_probe__",
            json={"write": True},
        )

    assert response.status_code == 405

    payload = response.json()

    assert payload["detail"] == "shadow_read_only"
    assert payload["mode"] == "shadow-read-only"
    assert "GET" in payload["allowed_methods"]
