import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from core.runtime.data_paths import resolve_data_path


DEFAULT_FRESHNESS_SECONDS = 90


def classify_heartbeat(
    latest: dict | None,
    freshness_seconds: int = DEFAULT_FRESHNESS_SECONDS,
    now: datetime | None = None,
):
    """Classify a previously read heartbeat without touching its store."""
    if latest is None:
        return {
            "status": "MISSING",
            "fresh": False,
            "freshness_seconds": freshness_seconds,
            "age_seconds": None,
            "latest": None,
        }

    try:
        created = datetime.fromisoformat(latest["created"])
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        observed_at = now or datetime.now(timezone.utc)
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        age = observed_at - created
        age_seconds = age.total_seconds()
        fresh = (
            latest.get("status") == "ALIVE"
            and age >= timedelta(0)
            and age <= timedelta(seconds=freshness_seconds)
        )
    except (KeyError, TypeError, ValueError):
        age_seconds = None
        fresh = False

    return {
        "status": "ALIVE" if fresh else "STALE",
        "fresh": fresh,
        "freshness_seconds": freshness_seconds,
        "age_seconds": age_seconds,
        "latest": latest,
    }


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
