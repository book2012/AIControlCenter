from fastapi import APIRouter
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
    return {
        "notifications": service.list()
    }


@router.post("/notifications")
def send_notification(request: NotificationRequest):
    return service.send(
        title=request.title,
        message=request.message,
        level=request.level,
        channel=request.channel,
    )
