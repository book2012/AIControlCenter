from fastapi import APIRouter

from core.scheduler.heartbeat import HeartbeatStore
from core.scheduler.jobs import JobRegistry
from core.scheduler.loop import SchedulerLoop


router = APIRouter()

heartbeat = HeartbeatStore()
jobs = JobRegistry()
loop = SchedulerLoop(
    heartbeat=heartbeat,
    jobs=jobs,
)


@router.get("/scheduler")
def scheduler_status():
    latest = heartbeat.latest()

    return {
        "status": "ONLINE",
        "heartbeat": latest,
        "jobs": jobs.list(),
    }


@router.post("/scheduler/tick")
def scheduler_tick():
    return loop.tick()
