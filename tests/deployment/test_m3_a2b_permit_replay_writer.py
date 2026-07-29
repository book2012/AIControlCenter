from __future__ import annotations

import ast
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.deployment.permit_replay_sqlite import (
    PermitReplayPathPolicy,
    PermitReplaySchemaExpectation,
)
from core.deployment.permit_replay_sqlite_writer import (
    PermitReplayWriteStatus,
    PermitReplayWriterConfig,
    PermitReservationRequest,
    PermitTerminalRequest,
    PermitTerminalState,
    SQLitePermitReplayRegistry,
)

NOW = "2026-07-29T12:00:00+09:00"
LATER = "2026-07-29T13:00:00+09:00"
EXPIRES = "2026-07-30T12:00:00+09:00"


def policy(tmp_path: Path) -> PermitReplayPathPolicy:
    home = tmp_path / "Users" / "operator"
    home.mkdir(parents=True)
    return PermitReplayPathPolicy(Path.cwd(), home)


def location(tmp_path: Path) -> tuple[PermitReplayPathPolicy, Path]:
    value = policy(tmp_path)
    path = value.canonical_future_path
    path.parent.mkdir(parents=True)
    return value, path


def create_db(path: Path, *, wal: bool = True, indexes: bool = True) -> None:
    schema = PermitReplaySchemaExpectation()
    connection = sqlite3.connect(path)
    connection.executescript(schema.schema_sql_for_documentation())
    connection.execute("INSERT INTO permit_replay_meta VALUES (?)", (schema.schema_version,))
    if not indexes:
        connection.execute("DROP INDEX ux_permit_use_events_one_terminal")
    connection.commit()
    if wal:
        assert connection.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
    connection.commit()
    connection.close()


def reservation(**changes) -> PermitReservationRequest:
    values = {
        "permit_id": "permit-1", "permit_digest": "sha256:permit",
        "activation_id": "activation-1",
        "activation_request_digest": "sha256:activation",
        "package_digest": "sha256:package", "plan_digest": "sha256:plan",
        "readiness_report_id": "readiness-1",
        "readiness_report_digest": "sha256:readiness",
        "target_identity": "mac-test-sandbox", "environment": "test",
        "sandbox_root_identity_digest": "sha256:sandbox",
        "requester_identity": "requester", "operator_identity": "operator",
        "approver_identity": "approver", "reserved_at": NOW,
        "expires_at": EXPIRES, "production_authorized": False,
    }
    values.update(changes)
    return PermitReservationRequest(**values)


def terminal(state=PermitTerminalState.CONSUMED, **changes) -> PermitTerminalRequest:
    values = {
        "permit_id": "permit-1", "permit_digest": "sha256:permit",
        "activation_id": "activation-1",
        "activation_request_digest": "sha256:activation",
        "target_identity": "mac-test-sandbox", "environment": "test",
        "terminal_state": state, "event_at": LATER, "actor_identity": "operator",
        "production_authorized": False,
    }
    values.update(changes)
    return PermitTerminalRequest(**values)


def registry(tmp_path: Path, *, wal=True, indexes=True):
    value, path = location(tmp_path)
    create_db(path, wal=wal, indexes=indexes)
    return SQLitePermitReplayRegistry(
        config=PermitReplayWriterConfig(path), path_policy=value
    ), path


def events(path: Path):
    connection = sqlite3.connect(path)
    try:
        return connection.execute(
            "SELECT ledger_sequence,event_id,event_type,previous_event_hash,event_hash "
            "FROM permit_use_events ORDER BY ledger_sequence"
        ).fetchall()
    finally:
        connection.close()


def test_immutable_contracts_and_explicit_configuration(tmp_path):
    value = policy(tmp_path)
    config = PermitReplayWriterConfig(value.canonical_future_path)
    with pytest.raises(FrozenInstanceError):
        config.busy_timeout_seconds = 4
    with pytest.raises((TypeError, ValueError)):
        SQLitePermitReplayRegistry(config=None, path_policy=value)


def test_missing_database_and_directory_remain_missing(tmp_path):
    value = policy(tmp_path)
    path = value.canonical_future_path
    writer = SQLitePermitReplayRegistry(
        config=PermitReplayWriterConfig(path), path_policy=value
    )
    report, receipt = writer.reserve(reservation())
    assert report.status is PermitReplayWriteStatus.UNAVAILABLE and receipt is None
    assert not path.exists() and not path.parent.exists()


def test_first_reservation_exact_binding_receipt_and_idempotency(tmp_path):
    writer, path = registry(tmp_path)
    first_report, first = writer.reserve(reservation())
    retry_report, retry = writer.reserve(reservation())
    assert first_report.status is PermitReplayWriteStatus.COMMITTED
    assert retry_report.status is PermitReplayWriteStatus.IDEMPOTENT
    assert first and retry and first.event_hash == retry.event_hash
    assert not first.idempotent_retry and retry.idempotent_retry
    assert first.transaction_committed and not first.production_authorized
    assert str(path) not in str(first.as_dict())
    assert len(events(path)) == 1
    denied, receipt = writer.reserve(reservation(plan_digest="sha256:changed"))
    assert denied.status is PermitReplayWriteStatus.DENIED and receipt is None
    assert len(events(path)) == 1


@pytest.mark.parametrize("state", list(PermitTerminalState))
def test_terminal_transitions_and_idempotency(tmp_path, state):
    writer, path = registry(tmp_path)
    writer.reserve(reservation())
    report, receipt = writer.transition_terminal(terminal(state))
    retry_report, retry = writer.transition_terminal(terminal(state))
    assert report.status is PermitReplayWriteStatus.COMMITTED
    assert retry_report.status is PermitReplayWriteStatus.IDEMPOTENT
    assert receipt and retry and retry.idempotent_retry
    assert [row[2] for row in events(path)] == ["RESERVED", state.value]


def test_terminal_without_reservation_changed_binding_and_conflict(tmp_path):
    writer, path = registry(tmp_path)
    report, _ = writer.transition_terminal(terminal())
    assert report.status is PermitReplayWriteStatus.DENIED
    writer.reserve(reservation())
    report, _ = writer.transition_terminal(terminal(activation_id="other"))
    assert report.status is PermitReplayWriteStatus.DENIED
    writer.transition_terminal(terminal(PermitTerminalState.FAILED_CLOSED))
    report, _ = writer.transition_terminal(terminal(PermitTerminalState.CONSUMED))
    assert report.status is PermitReplayWriteStatus.DENIED
    assert len(events(path)) == 2


def test_non_wal_schema_and_expiry_are_denied_without_partial_record(tmp_path):
    writer, path = registry(tmp_path, wal=False)
    report, _ = writer.reserve(reservation())
    assert report.status is PermitReplayWriteStatus.BLOCKED
    assert events(path) == []
    value, other = location(tmp_path / "other")
    create_db(other, indexes=False)
    writer = SQLitePermitReplayRegistry(
        config=PermitReplayWriterConfig(other), path_policy=value
    )
    assert writer.reserve(reservation())[0].status is PermitReplayWriteStatus.BLOCKED
    writer, path = registry(tmp_path / "expired")
    assert writer.reserve(reservation(expires_at=NOW))[0].status is PermitReplayWriteStatus.DENIED
    assert events(path) == []


@pytest.mark.parametrize("changes", [
    {"environment": "production"}, {"production_authorized": True},
    {"target_identity": "ubuntu-worker"}, {"operator_identity": "raw-nonce"},
])
def test_production_ubuntu_and_secret_bearing_content_denied(tmp_path, changes):
    writer, path = registry(tmp_path)
    report, _ = writer.reserve(reservation(**changes))
    assert report.status is PermitReplayWriteStatus.DENIED
    assert events(path) == []


def test_path_policy_rejections_and_no_creation(tmp_path):
    value = policy(tmp_path)
    for path in (Path("relative.sqlite3"), Path.cwd() / "state.sqlite3",
                 Path("/home/ubuntu/state.sqlite3"), Path("/Volumes/net/state.sqlite3")):
        writer = SQLitePermitReplayRegistry(
            config=PermitReplayWriterConfig(path), path_policy=value
        )
        assert writer.reserve(reservation())[0].status is PermitReplayWriteStatus.BLOCKED
        assert not path.exists()


def test_hash_chain_monotonic_sequence_and_tamper_denial(tmp_path):
    writer, path = registry(tmp_path)
    writer.reserve(reservation())
    writer.transition_terminal(terminal())
    rows = events(path)
    assert [row[0] for row in rows] == [1, 2]
    assert rows[1][3] == rows[0][4]
    connection = sqlite3.connect(path)
    connection.execute("DROP TRIGGER trg_permit_use_events_no_update")
    connection.execute("UPDATE permit_use_events SET event_hash='tampered' WHERE ledger_sequence=1")
    connection.commit()
    connection.close()
    report, _ = writer.reserve(reservation(permit_id="permit-2"))
    assert report.status in (PermitReplayWriteStatus.BLOCKED, PermitReplayWriteStatus.INVALID)
    assert len(events(path)) == 2


def test_concurrent_identical_and_conflicting_reservations(tmp_path):
    writer, path = registry(tmp_path)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: writer.reserve(reservation()), range(8)))
    assert sum(report.status is PermitReplayWriteStatus.COMMITTED for report, _ in results) == 1
    assert sum(report.status is PermitReplayWriteStatus.IDEMPOTENT for report, _ in results) == 7
    assert len(events(path)) == 1
    writer, path = registry(tmp_path / "conflict")
    requests = [reservation(plan_digest=f"sha256:plan-{index}") for index in range(8)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(writer.reserve, requests))
    assert sum(report.status is PermitReplayWriteStatus.COMMITTED for report, _ in results) == 1
    assert all(report.status in (PermitReplayWriteStatus.COMMITTED,
                                PermitReplayWriteStatus.DENIED) for report, _ in results)
    assert len(events(path)) == 1


def test_concurrent_terminal_transitions_exactly_one_wins(tmp_path):
    writer, path = registry(tmp_path)
    writer.reserve(reservation())
    requests = [terminal(PermitTerminalState.CONSUMED),
                terminal(PermitTerminalState.FAILED_CLOSED)] * 4
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(writer.transition_terminal, requests))
    assert sum(report.status is PermitReplayWriteStatus.COMMITTED for report, _ in results) == 1
    assert len(events(path)) == 2
    assert len({row[0] for row in events(path)}) == 2
    assert len({row[1] for row in events(path)}) == 2


def test_writer_has_rw_only_and_no_bootstrap_network_worker_or_api_dependency():
    root = Path("core/deployment/permit_replay_sqlite_writer")
    source = "\n".join(path.read_text() for path in root.glob("*.py"))
    tree = ast.parse(source)
    imports = {
        node.names[0].name if isinstance(node, ast.Import) else node.module
        for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
    }
    assert "mode=rw" in source and "mode=rwc" not in source
    assert not any(str(value).startswith((
        "subprocess", "socket", "requests", "paramiko", "core.api", "core.worker",
        "core.deployment.audit_sqlite_writer",
    )) for value in imports)
    upper = source.upper()
    assert "CREATE TABLE" not in upper and "PRAGMA JOURNAL_MODE=" not in upper
