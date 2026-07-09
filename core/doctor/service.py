from core.brain.status import BrainStatus
from core.datacenter.backup_registry import BackupRegistry
from core.datacenter.storage_registry import StorageRegistry
from core.providers.manager import ProviderManager


class DoctorService:
    def __init__(self):
        self.brain = BrainStatus()
        self.providers = ProviderManager()
        self.storage = StorageRegistry()
        self.backup = BackupRegistry()

    def run(self):
        brain = self.brain.status()
        provider_health = self.providers.health()
        storage = self.storage.summary()
        backup = self.backup.summary()

        checks = [
            {
                "name": "Brain",
                "status": "OK" if brain["state"] == "ONLINE" else "ERROR",
                "message": brain["state"],
            },
            {
                "name": "Providers",
                "status": "OK" if provider_health["ready"] else "WARNING",
                "message": "Ready" if provider_health["ready"] else "No provider configured",
            },
            {
                "name": "Storage",
                "status": "OK" if storage["exists"] else "ERROR",
                "message": storage["root"],
            },
            {
                "name": "Backup",
                "status": "OK" if backup["exists"] else "ERROR",
                "message": backup["root"],
            },
            {
                "name": "Workers",
                "status": "WARNING",
                "message": "Optional worker not queried",
            },
        ]

        overall = "HEALTHY"

        if any(check["status"] == "ERROR" for check in checks):
            overall = "ERROR"
        elif any(check["status"] == "WARNING" for check in checks):
            overall = "WARNING"

        return {
            "overall": overall,
            "checks": checks,
        }

    def format_text(self):
        result = self.run()

        icon = {
            "OK": "🟢",
            "WARNING": "🟡",
            "ERROR": "🔴",
        }

        lines = [
            "🩺 AIControlCenter Doctor",
            "",
        ]

        for check in result["checks"]:
            lines.append(f"{icon[check['status']]} {check['name']}")
            lines.append(check["message"])
            lines.append("")

        lines.append("Overall")
        lines.append(result["overall"])

        return "\n".join(lines)
