from pathlib import Path
import sqlite3

import pytest

from core.shopping.product_drafts.persistence import (
    APPLICATION_ID, SCHEMA_VERSION, ShoppingDatabaseError, connect_database,
    IsolatedTestDatabasePathPolicy, initialize_database, inspect_database, validate_database,
    validate_durable_database_path,
)


def test_explicit_schema_has_shopping_identity_durability_and_required_objects(tmp_path: Path):
    path = tmp_path / "drafts.sqlite3"
    policy = IsolatedTestDatabasePathPolicy(tmp_path)
    assert not path.exists()
    initialize_database(path, applied_at="2026-08-11T00:00:00Z", path_policy=policy)
    connection = connect_database(path, path_policy=policy)
    try:
        status = inspect_database(connection)
        assert (status.application_id, status.user_version) == (APPLICATION_ID, SCHEMA_VERSION)
        assert status.journal_mode == "WAL" and status.foreign_keys_enabled
        assert status.quick_check == "ok"
        assert {"schema_metadata", "product_draft_revisions",
                "product_draft_generation_operations",
                "product_draft_generation_audit_events"}.issubset(status.objects)
        assert connection.execute("PRAGMA synchronous").fetchone()[0] == 2
    finally:
        connection.close()
    reader = connect_database(path, read_only=True)
    try:
        assert reader.execute("PRAGMA query_only").fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError):
            reader.execute("DELETE FROM schema_metadata")
    finally: reader.close()


def test_unknown_database_and_unsafe_durable_paths_fail_closed(tmp_path: Path):
    path = tmp_path / "foreign.sqlite3"
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA application_id=123")
    connection.close()
    with pytest.raises(ShoppingDatabaseError, match="another application"):
        initialize_database(path, path_policy=IsolatedTestDatabasePathPolicy(tmp_path))
    with pytest.raises(ValueError): validate_durable_database_path("relative.sqlite3")
    with pytest.raises(ValueError): validate_durable_database_path("/private/tmp/drafts.sqlite3")
    with pytest.raises(ValueError): validate_durable_database_path("/home/ubuntu/drafts.sqlite3")


@pytest.mark.parametrize("kind", ["trigger", "index", "table"])
def test_same_name_schema_tampering_is_detected(tmp_path: Path, kind: str):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path)
    initialize_database(path, path_policy=policy)
    connection = connect_database(path, path_policy=policy)
    try:
        if kind == "trigger":
            connection.execute("DROP TRIGGER product_draft_generation_audit_deny_delete")
            connection.execute("CREATE TRIGGER product_draft_generation_audit_deny_delete BEFORE DELETE ON product_draft_generation_audit_events BEGIN SELECT 1; END")
        elif kind == "index":
            connection.execute("DROP INDEX product_draft_revisions_current")
            connection.execute("CREATE INDEX product_draft_revisions_current ON product_draft_revisions(revision_id)")
        else:
            connection.execute("ALTER TABLE schema_metadata RENAME TO old_metadata")
            connection.execute("CREATE TABLE schema_metadata(schema_version INTEGER PRIMARY KEY, applied_at TEXT, component TEXT)")
            connection.execute("INSERT INTO schema_metadata SELECT * FROM old_metadata")
            connection.execute("DROP TABLE old_metadata")
        with pytest.raises(ShoppingDatabaseError, match="schema_definitions"):
            validate_database(connection)
    finally: connection.close()


def test_read_only_validation_rejects_non_wal_without_changing_mode(tmp_path: Path):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path)
    initialize_database(path, path_policy=policy)
    connection = connect_database(path, path_policy=policy)
    connection.execute("PRAGMA journal_mode=DELETE"); connection.close()
    reader = connect_database(path, read_only=True)
    try:
        with pytest.raises(ShoppingDatabaseError, match="journal_mode"):
            validate_database(reader)
        assert reader.execute("PRAGMA journal_mode").fetchone()[0].upper() == "DELETE"
    finally: reader.close()
