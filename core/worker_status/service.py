from core.monitoring.snapshot import MonitoringSnapshot


class WorkerStatusService:
    def __init__(self, snapshot: MonitoringSnapshot | None = None):
        self.snapshot = snapshot or MonitoringSnapshot()

    def status(self, workers: list[str] | None = None):
        workers = workers or ["ubuntu-main"]
        return self.snapshot.collect(workers)

    def format_text(self, workers: list[str] | None = None):
        data = self.status(workers)

        lines = [
            "🖥️ Workers",
            "",
        ]

        for name, item in data.items():
            worker = item["worker"]
            session = item["session"]
            power = item["power"]
            error = item.get("error")

            lines.append(f"Worker: {name}")
            lines.append(f"Status: {worker.get('status')}")
            lines.append(f"Session: {session.get('state')}")
            lines.append(f"Can shutdown: {power.get('can_shutdown')}")

            if error:
                lines.append("Optional: unavailable")
                lines.append(f"Reason: {error}")

            lines.append("")

        return "\n".join(lines).strip()
