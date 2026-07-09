from core.commands.router import CommandRouter


def test_command_router_worker():
    router = CommandRouter()

    result = router.route("/worker")

    assert "Workers" in result
