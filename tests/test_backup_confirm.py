from core.backup.confirm import BackupConfirmService


def test_backup_confirm_token():
    service = BackupConfirmService()

    token = service.create_token()

    assert token["token"]
    assert token["used"] is False
    assert service.validate(token["token"]) is True


def test_backup_confirm_consume():
    service = BackupConfirmService()

    token = service.create_token()

    assert service.consume(token["token"]) is True
    assert service.validate(token["token"]) is False


def test_backup_confirm_format_text():
    service = BackupConfirmService()

    text = service.format_text()

    assert "Backup Confirm Token" in text
    assert "/backup run" in text
