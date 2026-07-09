from dataclasses import dataclass
from datetime import datetime


@dataclass
class Notification:
    title: str
    message: str
    level: str = "INFO"
    channel: str = "log"
    created: datetime = datetime.utcnow()

    def to_dict(self):
        return {
            "title": self.title,
            "message": self.message,
            "level": self.level,
            "channel": self.channel,
            "created": self.created.isoformat(),
        }


class NotificationService:
    def __init__(self):
        self.notifications = []

    def send(
        self,
        title: str,
        message: str,
        level: str = "INFO",
        channel: str = "log",
    ):
        notification = Notification(
            title=title,
            message=message,
            level=level,
            channel=channel,
        )

        self.notifications.append(notification)

        return notification.to_dict()

    def list(self):
        return [
            notification.to_dict()
            for notification in self.notifications
        ]
