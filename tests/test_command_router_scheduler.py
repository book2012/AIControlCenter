from core.commands.router import CommandRouter


def test_command_router_scheduler():
    router = CommandRouter()

    result = router.route("/scheduler")

    assert "Scheduler" in result
