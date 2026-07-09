from fastapi.testclient import TestClient

from core.api.app import app


client = TestClient(app)


def test_health_api():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ONLINE"


def test_brain_api():
    response = client.get("/brain")

    assert response.status_code == 200
    assert response.json()["role"] == "brain"


def test_dashboard_api():
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "brain" in response.json()
