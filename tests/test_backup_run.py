from core.backup.confirm import BackupConfirmService
from core.backup.run import BackupRunService


def test_backup_run_invalid_token():
    confirm = BackupConfirmService()
    service = BackupRunService(confirm)

    result = service.run("missing")

    assert result["ok"] is False
    assert result["executed"] is False
    assert result["reason"] == "invalid_or_expired_token"


def test_backup_run_valid_token_blocked():
    confirm = BackupConfirmService()
    service = BackupRunService(confirm)

    token = confirm.create_token()["token"]
    result = service.run(token)

    assert result["ok"] is False
    assert result["executed"] is False
    assert result["reason"] == "backup_execution_not_enabled_yet"


def test_backup_run_format_text():
    service = BackupRunService()

    text = service.format_text("missing")

    assert "Backup Run" in text
    assert "Safe mode" in text
