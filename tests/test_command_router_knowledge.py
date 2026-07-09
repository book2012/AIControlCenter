from core.commands.router import CommandRouter


def test_command_router_knowledge():
    result = CommandRouter().route("/knowledge")

    assert "Knowledge" in result
    assert "Documents:" in result


def test_command_router_knowledge_search():
    result = CommandRouter().route("/knowledge search AIControlCenter")

    assert "Knowledge Search" in result
    assert "Results:" in result
