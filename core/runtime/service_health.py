import subprocess
from datetime import datetime, timedelta

from core.scheduler.heartbeat import HeartbeatStore


class ServiceHealth:
    SERVICES = {
        "api": "aicontrolcenter-api",
        "telegram": "aicontrolcenter-telegram",
        "scheduler": "aicontrolcenter-scheduler",
    }

    def __init__(
        self,
        heartbeat: HeartbeatStore | None = None,
        heartbeat_timeout_seconds: int = 90,
    ):
        self.heartbeat = heartbeat or HeartbeatStore()
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds

    def systemd_status(self, unit: str) -> str:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", unit],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.stdout.strip() or "unknown"
        except (OSError, subprocess.SubprocessError):
            return "unavailable"

    def heartbeat_status(self):
        latest = self.heartbeat.latest()

        if not latest:
            return {
                "status": "MISSING",
                "fresh": False,
                "latest": None,
            }

        created = datetime.fromisoformat(latest["created"])
        fresh = datetime.utcnow() - created <= timedelta(
            seconds=self.heartbeat_timeout_seconds
        )

        return {
            "status": "ALIVE" if fresh else "STALE",
            "fresh": fresh,
            "latest": latest,
        }

    def status(self):
        services = {
            name: {
                "unit": unit,
                "status": self.systemd_status(unit),
            }
            for name, unit in self.SERVICES.items()
        }

        heartbeat = self.heartbeat_status()

        healthy = (
            all(item["status"] == "active" for item in services.values())
            and heartbeat["fresh"]
        )

        return {
            "healthy": healthy,
            "services": services,
            "scheduler_heartbeat": heartbeat,
        }

    def format_text(self):
        data = self.status()

        lines = [
            "🛠 Service Health",
            "",
        ]

        for name, item in data["services"].items():
            marker = "✅" if item["status"] == "active" else "❌"
            lines.append(f"{marker} {name}: {item['status']}")

        heartbeat = data["scheduler_heartbeat"]
        marker = "✅" if heartbeat["fresh"] else "❌"
        lines.extend([
            "",
            f"{marker} heartbeat: {heartbeat['status']}",
            "",
            f"Overall: {'HEALTHY' if data['healthy'] else 'WARNING'}",
        ])

        return "\n".join(lines)
