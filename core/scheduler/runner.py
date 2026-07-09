from core.commands.router import CommandRouter
from core.scheduler.jobs import ScheduledJob


class JobRunner:
    def __init__(self, commands: CommandRouter | None = None):
        self.commands = commands or CommandRouter()

    def run(self, job: ScheduledJob):
        if job.command == "heartbeat":
            return {
                "job": job.name,
                "command": job.command,
                "ok": True,
                "result": "heartbeat handled by scheduler loop",
            }

        try:
            result = self.commands.route(job.command)

            return {
                "job": job.name,
                "command": job.command,
                "ok": True,
                "result": result,
            }

        except Exception as exc:
            return {
                "job": job.name,
                "command": job.command,
                "ok": False,
                "error": str(exc),
            }
