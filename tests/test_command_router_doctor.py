from core.commands.router import CommandRouter


def test_command_router_doctor():
    router = CommandRouter()

    result = router.route("/doctor")

    assert "AIControlCenter Doctor" in result
    assert "Overall" in result
