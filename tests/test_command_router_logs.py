from core.commands.router import CommandRouter


def test_command_router_logs():
    router = CommandRouter()

    result = router.route("/logs")

    assert "Logs" in result
