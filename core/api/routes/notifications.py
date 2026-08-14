"""Legacy notification API plus the separate GET-only PA-04 projection."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from core.notification.service import NotificationService


router = APIRouter()
service = NotificationService()


class NotificationRequest(BaseModel):
    title: str
    message: str
    level: str = "INFO"
    channel: str = "log"


@router.get("/notifications")
def list_notifications():
    return {"notifications": service.list()}


@router.post("/notifications")
def send_notification(request: NotificationRequest):
    return service.send(
        title=request.title,
        message=request.message,
        level=request.level,
        channel=request.channel,
    )


@router.get("/api/notifications/platform")
def notification_platform(request: Request) -> dict[str, object]:
    return request.app.state.notification_platform.platform()


@router.get("/api/notifications/providers")
def notification_providers(request: Request) -> dict[str, object]:
    return request.app.state.notification_platform.providers()
