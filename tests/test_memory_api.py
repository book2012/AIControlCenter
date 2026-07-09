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


def test_working_memory_list_api():
    response = client.get("/memory/working")

    assert response.status_code == 200
    assert "items" in response.json()


def test_working_memory_set_get_api():
    response = client.post(
        "/memory/working",
        json={
            "key": "focus",
            "value": "memory",
        },
    )

    assert response.status_code == 200
    assert response.json()["key"] == "focus"

    response = client.get("/memory/working/focus")

    assert response.status_code == 200
    assert response.json()["value"] == "memory"
