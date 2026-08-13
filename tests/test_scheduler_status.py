from core.scheduler.heartbeat import HeartbeatStore
from core.scheduler.jobs import JobRegistry
from core.scheduler.status import SchedulerStatusService


def test_scheduler_status_format_text(tmp_path):
    heartbeat = HeartbeatStore(str(tmp_path / "scheduler.db"))
    heartbeat.beat()

    service = SchedulerStatusService(
        heartbeat=heartbeat,
        jobs=JobRegistry(),
    )

    text = service.format_text()

    assert "Scheduler" in text
    assert "Heartbeat" in text


def test_scheduler_status_no_heartbeat(tmp_path):
    db_path = tmp_path / "scheduler.db"
    heartbeat = HeartbeatStore(str(db_path))

    service = SchedulerStatusService(
        heartbeat=heartbeat,
        jobs=JobRegistry(),
    )

    text = service.format_text()

    assert "Heartbeat: none" in text
    assert service.status()["status"] == "MISSING"
    assert service.status()["status"] != "ONLINE"
    assert not db_path.exists()
