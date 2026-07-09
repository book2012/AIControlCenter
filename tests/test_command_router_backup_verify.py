from core.commands.router import CommandRouter


def test_command_router_backup_verify():
    router = CommandRouter()

    result = router.route("/backup verify")

    assert "Backup Verify" in result
    assert "Read-only" in result
