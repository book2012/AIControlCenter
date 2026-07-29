from __future__ import annotations

import ast
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.deployment.audit_contracts import (
    GENESIS_PREVIOUS_HASH,
    AuditAppendRequest,
    AuditEventType,
    create_audit_event,
)
from core.deployment.audit_sqlite import (
    SQLiteAuditPathPolicy,
    SQLiteAuditReadOnlyInspector,
    SQLiteAuditStatus,
    SQLiteAuditStorageConfig,
)
from core.deployment.audit_sqlite_writer import (
    SQLiteAuditAppendStatus,
    SQLiteAuditSchemaDefinition,
    SQLiteAuditWriter,
    SQLiteAuditWriterConfig,
    SQLiteAuditWriterError,
)
from core.deployment.policy import validate_dependency_boundaries

NOW = "2026-07-29T12:00:00+09:00"


def path_policy(tmp_path: Path) -> SQLiteAuditPathPolicy:
    home = tmp_path / "Users" / "operator"
    home.mkdir(parents=True)
    return SQLiteAuditPathPolicy(repository_root=Path.cwd(), user_home=home)


def bootstrap(tmp_path: Path, **changes) -> tuple[SQLiteAuditPathPolicy, Path]:
    policy = path_policy(tmp_path)
    path = policy.canonical_future_path
    path.parent.mkdir(parents=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=WAL")
    ddl = SQLiteAuditSchemaDefinition().ddl_for_test_bootstrap()
    if changes.get("missing_trigger"):
        ddl = ddl.replace(
            "CREATE TRIGGER trg_audit_events_no_delete BEFORE DELETE ON audit_events\n"
            "BEGIN SELECT RAISE(ABORT, 'audit_events are append-only'); END;", ""
        )
    if changes.get("missing_index"):
        ddl = ddl.replace(
            "CREATE UNIQUE INDEX ux_audit_events_event_id ON audit_events(event_id);", ""
        )
    if changes.get("missing_table"):
        ddl = "CREATE TABLE audit_ledger_meta (schema_version TEXT NOT NULL);"
    connection.executescript(ddl)
    connection.execute(
        "INSERT INTO audit_ledger_meta VALUES (?)",
        (changes.get("version", "dpl/audit-sqlite/v1"),),
    )
    connection.commit()
    connection.close()
    return policy, path


def writer(policy: SQLiteAuditPathPolicy, path: Path) -> SQLiteAuditWriter:
    return SQLiteAuditWriter(
        config=SQLiteAuditWriterConfig(path), path_policy=policy
    )


def event(sequence: int, previous: str, **changes):
    values = dict(
        event_type=AuditEventType.INTEGRITY_VERIFIED,
        sequence=sequence,
        previous_event_hash=previous,
        recorded_at=NOW,
        actor_identity="operator",
        environment="test",
        policy_decision="ALLOW",
        payload={"result": "safe"},
    )
    values.update(changes)
    return create_audit_event(**values)


def request(value):
    return AuditAppendRequest(
        event=value, expected_previous_hash=value.previous_event_hash
    )


def count(path: Path) -> int:
    connection = sqlite3.connect(path)
    try:
        return int(connection.execute("SELECT count(*) FROM audit_events").fetchone()[0])
    finally:
        connection.close()


def test_config_is_immutable_and_path_is_explicit(tmp_path):
    with pytest.raises((TypeError, ValueError)):
        SQLiteAuditWriterConfig()  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        SQLiteAuditWriterConfig(Path("relative.sqlite3"))
    config = SQLiteAuditWriterConfig(tmp_path / "ledger.sqlite3")
    with pytest.raises(FrozenInstanceError):
        config.timeout_seconds = 3


def test_missing_database_and_directory_are_never_created(tmp_path):
    policy = path_policy(tmp_path)
    path = policy.canonical_future_path
    with pytest.raises(SQLiteAuditWriterError) as raised:
        writer(policy, path).append(request(event(1, GENESIS_PREVIOUS_HASH)))
    assert raised.value.status is SQLiteAuditAppendStatus.UNAVAILABLE
    assert not path.exists() and not path.parent.exists()


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"version": "wrong"}, "SCHEMA_VERSION_MISMATCH"),
        ({"missing_table": True}, "MISSING_TABLE"),
        ({"missing_index": True}, "MISSING_INDEX"),
        ({"missing_trigger": True}, "MISSING_APPEND_ONLY_TRIGGER"),
    ],
)
def test_schema_is_validated_default_deny(tmp_path, change, code):
    policy, path = bootstrap(tmp_path, **change)
    report = writer(policy, path).validate_schema()
    assert not report.valid and code in report.reason_codes


def test_non_wal_database_is_denied_without_migration(tmp_path):
    policy, path = bootstrap(tmp_path)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=DELETE")
    connection.close()
    with pytest.raises(SQLiteAuditWriterError) as raised:
        writer(policy, path).append(request(event(1, GENESIS_PREVIOUS_HASH)))
    assert raised.value.code == "JOURNAL_MODE_NOT_WAL"
    connection = sqlite3.connect(path)
    assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    connection.close()


def test_genesis_chain_monotonic_hashes_receipt_and_read_only_compatibility(tmp_path):
    policy, path = bootstrap(tmp_path)
    first = event(1, GENESIS_PREVIOUS_HASH)
    receipt1 = writer(policy, path).append(request(first))
    second = event(2, first.event_hash, payload={"result": "second"})
    receipt2 = writer(policy, path).append(request(second))
    assert receipt1.status is SQLiteAuditAppendStatus.COMMITTED
    assert receipt1.writes_performed == 1 and receipt1.transaction_committed
    assert receipt2.ledger_sequence == 2
    assert receipt2.previous_event_hash == receipt1.event_hash
    assert receipt2.payload_digest.startswith("sha256:")
    assert receipt2.event_hash == second.event_hash
    assert receipt1.database_path_identity_digest == policy.identity_digest(path)
    assert str(path) not in repr(receipt1)
    report = SQLiteAuditReadOnlyInspector(
        config=SQLiteAuditStorageConfig(path), path_policy=policy
    ).inspect(inspected_at=NOW)
    assert report.status is SQLiteAuditStatus.HEALTHY
    assert report.event_count == 2 and report.chain_result == "VALID"


def test_receipt_is_deterministic_and_identical_duplicate_is_idempotent(tmp_path):
    policy, path = bootstrap(tmp_path)
    value = event(1, GENESIS_PREVIOUS_HASH)
    first = writer(policy, path).append(request(value))
    retry = writer(policy, path).append(request(value))
    retry2 = writer(policy, path).append(request(value))
    assert retry == retry2
    assert retry.idempotent_retry and retry.writes_performed == 0
    assert retry.status is SQLiteAuditAppendStatus.IDEMPOTENT
    assert first.event_id == retry.event_id and count(path) == 1


def test_conflicting_duplicate_and_position_mismatch_roll_back(tmp_path):
    policy, path = bootstrap(tmp_path)
    first = event(1, GENESIS_PREVIOUS_HASH)
    writer(policy, path).append(request(first))
    conflict = AuditAppendRequest(first, expected_previous_hash="sha256:conflict")
    with pytest.raises(SQLiteAuditWriterError) as raised:
        writer(policy, path).append(conflict)
    assert raised.value.code == "DUPLICATE_EVENT_CONFLICT"
    wrong = event(3, first.event_hash)
    with pytest.raises(SQLiteAuditWriterError):
        writer(policy, path).append(request(wrong))
    assert count(path) == 1


def test_update_delete_database_protections(tmp_path):
    policy, path = bootstrap(tmp_path)
    writer(policy, path).append(request(event(1, GENESIS_PREVIOUS_HASH)))
    connection = sqlite3.connect(path)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("UPDATE audit_events SET actor_identity='other'")
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("DELETE FROM audit_events")
    connection.close()
    assert count(path) == 1


def test_tampered_existing_payload_and_chain_are_not_repaired(tmp_path):
    policy, path = bootstrap(tmp_path)
    first = event(1, GENESIS_PREVIOUS_HASH)
    writer(policy, path).append(request(first))
    connection = sqlite3.connect(path)
    connection.execute("DROP TRIGGER trg_audit_events_no_update")
    connection.execute(
        "UPDATE audit_events SET canonical_payload='{}' WHERE ledger_sequence=1"
    )
    connection.execute(
        "CREATE TRIGGER trg_audit_events_no_update BEFORE UPDATE ON audit_events "
        "BEGIN SELECT RAISE(ABORT, 'audit_events are append-only'); END"
    )
    connection.commit()
    connection.close()
    before = path.read_bytes()
    with pytest.raises(SQLiteAuditWriterError) as raised:
        writer(policy, path).append(request(event(2, first.event_hash)))
    assert raised.value.code == "MODIFIED_EXISTING_PAYLOAD"
    assert count(path) == 1
    assert path.read_bytes() == before


def test_insert_failure_rolls_back_without_partial_event(tmp_path):
    policy, path = bootstrap(tmp_path)
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TRIGGER reject_insert BEFORE INSERT ON audit_events "
        "BEGIN SELECT RAISE(ABORT, 'test rejection'); END"
    )
    connection.commit()
    connection.close()
    with pytest.raises(SQLiteAuditWriterError) as raised:
        writer(policy, path).append(request(event(1, GENESIS_PREVIOUS_HASH)))
    assert raised.value.code == "APPEND_TRANSACTION_FAILED"
    assert count(path) == 0


def test_concurrent_genesis_append_is_serialized_with_one_winner(tmp_path):
    policy, path = bootstrap(tmp_path)
    requests = (
        request(event(1, GENESIS_PREVIOUS_HASH, payload={"candidate": "a"})),
        request(event(1, GENESIS_PREVIOUS_HASH, payload={"candidate": "b"})),
    )

    def attempt(value):
        try:
            return writer(policy, path).append(value).status.value
        except SQLiteAuditWriterError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = tuple(executor.map(attempt, requests))
    assert outcomes.count("COMMITTED") == 1
    assert outcomes.count("APPEND_POSITION_MISMATCH") == 1
    assert count(path) == 1


def test_secret_production_and_unknown_events_are_rejected_before_write(tmp_path):
    policy, path = bootstrap(tmp_path)
    for changes in (
        {"payload": {"access_token": "redacted"}},
        {"payload": {"shell": "redacted"}},
        {"production_authorized": True},
        {"event_type": "UNKNOWN"},
    ):
        with pytest.raises(Exception):
            event(1, GENESIS_PREVIOUS_HASH, **changes)
    assert count(path) == 0


def test_symlink_repository_protected_network_and_no_forbidden_dependencies(tmp_path):
    policy, path = bootstrap(tmp_path)
    link = path.with_name("link.sqlite3")
    link.symlink_to(path)
    with pytest.raises(SQLiteAuditWriterError):
        writer(policy, link).append(request(event(1, GENESIS_PREVIOUS_HASH)))
    for candidate in (
        Path.cwd() / "audit.sqlite3",
        Path("/System/audit.sqlite3"),
        Path("/Volumes/network/audit.sqlite3"),
        Path("/home/ubuntu/audit.sqlite3"),
    ):
        assert policy.validate(candidate)
    sources = tuple(Path("core/deployment/audit_sqlite_writer").glob("*.py"))
    text = "\n".join(source.read_text() for source in sources)
    assert "mode=rw" in text and "mode=rwc" not in text
    tree = ast.parse(text)
    imports = {
        node.names[0].name if isinstance(node, ast.Import) else node.module
        for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
    }
    assert not any(str(value).startswith((
        "subprocess", "socket", "requests", "paramiko", "core.api", "core.worker"
    )) for value in imports)
    assert validate_dependency_boundaries(
        repository_root=Path.cwd()
    )["overall_result"] == "PASS"
