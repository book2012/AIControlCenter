from core.automation.executor import AutomationExecutor
from core.scheduler.jobs import ScheduledJob


class SchedulerExecutionPolicy:
    """Narrow, scheduler-owned authority for unattended execution."""

    ALLOWED_COMMANDS = frozenset({
        "heartbeat",
        "/status",
        "/doctor",
        "/backup verify",
    })

    def check(self, command: str):
        allowed = command in self.ALLOWED_COMMANDS
        return {
            "allowed": allowed,
            "reason": (
                "allowed_scheduler_command"
                if allowed
                else "scheduler_command_not_allowed"
            ),
        }


class JobRunner:
    def __init__(
        self,
        executor: AutomationExecutor | None = None,
        policy: SchedulerExecutionPolicy | None = None,
    ):
        self.executor = executor or AutomationExecutor()
        self.policy = policy or SchedulerExecutionPolicy()

    def run(self, job: ScheduledJob):
        decision = self.policy.check(job.command)
        if not decision["allowed"]:
            return {
                "job": job.name,
                "command": job.command,
                "ok": False,
                "result": {
                    "action": job.command,
                    "executed": False,
                    "blocked": True,
                    "reason": decision["reason"],
                },
            }

        if job.command == "heartbeat":
            return {
                "job": job.name,
                "command": job.command,
                "ok": True,
                "result": "heartbeat handled by scheduler loop",
            }

        result = self.executor.execute(job.command)

        return {
            "job": job.name,
            "command": job.command,
            "ok": result.get("executed") is True,
            "result": result,
        }
