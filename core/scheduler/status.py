from core.scheduler.defaults import create_default_jobs
from core.scheduler.heartbeat import (
    DEFAULT_FRESHNESS_SECONDS,
    HeartbeatStore,
    classify_heartbeat,
)
from core.scheduler.jobs import JobRegistry


class SchedulerStatusService:
    def __init__(
        self,
        heartbeat: HeartbeatStore | None = None,
        jobs: JobRegistry | None = None,
        freshness_seconds: int = DEFAULT_FRESHNESS_SECONDS,
    ):
        self.heartbeat = heartbeat or HeartbeatStore()
        self.jobs = jobs or create_default_jobs()
        self.freshness_seconds = freshness_seconds

    def status(self):
        heartbeat = classify_heartbeat(
            self.heartbeat.latest(),
            self.freshness_seconds,
        )
        return {
            "status": heartbeat["status"],
            "heartbeat": heartbeat,
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

        if heartbeat["latest"]:
            lines.append(f"Heartbeat: {heartbeat['status']}")
            lines.append(f"Last: {heartbeat['latest']['created']}")
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
