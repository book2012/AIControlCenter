from fastapi import APIRouter

from core.scheduler.defaults import create_default_jobs
from core.scheduler.heartbeat import HeartbeatStore
from core.scheduler.loop import SchedulerLoop
from core.scheduler.service import SchedulerService


router = APIRouter()

heartbeat = HeartbeatStore()
jobs = create_default_jobs()
loop = SchedulerLoop(
    heartbeat=heartbeat,
    jobs=jobs,
)
service = SchedulerService(loop=loop)


@router.get("/scheduler")
def scheduler_status():
    status = service.status()
    status["status"] = "ONLINE"
    return status


@router.post("/scheduler/tick")
def scheduler_tick():
    return loop.tick()
