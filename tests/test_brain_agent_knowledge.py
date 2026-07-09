from core.agent.brain_agent import BrainAgent


class FakeProviders:
    def chat(self, prompt, provider=None):
        return {
            "ok": True,
            "result": {
                "content": prompt
            },
        }


class FakeRouter:
    def route(self, prompt):
        return None


def test_brain_agent_knowledge_context():
    agent = BrainAgent(
        providers=FakeProviders(),
        router=FakeRouter(),
    )

    result = agent.ask_with_knowledge_context(
        "README"
    )

    assert "response" in result
    assert result["knowledge_count"] >= 1
