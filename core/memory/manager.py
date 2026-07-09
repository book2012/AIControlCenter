from core.memory.sqlite_store import SQLiteConversationStore
from core.memory.working import WorkingMemory


class MemoryManager:
    def __init__(
        self,
        store: SQLiteConversationStore | None = None,
        working: WorkingMemory | None = None,
    ):
        self.store = store or SQLiteConversationStore()
        self.working = working or WorkingMemory()

    def create_session(self):
        return self.store.create_session()

    def add_user_message(self, session_id: str, content: str):
        return self.store.add_message(session_id, "user", content)

    def add_assistant_message(self, session_id: str, content: str):
        return self.store.add_message(session_id, "assistant", content)

    def get_session(self, session_id: str):
        return self.store.get_session(session_id)

    def list_sessions(self):
        return self.store.list_sessions()

    def set_working(self, key: str, value):
        return self.working.set(key, value)

    def get_working(self, key: str):
        return self.working.get(key)

    def list_working(self):
        return self.working.list()

    def status(self):
        sessions = self.list_sessions()
        working = self.working.status()

        return {
            "type": "sqlite+working",
            "sessions": len(sessions),
            "working_items": working["items"],
            "ready": True,
        }
