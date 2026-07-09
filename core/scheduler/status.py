from core.scheduler.defaults import create_default_jobs
from core.scheduler.heartbeat import HeartbeatStore
from core.scheduler.jobs import JobRegistry


class SchedulerStatusService:
    def __init__(
        self,
        heartbeat: HeartbeatStore | None = None,
        jobs: JobRegistry | None = None,
    ):
        self.heartbeat = heartbeat or HeartbeatStore()
        self.jobs = jobs or create_default_jobs()

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

        for job in jobs:
            enabled = "ON" if job["enabled"] else "OFF"
            lines.append(
                f"- {job['name']} [{enabled}] every {job['interval_seconds']}s"
            )

        return "\n".join(lines)
