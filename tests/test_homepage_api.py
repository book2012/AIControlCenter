from fastapi.testclient import TestClient

from core.api.app import app


client = TestClient(app)


def test_homepage_status_api():
    response = client.get("/homepage/status")

    assert response.status_code == 200
    assert "brain" in response.json()
    assert "scheduler" in response.json()
    assert "memory" in response.json()
    assert "knowledge" in response.json()
