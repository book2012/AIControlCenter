from fastapi import APIRouter

from core.scheduler.status import SchedulerStatusService


router = APIRouter()

service = SchedulerStatusService()


@router.get("/scheduler")
def scheduler_status():
    return service.status()
