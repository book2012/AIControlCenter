from core.scheduler.jobs import JobRegistry
from core.scheduler.runner import JobRunner


def test_job_runner_heartbeat():
    registry = JobRegistry()
    job = registry.add("heartbeat", "heartbeat", 30)

    runner = JobRunner()

    result = runner.run(job)

    assert result["ok"] is True
    assert result["job"] == "heartbeat"


def test_job_runner_command():
    registry = JobRegistry()
    job = registry.add("status", "/status", 60)

    runner = JobRunner()

    result = runner.run(job)

    assert result["ok"] is True
    assert "AIControlCenter" in result["result"]
