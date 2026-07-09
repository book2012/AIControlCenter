from fastapi.testclient import TestClient

from core.api.app import app


client = TestClient(app)


def test_scheduler_status_api():
    response = client.get("/scheduler")

    assert response.status_code == 200
    assert response.json()["status"] == "ONLINE"


def test_scheduler_tick_api():
    response = client.post("/scheduler/tick")

    assert response.status_code == 200
    assert "heartbeat" in response.json()
    assert "due_jobs" in response.json()
