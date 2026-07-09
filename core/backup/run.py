from core.backup.confirm import BackupConfirmService


class BackupRunService:
    def __init__(self, confirm: BackupConfirmService | None = None):
        self.confirm = confirm or BackupConfirmService()

    def run(self, token: str):
        if not self.confirm.consume(token):
            return {
                "ok": False,
                "status": "blocked",
                "reason": "invalid_or_expired_token",
                "executed": False,
            }

        return {
            "ok": False,
            "status": "blocked",
            "reason": "backup_execution_not_enabled_yet",
            "executed": False,
        }

    def format_text(self, token: str):
        result = self.run(token)

        return "\n".join([
            "💾 Backup Run",
            "",
            f"Status: {result['status']}",
            f"Reason: {result['reason']}",
            f"Executed: {result['executed']}",
            "",
            "Safe mode: actual backup execution is disabled.",
        ])
