from fastapi.testclient import TestClient

from core.api.app import app, create_app
from core.notifications import NotificationPlatform, NotificationProviderRegistry
from core.notifications.contracts import (
    NotificationChannel, NotificationProviderStatus, ProviderReadiness,
)


client = TestClient(app)


class FakeProvider:
    provider_id = "reference"

    def observe(self):
        return ProviderReadiness(
            "reference", NotificationProviderStatus.AVAILABLE, True, True,
            (NotificationChannel.EMAIL,),
        )


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


def test_get_only_pa04_api_and_dependency_injection():
    platform = NotificationPlatform(NotificationProviderRegistry((FakeProvider(),)))
    injected_app = create_app(notification_platform=platform)
    assert injected_app.state.notification_platform is platform
    injected_client = TestClient(injected_app)
    assert injected_client.get("/api/notifications/platform").json()["status"] == "READ_ONLY_VALIDATION"
    providers = injected_client.get("/api/notifications/providers").json()
    assert providers["providers"][0]["provider_id"] == "reference"
    for path in ("/api/notifications/platform", "/api/notifications/providers"):
        for method in ("post", "put", "patch", "delete"):
            assert getattr(injected_client, method)(path).status_code == 405
