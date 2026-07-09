from core.commands.router import CommandRouter


def test_command_router_plan():
    result = CommandRouter().route("/plan Check system status")

    assert "Plan" in result
    assert "Check system status" in result
