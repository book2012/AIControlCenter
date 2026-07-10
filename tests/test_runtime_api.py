from fastapi.testclient import TestClient

from core.api.app import app


client = TestClient(app)


def test_runtime_health_api():
    response = client.get("/runtime/health")

    assert response.status_code == 200
    assert "healthy" in response.json()
    assert "services" in response.json()
    assert "scheduler_heartbeat" in response.json()
