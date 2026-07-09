from core.commands.router import CommandRouter


def test_command_router_homepage():
    result = CommandRouter().route("/homepage")

    assert "Homepage" in result
    assert "Brain:" in result
