from core.datacenter.backup_registry import BackupRegistry


class BackupVerifyService:
    def __init__(self, registry: BackupRegistry | None = None):
        self.registry = registry or BackupRegistry()

    def verify(self):
        summary = self.registry.summary()
        categories = summary["categories"]

        checks = {
            "root_exists": summary["exists"],
            "compose_backups": categories["compose"]["file_count"],
            "config_backups": categories["configs"]["file_count"],
            "log_files": categories["logs"]["file_count"],
            "server_snapshots": categories["server_backup"]["directory_count"],
        }

        ok = (
            checks["root_exists"]
            and checks["compose_backups"] > 0
            and checks["config_backups"] > 0
            and checks["log_files"] > 0
        )

        return {
            "ok": ok,
            "checks": checks,
        }

    def format_text(self):
        result = self.verify()
        checks = result["checks"]

        return "\n".join([
            "💾 Backup Verify",
            "",
            f"Root: {'OK' if checks['root_exists'] else 'NO'}",
            f"Compose backups: {checks['compose_backups']}",
            f"Config backups: {checks['config_backups']}",
            f"Log files: {checks['log_files']}",
            f"Server snapshots: {checks['server_snapshots']}",
            "",
            f"Overall: {'OK' if result['ok'] else 'WARNING'}",
            "",
            "Read-only verification. No backup was executed.",
        ])
