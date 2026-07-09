from core.scheduler.heartbeat import HeartbeatStore
from core.scheduler.jobs import JobRegistry
from core.scheduler.loop import SchedulerLoop
from core.scheduler.service import SchedulerService


def test_scheduler_service_run_once(tmp_path):
    heartbeat = HeartbeatStore(str(tmp_path / "scheduler.db"))
    jobs = JobRegistry()
    jobs.add("heartbeat", "heartbeat", 30)

    loop = SchedulerLoop(
        heartbeat=heartbeat,
        jobs=jobs,
    )

    service = SchedulerService(
        interval_seconds=1,
        loop=loop,
    )

    result = service.run_once()

    assert result["heartbeat"]["status"] == "ALIVE"


def test_scheduler_service_run_for_ticks(tmp_path):
    heartbeat = HeartbeatStore(str(tmp_path / "scheduler.db"))
    jobs = JobRegistry()
    jobs.add("heartbeat", "heartbeat", 30)

    loop = SchedulerLoop(
        heartbeat=heartbeat,
        jobs=jobs,
    )

    service = SchedulerService(
        interval_seconds=1,
        loop=loop,
    )

    result = service.run_for_ticks(2)

    assert result["ticks"] == 2
    assert len(result["results"]) == 2
    assert service.running is False


def test_scheduler_service_status(tmp_path):
    heartbeat = HeartbeatStore(str(tmp_path / "scheduler.db"))
    jobs = JobRegistry()

    loop = SchedulerLoop(
        heartbeat=heartbeat,
        jobs=jobs,
    )

    service = SchedulerService(
        interval_seconds=1,
        loop=loop,
    )

    status = service.status()

    assert status["running"] is False
    assert status["interval_seconds"] == 1
    assert "jobs" in status
