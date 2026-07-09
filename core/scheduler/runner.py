from core.automation.executor import AutomationExecutor
from core.scheduler.jobs import ScheduledJob


class JobRunner:
    def __init__(self, executor: AutomationExecutor | None = None):
        self.executor = executor or AutomationExecutor()

    def run(self, job: ScheduledJob):
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
