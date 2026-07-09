from core.commands.router import CommandRouter


def test_command_router_memory():
    router = CommandRouter()

    result = router.route("/memory")

    assert "Memory" in result
    assert "Sessions:" in result
