from core.notification.service import NotificationService


class FakeTelegram:
    def send_message(self, message: str):
        return {
            "adapter": "telegram",
            "ok": True,
            "message": message,
        }


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


def test_notification_service_telegram_channel():
    service = NotificationService(
        telegram=FakeTelegram()
    )

    result = service.send(
        title="Alert",
        message="Hello Telegram",
        level="INFO",
        channel="telegram",
    )

    assert result["channel"] == "telegram"
    assert result["delivery"]["ok"] is True
