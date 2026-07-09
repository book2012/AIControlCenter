from core.memory.manager import MemoryManager
from core.memory.sqlite_store import SQLiteConversationStore
from core.memory.working import WorkingMemory


def test_memory_manager_status(tmp_path):
    store = SQLiteConversationStore(str(tmp_path / "memory.db"))
    manager = MemoryManager(store=store, working=WorkingMemory())

    status = manager.status()

    assert status["ready"] is True
    assert status["type"] == "sqlite+working"
    assert "working_items" in status


def test_memory_manager_session_flow(tmp_path):
    store = SQLiteConversationStore(str(tmp_path / "memory.db"))
    manager = MemoryManager(store=store, working=WorkingMemory())

    session = manager.create_session()
    manager.add_user_message(session["id"], "hello")
    manager.add_assistant_message(session["id"], "hi")

    loaded = manager.get_session(session["id"])

    assert len(loaded["messages"]) == 2


def test_memory_manager_working_memory(tmp_path):
    store = SQLiteConversationStore(str(tmp_path / "memory.db"))
    manager = MemoryManager(store=store, working=WorkingMemory())

    manager.set_working("focus", "memory")

    assert manager.get_working("focus")["value"] == "memory"
    assert len(manager.list_working()) == 1
