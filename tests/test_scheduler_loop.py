from core.scheduler.heartbeat import HeartbeatStore
from core.scheduler.jobs import JobRegistry
from core.scheduler.loop import SchedulerLoop


def test_scheduler_loop_tick(tmp_path):
    heartbeat = HeartbeatStore(str(tmp_path / "scheduler.db"))
    jobs = JobRegistry()
    jobs.add("heartbeat", "heartbeat", 30)

    loop = SchedulerLoop(
        heartbeat=heartbeat,
        jobs=jobs,
    )

    result = loop.tick()

    assert result["heartbeat"]["status"] == "ALIVE"
    assert len(result["due_jobs"]) == 1


def test_scheduler_loop_disabled_job(tmp_path):
    heartbeat = HeartbeatStore(str(tmp_path / "scheduler.db"))
    jobs = JobRegistry()
    job = jobs.add("doctor", "/doctor", 3600)
    jobs.disable(job.id)

    loop = SchedulerLoop(
        heartbeat=heartbeat,
        jobs=jobs,
    )

    result = loop.tick()

    assert result["due_jobs"] == []
