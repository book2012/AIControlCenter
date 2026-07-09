from core.backup.verify import BackupVerifyService


def test_backup_verify_shape():
    service = BackupVerifyService()

    result = service.verify()

    assert "ok" in result
    assert "checks" in result
    assert "root_exists" in result["checks"]


def test_backup_verify_format_text():
    service = BackupVerifyService()

    text = service.format_text()

    assert "Backup Verify" in text
    assert "Read-only" in text
