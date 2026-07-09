import sqlite3
from pathlib import Path
from uuid import uuid4
from datetime import datetime


class SQLiteConversationStore:
    def __init__(self, db_path: str = "data/conversations.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    created TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created TEXT NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
                )
            """)

    def create_session(self):
        session_id = str(uuid4())
        created = datetime.utcnow().isoformat()

        with self._connect() as conn:
            conn.execute(
                "INSERT INTO conversations (id, created) VALUES (?, ?)",
                (session_id, created),
            )

        return {
            "id": session_id,
            "created": created,
            "messages": [],
        }

    def add_message(self, session_id: str, role: str, content: str):
        message = {
            "id": str(uuid4()),
            "conversation_id": session_id,
            "role": role,
            "content": content,
            "created": datetime.utcnow().isoformat(),
        }

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO messages
                (id, conversation_id, role, content, created)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    message["id"],
                    message["conversation_id"],
                    message["role"],
                    message["content"],
                    message["created"],
                ),
            )

        return message

    def get_session(self, session_id: str):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, created FROM conversations WHERE id = ?",
                (session_id,),
            ).fetchone()

            if not row:
                raise KeyError(session_id)

            messages = conn.execute(
                """
                SELECT role, content, created
                FROM messages
                WHERE conversation_id = ?
                ORDER BY created ASC
                """,
                (session_id,),
            ).fetchall()

        return {
            "id": row[0],
            "created": row[1],
            "messages": [
                {
                    "role": role,
                    "content": content,
                    "timestamp": created,
                }
                for role, content, created in messages
            ],
        }

    def list_sessions(self):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, created FROM conversations ORDER BY created DESC"
            ).fetchall()

        return [
            self.get_session(session_id)
            for session_id, _ in rows
        ]
