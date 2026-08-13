from core.scheduler.jobs import JobRegistry
from core.scheduler.runner import JobRunner, SchedulerExecutionPolicy


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


def test_scheduler_policy_allows_exact_automatic_command_set():
    policy = SchedulerExecutionPolicy()
    assert set(policy.ALLOWED_COMMANDS) == {
        "heartbeat",
        "/status",
        "/doctor",
        "/backup verify",
    }
    commands = {
        "heartbeat",
        "/status",
        "/doctor",
        "/backup verify",
        "/scheduler",
        "/memory",
        "/backup run token",
    }

    allowed = {command for command in commands if policy.check(command)["allowed"]}

    assert allowed == {"heartbeat", "/status", "/doctor", "/backup verify"}


def test_scheduler_blocks_command_even_if_generic_executor_permits_it():
    class PermissiveExecutor:
        def execute(self, action):
            return {"action": action, "executed": True, "blocked": False}

    registry = JobRegistry()
    job = registry.add("unsafe", "/future-generic-command", 60)

    result = JobRunner(executor=PermissiveExecutor()).run(job)

    assert result["ok"] is False
    assert result["result"]["blocked"] is True
