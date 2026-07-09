from core.agent.brain_agent import BrainAgent


def test_brain_agent_memory_shape():
    agent = BrainAgent()

    result = agent.ask_with_memory(
        prompt="hello",
        provider="missing",
    )

    assert "session" in result
    assert "response" in result
    assert len(result["session"]["messages"]) == 2
    assert result["session"]["messages"][0]["role"] == "user"
    assert result["session"]["messages"][1]["role"] == "assistant"
