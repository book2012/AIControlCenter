from fastapi.testclient import TestClient

from core.api.app import app


client = TestClient(app)


def test_list_notifications_api():
    response = client.get("/notifications")

    assert response.status_code == 200
    assert "notifications" in response.json()


def test_send_notification_api():
    response = client.post(
        "/notifications",
        json={
            "title": "Test",
            "message": "Hello",
            "level": "INFO",
            "channel": "log",
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Test"
