from core.memory.long_term import LongTermMemory
from core.memory.manager import MemoryManager
from core.memory.sqlite_store import SQLiteConversationStore
from core.memory.working import WorkingMemory


def create_manager(tmp_path):
    store = SQLiteConversationStore(str(tmp_path / "memory.db"))
    return MemoryManager(
        store=store,
        working=WorkingMemory(),
        long_term=LongTermMemory(),
    )


def test_memory_manager_status(tmp_path):
    manager = create_manager(tmp_path)

    status = manager.status()

    assert status["ready"] is True
    assert status["type"] == "sqlite+working+long_term"
    assert "working_items" in status
    assert "long_term_items" in status


def test_memory_manager_session_flow(tmp_path):
    manager = create_manager(tmp_path)

    session = manager.create_session()
    manager.add_user_message(session["id"], "hello")
    manager.add_assistant_message(session["id"], "hi")

    loaded = manager.get_session(session["id"])

    assert len(loaded["messages"]) == 2


def test_memory_manager_working_memory(tmp_path):
    manager = create_manager(tmp_path)

    manager.set_working("focus", "memory")

    assert manager.get_working("focus")["value"] == "memory"
    assert len(manager.list_working()) == 1


def test_memory_manager_long_term_memory(tmp_path):
    manager = create_manager(tmp_path)

    item = manager.add_long_term("Telegram is connected")

    assert manager.get_long_term(item["id"])["content"] == "Telegram is connected"
    assert len(manager.search_long_term("telegram")) == 1
