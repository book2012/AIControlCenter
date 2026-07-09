from core.agent.brain_agent import BrainAgent
from core.memory.long_term import LongTermMemory
from core.memory.manager import MemoryManager
from core.memory.sqlite_store import SQLiteConversationStore
from core.memory.working import WorkingMemory


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


def test_brain_agent_uses_long_term_memory(tmp_path):
    manager = MemoryManager(
        store=SQLiteConversationStore(str(tmp_path / "memory.db")),
        working=WorkingMemory(),
        long_term=LongTermMemory(),
    )

    manager.add_long_term("Telegram is connected", source="test")

    agent = BrainAgent(
        providers=FakeProviders(),
        router=FakeRouter(),
        memory_manager=manager,
    )

    result = agent.ask_with_memory_context(
        "telegram 상태 알려줘"
    )

    assert result["memory_count"] == 1
    assert "Telegram is connected" in result["response"]["result"]["content"]
