from datetime import timedelta

from core.scheduler.defaults import create_default_jobs
from core.scheduler.heartbeat import HeartbeatStore
from core.scheduler.jobs import JobRegistry
from core.scheduler.loop import SchedulerLoop


def test_scheduler_loop_tick(tmp_path):
    heartbeat = HeartbeatStore(str(tmp_path / "scheduler.db"))
    jobs = JobRegistry()
    jobs.add("heartbeat", "heartbeat", 30, run_on_start=True)

    loop = SchedulerLoop(
        heartbeat=heartbeat,
        jobs=jobs,
    )

    result = loop.tick()

    assert result["heartbeat"]["status"] == "ALIVE"
    assert len(result["due_jobs"]) == 1
    assert len(result["results"]) == 1


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
    assert result["results"] == []


def test_only_heartbeat_is_due_on_process_start(tmp_path):
    loop = SchedulerLoop(
        heartbeat=HeartbeatStore(str(tmp_path / "scheduler.db")),
        jobs=create_default_jobs(),
    )

    assert [job.name for job in loop.due_jobs()] == ["heartbeat"]


def test_non_startup_jobs_wait_for_their_intervals(tmp_path):
    loop = SchedulerLoop(
        heartbeat=HeartbeatStore(str(tmp_path / "scheduler.db")),
        jobs=create_default_jobs(),
    )

    after_one_hour = loop.started_at + timedelta(seconds=3600)
    assert {job.name for job in loop.due_jobs(after_one_hour)} == {
        "heartbeat",
        "doctor",
        "provider-check",
    }
    after_one_day = loop.started_at + timedelta(seconds=86400)
    assert {job.name for job in loop.due_jobs(after_one_day)} == {
        "heartbeat",
        "doctor",
        "provider-check",
        "backup-verify",
    }
