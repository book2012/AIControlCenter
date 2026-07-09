import sqlite3
from datetime import datetime
from pathlib import Path


class HeartbeatStore:
    def __init__(self, db_path: str = "data/scheduler.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS heartbeat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT NOT NULL,
                    created TEXT NOT NULL
                )
            """)

    def beat(self, status: str = "ALIVE"):
        created = datetime.utcnow().isoformat()

        with self._connect() as conn:
            conn.execute(
                "INSERT INTO heartbeat (status, created) VALUES (?, ?)",
                (status, created),
            )

        return {
            "status": status,
            "created": created,
        }

    def latest(self):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT status, created
                FROM heartbeat
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()

        if not row:
            return None

        return {
            "status": row[0],
            "created": row[1],
        }
