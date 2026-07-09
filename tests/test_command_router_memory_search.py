from core.commands.router import CommandRouter
from core.memory.long_term import LongTermMemory
from core.memory.manager import MemoryManager
from core.memory.sqlite_store import SQLiteConversationStore
from core.memory.working import WorkingMemory


def test_command_router_memory_search(tmp_path):
    manager = MemoryManager(
        store=SQLiteConversationStore(str(tmp_path / "memory.db")),
        working=WorkingMemory(),
        long_term=LongTermMemory(),
    )

    manager.add_long_term("Telegram is connected", source="test")

    router = CommandRouter(memory=manager)

    result = router.route("/memory search telegram")

    assert "Memory Search" in result
    assert "Telegram is connected" in result
