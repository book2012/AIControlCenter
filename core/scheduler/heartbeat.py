import sqlite3
from datetime import datetime
from pathlib import Path
from core.runtime.data_paths import resolve_data_path


class HeartbeatStore:
    def __init__(self, db_path: str | None = None):
        self.db_path = (
            Path(db_path)
            if db_path is not None
            else resolve_data_path(
                "scheduler.db"
            )
        )

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS heartbeat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT NOT NULL,
                    created TEXT NOT NULL
                )
            """)

    def beat(self, status: str = "ALIVE"):
        self._init_db()
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
        if not self.db_path.is_file():
            return None
        try:
            uri = f"file:{self.db_path.resolve()}?mode=ro"
            with sqlite3.connect(uri, uri=True) as conn:
                row = conn.execute(
                    """
                    SELECT status, created
                    FROM heartbeat
                    ORDER BY id DESC
                    LIMIT 1
                    """
                ).fetchone()
        except sqlite3.Error:
            return None

        if not row:
            return None

        return {
            "status": row[0],
            "created": row[1],
        }
