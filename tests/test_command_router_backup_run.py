from core.commands.router import CommandRouter


def test_command_router_backup_run_invalid_token():
    router = CommandRouter()

    result = router.route("/backup run invalid-token")

    assert "Backup Run" in result
    assert "Executed: False" in result
