from core.notification.service import NotificationService


def test_notification_service_send():
    service = NotificationService()

    result = service.send(
        title="Test",
        message="Hello",
    )

    assert result["title"] == "Test"
    assert result["message"] == "Hello"
    assert result["level"] == "INFO"
    assert result["channel"] == "log"


def test_notification_service_list():
    service = NotificationService()

    service.send("A", "B")

    assert len(service.list()) == 1
