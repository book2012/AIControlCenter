from core.agent.router import AgentActionRouter


class FakeAction:
    def matches(self, message):
        return "status" in message

    def run(self, message):
        return {
            "action": "status",
            "message": message,
        }


def test_agent_action_router_match():
    router = AgentActionRouter(actions=[FakeAction()])

    result = router.route("status please")

    assert result["action"] == "status"


def test_agent_action_router_no_match():
    router = AgentActionRouter(actions=[FakeAction()])

    result = router.route("hello")

    assert result is None
