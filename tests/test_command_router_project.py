from core.commands.router import CommandRouter


def test_command_router_sprint():
    result = CommandRouter().route("/sprint")

    assert "Sprint Status" in result


def test_command_router_agents():
    result = CommandRouter().route("/agents")

    assert "Agent Status" in result


def test_command_router_project():
    result = CommandRouter().route("/project")

    assert "AIControlCenter Project" in result
