from dataclasses import dataclass, field
from datetime import datetime

from core.adapters.telegram.bot import TelegramBotAdapter


@dataclass
class Notification:
    title: str
    message: str
    level: str = "INFO"
    channel: str = "log"
    created: datetime = field(default_factory=datetime.utcnow)
    delivery: dict | None = None

    def to_dict(self):
        return {
            "title": self.title,
            "message": self.message,
            "level": self.level,
            "channel": self.channel,
            "created": self.created.isoformat(),
            "delivery": self.delivery,
        }


class NotificationService:
    def __init__(self, telegram: TelegramBotAdapter | None = None):
        self.notifications = []
        self.telegram = telegram or TelegramBotAdapter()

    def send(
        self,
        title: str,
        message: str,
        level: str = "INFO",
        channel: str = "log",
    ):
        delivery = None

        if channel == "telegram":
            delivery = self.telegram.send_message(
                f"[{level}] {title}\n{message}"
            )

        notification = Notification(
            title=title,
            message=message,
            level=level,
            channel=channel,
            delivery=delivery,
        )

        self.notifications.append(notification)

        return notification.to_dict()

    def list(self):
        return [
            notification.to_dict()
            for notification in self.notifications
        ]
