from core.memory.long_term import LongTermMemory
from core.memory.sqlite_store import SQLiteConversationStore
from core.memory.working import WorkingMemory


class MemoryManager:
    def __init__(
        self,
        store: SQLiteConversationStore | None = None,
        working: WorkingMemory | None = None,
        long_term: LongTermMemory | None = None,
    ):
        self.store = store or SQLiteConversationStore()
        self.working = working or WorkingMemory()
        self.long_term = long_term or LongTermMemory()

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

    def add_long_term(self, content: str, source: str = "manual", metadata: dict | None = None):
        return self.long_term.add(content, source=source, metadata=metadata)

    def get_long_term(self, item_id: str):
        return self.long_term.get(item_id)

    def list_long_term(self):
        return self.long_term.list()

    def search_long_term(self, query: str):
        return self.long_term.search(query)

    def status(self):
        sessions = self.list_sessions()
        working = self.working.status()
        long_term = self.long_term.status()

        return {
            "type": "sqlite+working+long_term",
            "sessions": len(sessions),
            "working_items": working["items"],
            "long_term_items": long_term["items"],
            "ready": True,
        }
