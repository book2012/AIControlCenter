from core.backup.plan import BackupPlanService


def test_backup_plan():
    service = BackupPlanService()

    plan = service.plan()

    assert plan["execution"] == "not_started"
    assert plan["mode"] == "read-only planning"
    assert len(plan["actions"]) > 0


def test_backup_plan_format_text():
    service = BackupPlanService()

    text = service.format_text()

    assert "Backup Plan" in text
    assert "No backup was executed" in text
