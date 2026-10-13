import sqlite3
import pytest
from core.shopping.sqlite_resource import connection


def test_transaction_commits_and_closes_even_when_reference_is_retained(tmp_path):
    path = tmp_path / "store.sqlite3"
    retained = []
    for index in range(300):
        with connection(path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS values_table(value INTEGER)")
            conn.execute("INSERT INTO values_table VALUES(?)", (index,))
            retained.append(conn)
    for conn in retained:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            conn.execute("SELECT 1")
    with connection(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM values_table").fetchone()[0] == 300


def test_transaction_rolls_back_and_closes_after_error(tmp_path):
    path = tmp_path / "store.sqlite3"
    with connection(path) as conn:
        conn.execute("CREATE TABLE values_table(value INTEGER)")
    with pytest.raises(RuntimeError):
        with connection(path) as conn:
            conn.execute("INSERT INTO values_table VALUES(1)")
            raise RuntimeError("abort")
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        conn.execute("SELECT 1")
    with connection(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM values_table").fetchone()[0] == 0
