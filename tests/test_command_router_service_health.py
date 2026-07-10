from core.commands.router import CommandRouter


def test_service_health_command():
    result = CommandRouter().route("/service-health")

    assert "Service Health" in result
    assert "Overall:" in result
