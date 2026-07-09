from core.commands.router import CommandRouter


def test_command_router_backup_plan():
    router = CommandRouter()

    result = router.route("/backup plan")

    assert "Backup Plan" in result
    assert "not started" in result
