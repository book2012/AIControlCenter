from core.dashboard.api import DashboardAPI
from core.datacenter.backup_registry import BackupRegistry
from core.backup.verify import BackupVerifyService
from core.datacenter.storage_registry import StorageRegistry
from core.doctor.service import DoctorService
from core.logs.service import LogsService
from core.task.registry import TaskRegistry


class CommandRouter:
    def __init__(
        self,
        dashboard: DashboardAPI | None = None,
        storage: StorageRegistry | None = None,
        backup: BackupRegistry | None = None,
        registry: TaskRegistry | None = None,
        doctor: DoctorService | None = None,
        logs: LogsService | None = None,
        backup_verify: BackupVerifyService | None = None,
    ):
        self.dashboard = dashboard or DashboardAPI()
        self.storage = storage or StorageRegistry()
        self.backup = backup or BackupRegistry()
        self.registry = registry or TaskRegistry()
        self.doctor = doctor or DoctorService()
        self.logs = logs or LogsService()
        self.backup_verify = backup_verify or BackupVerifyService()

    def route(self, text: str) -> str:
        command = text.strip().lower()

        if command == "/status":
            return self.status()

        if command == "/storage":
            return self.storage_status()

        if command == "/backup":
            return self.backup_status()

        if command == "/backup verify":
            return self.backup_verify.format_text()

        if command == "/tasks":
            return self.tasks_status()

        if command == "/doctor":
            return self.doctor.format_text()

        if command == "/logs":
            return self.logs.format_text()

        if command == "/help":
            return self.help()

        return self.help()

    def status(self) -> str:
        data = self.dashboard.status()
        brain = data["brain"]
        integrations = brain["integrations"]["integrations"]

        return "\n".join([
            "🧠 AIControlCenter",
            f"State: {brain['state']}",
            f"Standalone: {brain['standalone']}",
            "",
            "Integrations:",
            f"- OpenAI: {'OK' if integrations['openai']['configured'] else 'NO'}",
            f"- Google: {'OK' if integrations['google']['configured'] else 'NO'}",
            f"- Notion: {'OK' if integrations['notion']['configured'] else 'NO'}",
            f"- GitHub: {'OK' if integrations['github']['configured'] else 'NO'}",
            "",
            f"Storage: {'OK' if data['storage']['exists'] else 'NO'}",
            f"Backup: {'OK' if data['backup']['exists'] else 'NO'}",
            f"Workers queried: {len(data['workers'])}",
        ])

    def storage_status(self) -> str:
        summary = self.storage.summary()

        lines = [
            "📦 Storage",
            f"Root: {summary['root']}",
            f"Exists: {'OK' if summary['exists'] else 'NO'}",
            "",
            "Categories:",
        ]

        for name, item in summary["categories"].items():
            marker = "✅" if item["exists"] else "❌"
            empty = (
                " empty"
                if item["file_count"] == 0 and item["directory_count"] == 0
                else ""
            )
            lines.append(
                f"- {marker} {name}: "
                f"{item['directory_count']} dirs, "
                f"{item['file_count']} files{empty}"
            )

        return "\n".join(lines)

    def backup_status(self) -> str:
        summary = self.backup.summary()

        lines = [
            "💾 Backup",
            f"Root: {summary['root']}",
            f"Exists: {'OK' if summary['exists'] else 'NO'}",
            "",
            "Categories:",
        ]

        for name, item in summary["categories"].items():
            marker = "✅" if item["exists"] else "❌"
            empty = (
                " empty"
                if item["file_count"] == 0 and item["directory_count"] == 0
                else ""
            )
            lines.append(
                f"- {marker} {name}: "
                f"{item['directory_count']} dirs, "
                f"{item['file_count']} files{empty}"
            )

        lines.append("")
        lines.append("Read-only mode. Use /backup only for status.")

        return "\n".join(lines)

    def tasks_status(self) -> str:
        running = self.registry.running()

        if not running:
            return "🧾 Tasks\nRunning: none"

        lines = ["🧾 Tasks", "Running:"]
        for task in running:
            lines.append(f"- {task.worker}: {task.command} ({task.status})")

        return "\n".join(lines)

    def help(self) -> str:
        return "\n".join([
            "AIControlCenter Commands",
            "",
            "/status  - Brain status",
            "/storage - Storage summary",
            "/backup  - Backup summary (read-only)",
            "/backup verify - Verify backup status",
            "/tasks   - Running tasks",
            "/doctor  - System diagnosis",
            "/logs    - Recent logs",
            "/help    - Command list",
            "/ask <message> - Ask BrainAgent",
        ])
