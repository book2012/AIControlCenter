from core.memory.sqlite_store import SQLiteConversationStore


class MemoryManager:
    def __init__(self, store: SQLiteConversationStore | None = None):
        self.store = store or SQLiteConversationStore()

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

    def status(self):
        sessions = self.list_sessions()

        return {
            "type": "sqlite",
            "sessions": len(sessions),
            "ready": True,
        }
