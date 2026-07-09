from fastapi.testclient import TestClient

from core.api.app import app


client = TestClient(app)


def test_automation_list_api():
    response = client.get("/automation")

    assert response.status_code == 200
    assert "items" in response.json()


def test_automation_submit_api():
    response = client.post(
        "/automation",
        json={"action": "/status"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "FINISHED"


def test_automation_submit_blocked_api():
    response = client.post(
        "/automation",
        json={"action": "/backup run token"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "BLOCKED"


def test_automation_missing_api():
    response = client.get("/automation/missing")

    assert response.status_code == 404
