from core.commands.router import CommandRouter


def test_command_router_backup_confirm():
    router = CommandRouter()

    result = router.route("/backup confirm")

    assert "Backup Confirm Token" in result
    assert "/backup run" in result
