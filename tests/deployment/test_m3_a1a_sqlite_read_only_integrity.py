from __future__ import annotations

import ast
import sqlite3
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.deployment.audit_contracts import (
    GENESIS_PREVIOUS_HASH,
    AuditEventType,
    create_audit_event,
)
from core.deployment.audit_sqlite import (
    SQLiteAuditPathPolicy,
    SQLiteAuditReadOnlyInspector,
    SQLiteAuditSchemaExpectation,
    SQLiteAuditStatus,
    SQLiteAuditStorageConfig,
)
from core.deployment.contracts import canonical_json_bytes, sha256_digest

NOW = "2026-07-29T12:00:00+09:00"


def policy(tmp_path: Path) -> SQLiteAuditPathPolicy:
    home = tmp_path / "Users" / "operator"
    home.mkdir(parents=True)
    return SQLiteAuditPathPolicy(repository_root=Path.cwd(), user_home=home)


def db_path(tmp_path: Path) -> tuple[SQLiteAuditPathPolicy, Path]:
    value = policy(tmp_path)
    path = value.canonical_future_path
    path.parent.mkdir(parents=True)
    return value, path


def create_db(path: Path, events=(), *, version="dpl/audit-sqlite/v1",
              indexes=True) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        "CREATE TABLE audit_ledger_meta (schema_version TEXT NOT NULL);"
        "CREATE TABLE audit_events (ledger_sequence INTEGER NOT NULL,"
        "event_id TEXT NOT NULL,schema_version TEXT NOT NULL,event_type TEXT NOT NULL,"
        "recorded_at TEXT NOT NULL,actor_identity TEXT NOT NULL,"
        "canonical_payload TEXT NOT NULL,payload_digest TEXT NOT NULL,"
        "previous_event_hash TEXT NOT NULL,event_hash TEXT NOT NULL,"
        "production_authorized INTEGER NOT NULL);"
    )
    if indexes:
        connection.executescript(
            "CREATE UNIQUE INDEX ux_audit_events_event_id ON audit_events(event_id);"
            "CREATE UNIQUE INDEX ux_audit_events_ledger_sequence "
            "ON audit_events(ledger_sequence);"
        )
    connection.execute("INSERT INTO audit_ledger_meta VALUES (?)", (version,))
    for event in events:
        semantic = event.semantic()
        connection.execute(
            "INSERT INTO audit_events VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (event.sequence, event.event_id, "dpl/audit/v1", event.event_type.value,
             event.recorded_at, event.actor_identity,
             canonical_json_bytes(semantic).decode(), sha256_digest(semantic),
             event.previous_event_hash, event.event_hash,
             int(event.production_authorized)),
        )
    connection.commit()
    connection.close()


def events(count=2):
    result = []
    previous = GENESIS_PREVIOUS_HASH
    for sequence in range(1, count + 1):
        event = create_audit_event(
            event_type=AuditEventType.INTEGRITY_VERIFIED, sequence=sequence,
            previous_event_hash=previous, recorded_at=NOW,
            actor_identity="operator", environment="test",
            policy_decision="ALLOW", payload={"result": "safe"},
        )
        result.append(event)
        previous = event.event_hash
    return result


def inspect(path: Path, value: SQLiteAuditPathPolicy):
    return SQLiteAuditReadOnlyInspector(
        config=SQLiteAuditStorageConfig(path), path_policy=value
    ).inspect(inspected_at=NOW)


def codes(report) -> set[str]:
    return {finding.code for finding in report.schema_findings}


def test_immutable_configuration_and_canonical_future_policy(tmp_path):
    value = policy(tmp_path)
    config = SQLiteAuditStorageConfig(value.canonical_future_path)
    assert str(value.canonical_future_path).endswith(
        "Library/Application Support/AIControlCenter/audit/audit-ledger.sqlite3"
    )
    with pytest.raises(FrozenInstanceError):
        config.timeout_seconds = 3


def test_missing_file_is_unavailable_and_never_created(tmp_path):
    value = policy(tmp_path)
    path = value.canonical_future_path
    report = inspect(path, value)
    assert report.status is SQLiteAuditStatus.UNAVAILABLE
    assert not path.exists()
    assert report.writes_performed == report.migrations_performed == report.repairs_performed == 0


@pytest.mark.parametrize("count", [0, 3])
def test_valid_empty_and_multi_event_ledger_is_healthy(tmp_path, count):
    value, path = db_path(tmp_path)
    create_db(path, events(count))
    before = path.read_bytes()
    report = inspect(path, value)
    assert report.status is SQLiteAuditStatus.HEALTHY
    assert report.event_count == count
    assert report.query_only and report.connection_mode == "mode=ro"
    assert report.chain_result == report.privacy_result == "VALID"
    assert path.read_bytes() == before


def test_report_is_deterministic(tmp_path):
    value, path = db_path(tmp_path)
    create_db(path, events())
    first, second = inspect(path, value), inspect(path, value)
    assert first == second
    assert first.canonical_json() == second.canonical_json()
    assert first.report_digest == second.report_digest


def test_schema_mismatch_missing_table_and_missing_index(tmp_path):
    value, path = db_path(tmp_path)
    create_db(path, version="wrong", indexes=False)
    report = inspect(path, value)
    assert {"SCHEMA_VERSION_MISMATCH", "MISSING_INDEX"} <= codes(report)
    path2 = path.with_name("missing.sqlite3")
    connection = sqlite3.connect(path2)
    connection.execute("CREATE TABLE audit_ledger_meta(schema_version TEXT)")
    connection.execute("INSERT INTO audit_ledger_meta VALUES (?)", ("dpl/audit-sqlite/v1",))
    connection.commit()
    connection.close()
    assert "MISSING_TABLE" in codes(inspect(path2, value))


def test_corrupt_sqlite_file(tmp_path):
    value, path = db_path(tmp_path)
    path.write_bytes(b"not sqlite")
    report = inspect(path, value)
    assert report.status is SQLiteAuditStatus.INVALID
    assert "INVALID_SQLITE_HEADER" in codes(report)


def test_duplicate_ids_sequences_and_gap(tmp_path):
    value, path = db_path(tmp_path)
    source = events()
    create_db(path, source, indexes=False)
    connection = sqlite3.connect(path)
    semantic = source[1].semantic()
    connection.execute(
        "INSERT INTO audit_events VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (4, source[0].event_id, "dpl/audit/v1", source[1].event_type.value,
         source[1].recorded_at, source[1].actor_identity,
         canonical_json_bytes(semantic).decode(), sha256_digest(semantic),
         source[1].previous_event_hash, source[1].event_hash, 0),
    )
    connection.execute("UPDATE audit_events SET ledger_sequence=1 WHERE rowid=2")
    connection.commit()
    connection.close()
    report = inspect(path, value)
    assert {"DUPLICATE_EVENT_ID", "DUPLICATE_SEQUENCE",
            "MISSING_SEQUENCE_GAP"} <= codes(report)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("UPDATE audit_events SET previous_event_hash='sha256:broken' WHERE ledger_sequence=2",
         "BROKEN_PREVIOUS_HASH"),
        ("UPDATE audit_events SET event_hash='sha256:invalid' WHERE ledger_sequence=2",
         "MODIFIED_EVENT"),
        ("UPDATE audit_events SET canonical_payload='{}' WHERE ledger_sequence=1",
         "MODIFIED_PAYLOAD"),
    ],
)
def test_chain_and_payload_tampering(tmp_path, mutation, expected):
    value, path = db_path(tmp_path)
    create_db(path, events())
    connection = sqlite3.connect(path)
    connection.execute(mutation)
    connection.commit()
    connection.close()
    assert expected in codes(inspect(path, value))


def test_secret_payload_and_production_authorization_are_redacted(tmp_path):
    value, path = db_path(tmp_path)
    create_db(path, events(1))
    connection = sqlite3.connect(path)
    secret = '{"environment":"test","policy_decision":"ALLOW","payload":{"api_key":"VALUE"}}'
    connection.execute(
        "UPDATE audit_events SET canonical_payload=?,payload_digest=?,"
        "production_authorized=1", (secret, sha256_digest(__import__("json").loads(secret))),
    )
    connection.commit()
    connection.close()
    report = inspect(path, value)
    assert {"SECRET_OR_INVALID_PAYLOAD",
            "PRODUCTION_AUTHORIZED_VIOLATION"} <= codes(report)
    assert "VALUE" not in report.canonical_json()


def test_path_rejections(tmp_path):
    value = policy(tmp_path)
    candidates = [
        Path("relative.sqlite3"),
        Path.cwd() / "audit.sqlite3",
        Path("/System/audit.sqlite3"),
        Path("/Volumes/network/audit.sqlite3"),
        Path("/home/ubuntu/audit.sqlite3"),
    ]
    for path in candidates:
        assert inspect(path, value).status is SQLiteAuditStatus.BLOCKED


def test_symlink_database_and_parent_rejected(tmp_path):
    value, real = db_path(tmp_path)
    create_db(real)
    link = real.with_name("link.sqlite3")
    link.symlink_to(real)
    assert "SYMLINK_PATH_COMPONENT" in codes(inspect(link, value))
    real_parent = value.user_home / "real"
    real_parent.mkdir()
    linked_parent = value.user_home / "Library" / "Application Support" / "linked"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    assert "SYMLINK_PATH_COMPONENT" in value.validate(linked_parent / "audit.sqlite3")


def test_expected_schema_is_pure_and_runtime_has_no_forbidden_capability():
    schema = SQLiteAuditSchemaExpectation()
    assert schema.append_only and schema.immutable_events
    sources = list((Path("core/deployment/audit_sqlite")).glob("*.py"))
    text = "\n".join(source.read_text() for source in sources)
    assert "mode=ro" in text and "PRAGMA query_only=ON" in text
    assert not any(term in text for term in (
        "subprocess", "socket", "requests", "paramiko", "core.api",
        "core.worker", "UbuntuWorkerClient", "DurableAuditPort",
    ))
    inspector_tree = ast.parse(Path(
        "core/deployment/audit_sqlite/inspector.py"
    ).read_text())
    calls = [node for node in ast.walk(inspector_tree) if isinstance(node, ast.Call)]
    assert not any(
        isinstance(call.func, ast.Attribute) and call.func.attr in {
            "executescript", "commit", "rollback"
        } for call in calls
    )
    assert all(word not in Path(
        "core/deployment/audit_sqlite/inspector.py"
    ).read_text().upper() for word in (
        "CREATE TABLE", "ALTER TABLE", "DROP TABLE", "PRAGMA JOURNAL_MODE="
    ))
