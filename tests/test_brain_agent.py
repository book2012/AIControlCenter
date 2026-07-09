from core.agent.brain_agent import BrainAgent


def test_brain_agent_ask_shape():
    agent = BrainAgent()

    result = agent.ask(
        prompt="hello",
        provider="missing",
    )

    assert "ok" in result
    assert "attempts" in result
