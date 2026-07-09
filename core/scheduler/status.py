from core.scheduler.heartbeat import HeartbeatStore
from core.scheduler.jobs import JobRegistry


class SchedulerStatusService:
    def __init__(
        self,
        heartbeat: HeartbeatStore | None = None,
        jobs: JobRegistry | None = None,
    ):
        self.heartbeat = heartbeat or HeartbeatStore()
        self.jobs = jobs or JobRegistry()

    def status(self):
        return {
            "status": "ONLINE",
            "heartbeat": self.heartbeat.latest(),
            "jobs": self.jobs.list(),
        }

    def format_text(self):
        status = self.status()
        heartbeat = status["heartbeat"]
        jobs = status["jobs"]

        lines = [
            "🫀 Scheduler",
            f"Status: {status['status']}",
            "",
        ]

        if heartbeat:
            lines.append(f"Heartbeat: {heartbeat['status']}")
            lines.append(f"Last: {heartbeat['created']}")
        else:
            lines.append("Heartbeat: none")

        lines.append("")
        lines.append(f"Jobs: {len(jobs)}")

        return "\n".join(lines)
