from fastapi import APIRouter

from core.scheduler.defaults import create_default_jobs
from core.scheduler.heartbeat import HeartbeatStore
from core.scheduler.loop import SchedulerLoop


router = APIRouter()

heartbeat = HeartbeatStore()
jobs = create_default_jobs()
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
