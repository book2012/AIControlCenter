from core.commands.router import CommandRouter


def test_command_router_automation_status():
    result = CommandRouter().route("/automation")

    assert "Automation" in result


def test_command_router_automation_run():
    result = CommandRouter().route("/automation run /status")

    assert "Automation Run" in result
    assert "Status: FINISHED" in result


def test_command_router_automation_blocked():
    result = CommandRouter().route("/automation run /backup run token")

    assert "Automation Run" in result
    assert "Status: BLOCKED" in result
