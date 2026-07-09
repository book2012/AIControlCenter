from fastapi.testclient import TestClient

from core.api.app import app


client = TestClient(app)


def test_memory_status_api():
    response = client.get("/memory")

    assert response.status_code == 200
    assert response.json()["ready"] is True


def test_memory_sessions_api():
    response = client.get("/memory/sessions")

    assert response.status_code == 200
    assert "sessions" in response.json()


def test_memory_missing_session_api():
    response = client.get("/memory/sessions/missing")

    assert response.status_code == 404
