"""Short-lived SQLite transactions with deterministic connection cleanup."""
from contextlib import contextmanager
import sqlite3


@contextmanager
def connection(*args, **kwargs):
    """Preserve SQLite commit/rollback semantics and always close the handle."""
    conn = sqlite3.connect(*args, **kwargs)
    try:
        with conn:
            yield conn
    finally:
        conn.close()
