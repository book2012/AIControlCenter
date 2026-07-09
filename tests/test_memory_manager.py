from core.memory.manager import MemoryManager
from core.memory.sqlite_store import SQLiteConversationStore


def test_memory_manager_status(tmp_path):
    store = SQLiteConversationStore(str(tmp_path / "memory.db"))
    manager = MemoryManager(store)

    status = manager.status()

    assert status["ready"] is True
    assert status["type"] == "sqlite"


def test_memory_manager_session_flow(tmp_path):
    store = SQLiteConversationStore(str(tmp_path / "memory.db"))
    manager = MemoryManager(store)

    session = manager.create_session()
    manager.add_user_message(session["id"], "hello")
    manager.add_assistant_message(session["id"], "hi")

    loaded = manager.get_session(session["id"])

    assert len(loaded["messages"]) == 2
