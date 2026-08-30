from fastapi.testclient import TestClient

from core.api.app import app
from core.api.dependencies.audit import DATA_ROOT_ENV, reset_audit_dependencies


client = TestClient(app)


def test_health_api():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ONLINE"


def test_brain_api():
    response = client.get("/brain")

    assert response.status_code == 200
    assert response.json()["role"] == "brain"


def test_dashboard_api(tmp_path, monkeypatch):
    monkeypatch.setenv(DATA_ROOT_ENV, str(tmp_path / "audit-state"))
    reset_audit_dependencies()
    try:
        response = client.get("/dashboard")
    finally:
        reset_audit_dependencies()

    assert response.status_code == 200
    assert "brain" in response.json()
