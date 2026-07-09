from core.scheduler.jobs import JobRegistry
from core.scheduler.runner import JobRunner


def test_job_runner_heartbeat():
    registry = JobRegistry()
    job = registry.add("heartbeat", "heartbeat", 30)

    result = JobRunner().run(job)

    assert result["ok"] is True
    assert result["job"] == "heartbeat"


def test_job_runner_command():
    registry = JobRegistry()
    job = registry.add("status", "/status", 60)

    result = JobRunner().run(job)

    assert result["ok"] is True
    assert result["result"]["executed"] is True


def test_job_runner_blocks_unsafe():
    registry = JobRegistry()
    job = registry.add("backup-run", "/backup run token", 60)

    result = JobRunner().run(job)

    assert result["ok"] is False
    assert result["result"]["blocked"] is True
