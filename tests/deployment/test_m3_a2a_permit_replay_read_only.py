from __future__ import annotations

import ast
import json
import sqlite3
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.deployment.contracts import canonical_json_bytes, sha256_digest
from core.deployment.permit_replay_sqlite import (
    PermitReplayPathPolicy,
    PermitReplayReadOnlyInspector,
    PermitReplaySchemaExpectation,
    PermitReplayStatus,
    PermitReplayStorageConfig,
    PermitUseState,
)
from core.deployment.policy import validate_dependency_boundaries

NOW = "2026-07-29T12:00:00+09:00"
FIELDS = PermitReplaySchemaExpectation().event_fields


def policy(tmp_path: Path) -> PermitReplayPathPolicy:
    home = tmp_path / "Users" / "operator"
    home.mkdir(parents=True)
    return PermitReplayPathPolicy(Path.cwd(), home)


def location(tmp_path: Path) -> tuple[PermitReplayPathPolicy, Path]:
    value = policy(tmp_path)
    path = value.canonical_future_path
    path.parent.mkdir(parents=True)
    return value, path


def semantic(row: dict, payload: object) -> dict:
    return {
        **{key: row[key] for key in FIELDS if key not in (
            "canonical_payload", "event_hash",
        )},
        "canonical_payload": payload,
        "production_authorized": bool(row["production_authorized"]),
    }


def event(
    sequence: int, previous: str, *, permit_id: str = "permit-1",
    event_type: str = "RESERVED", payload: dict | None = None, **changes,
) -> dict:
    payload = payload if payload is not None else {"scope": "sandbox"}
    row = {
        "ledger_sequence": sequence, "event_id": f"{permit_id}-event-{sequence}",
        "permit_id": permit_id, "permit_digest": "sha256:permit",
        "activation_id": "activation-1",
        "activation_request_digest": "sha256:activation", "event_type": event_type,
        "event_at": NOW, "actor_identity": "operator",
        "target_identity": "mac-control-plane", "environment": "test",
        "canonical_payload": canonical_json_bytes(payload).decode(),
        "payload_digest": sha256_digest(payload), "previous_event_hash": previous,
        "production_authorized": 0,
    }
    row.update(changes)
    row["event_hash"] = sha256_digest(semantic(row, payload))
    return row


def lifecycle(*types: str, permit_id: str = "permit-1") -> list[dict]:
    result, previous = [], "GENESIS"
    for sequence, event_type in enumerate(types, 1):
        value = event(sequence, previous, permit_id=permit_id, event_type=event_type)
        result.append(value)
        previous = value["event_hash"]
    return result


def create_db(
    path: Path, events=(), *, version="dpl/permit-replay-sqlite/v1",
    indexes=True, triggers=True,
) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        "CREATE TABLE permit_replay_meta(schema_version TEXT NOT NULL);"
        "CREATE TABLE permit_use_events("
        "ledger_sequence INTEGER NOT NULL,event_id TEXT NOT NULL,"
        "permit_id TEXT NOT NULL,permit_digest TEXT NOT NULL,"
        "activation_id TEXT NOT NULL,activation_request_digest TEXT NOT NULL,"
        "event_type TEXT NOT NULL,event_at TEXT NOT NULL,actor_identity TEXT NOT NULL,"
        "target_identity TEXT NOT NULL,environment TEXT NOT NULL,"
        "canonical_payload TEXT NOT NULL,payload_digest TEXT NOT NULL,"
        "previous_event_hash TEXT NOT NULL,event_hash TEXT NOT NULL,"
        "production_authorized INTEGER NOT NULL);"
    )
    if indexes:
        connection.executescript(
            "CREATE UNIQUE INDEX ux_permit_use_events_event_id "
            "ON permit_use_events(event_id);"
            "CREATE UNIQUE INDEX ux_permit_use_events_ledger_sequence "
            "ON permit_use_events(ledger_sequence);"
            "CREATE UNIQUE INDEX ux_permit_use_events_one_reservation "
            "ON permit_use_events(permit_id) WHERE event_type='RESERVED';"
            "CREATE UNIQUE INDEX ux_permit_use_events_one_terminal "
            "ON permit_use_events(permit_id) "
            "WHERE event_type IN ('CONSUMED','FAILED_CLOSED');"
        )
    if triggers:
        connection.executescript(
            "CREATE TRIGGER trg_permit_use_events_no_update BEFORE UPDATE "
            "ON permit_use_events BEGIN SELECT RAISE(ABORT,'immutable'); END;"
            "CREATE TRIGGER trg_permit_use_events_no_delete BEFORE DELETE "
            "ON permit_use_events BEGIN SELECT RAISE(ABORT,'immutable'); END;"
        )
    connection.execute("INSERT INTO permit_replay_meta VALUES (?)", (version,))
    for value in events:
        connection.execute(
            f"INSERT INTO permit_use_events ({','.join(FIELDS)}) "
            f"VALUES ({','.join('?' for _ in FIELDS)})",
            tuple(value[field] for field in FIELDS),
        )
    connection.commit()
    connection.close()


def inspect(path: Path, value: PermitReplayPathPolicy):
    return PermitReplayReadOnlyInspector(
        config=PermitReplayStorageConfig(path), path_policy=value,
    ).inspect(inspected_at=NOW)


def codes(report) -> set[str]:
    return {finding.code for finding in report.schema_findings}


def mutate(path: Path, sql: str, parameters=()) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        "DROP TRIGGER IF EXISTS trg_permit_use_events_no_update;"
        "DROP TRIGGER IF EXISTS trg_permit_use_events_no_delete;"
    )
    connection.execute(sql, parameters)
    connection.commit()
    connection.close()


def test_immutable_config_report_schema_and_future_path(tmp_path):
    value = policy(tmp_path)
    config = PermitReplayStorageConfig(value.canonical_future_path)
    assert str(value.canonical_future_path).endswith(
        "Library/Application Support/AIControlCenter/security/permit-replay.sqlite3"
    )
    with pytest.raises(FrozenInstanceError):
        config.timeout_seconds = 4
    schema = PermitReplaySchemaExpectation()
    assert schema.immutable_events and schema.append_only
    assert "production_authorized = 0" in schema.schema_sql_for_documentation()


def test_missing_file_remains_missing_and_mode_ro_never_creates_parent(tmp_path):
    value = policy(tmp_path)
    path = value.canonical_future_path
    report = inspect(path, value)
    assert report.status is PermitReplayStatus.UNAVAILABLE
    assert report.connection_mode == "mode=ro"
    assert not path.exists() and not path.parent.exists()
    assert report.writes_performed == report.reservations_performed == 0
    assert report.consumptions_performed == report.migrations_performed == 0
    assert report.repairs_performed == 0


@pytest.mark.parametrize(
    ("types", "state"),
    [
        ((), None), (("RESERVED",), PermitUseState.RESERVED),
        (("RESERVED", "CONSUMED"), PermitUseState.CONSUMED),
        (("RESERVED", "FAILED_CLOSED"), PermitUseState.FAILED_CLOSED),
    ],
)
def test_valid_states_are_healthy_deterministic_and_read_only(tmp_path, types, state):
    value, path = location(tmp_path)
    values = lifecycle(*types)
    create_db(path, values)
    before = path.read_bytes()
    first, second = inspect(path, value), inspect(path, value)
    assert first == second and first.canonical_json() == second.canonical_json()
    assert first.status is PermitReplayStatus.HEALTHY
    assert first.query_only and first.chain_result == first.privacy_result == "VALID"
    assert path.read_bytes() == before
    if state:
        assert first.permit_states[0][1] is state
    else:
        assert first.event_count == first.permit_count == 0


def test_multiple_valid_lifecycles(tmp_path):
    value, path = location(tmp_path)
    first = lifecycle("RESERVED", "CONSUMED", permit_id="permit-1")
    second = lifecycle("RESERVED", permit_id="permit-2")
    second[0]["ledger_sequence"] = 3
    second[0]["previous_event_hash"] = first[-1]["event_hash"]
    payload = json.loads(second[0]["canonical_payload"])
    second[0]["event_hash"] = sha256_digest(semantic(second[0], payload))
    create_db(path, first + second)
    report = inspect(path, value)
    assert report.status is PermitReplayStatus.HEALTHY
    assert report.permit_count == 2 and report.consumed_count == report.reserved_count == 1


@pytest.mark.parametrize(
    ("types", "expected"),
    [
        (("RESERVED", "RESERVED"), "DUPLICATE_RESERVATION"),
        (("CONSUMED",), "TERMINAL_WITHOUT_RESERVATION"),
        (("RESERVED", "CONSUMED", "CONSUMED"), "MULTIPLE_TERMINAL_EVENTS"),
        (("RESERVED", "FAILED_CLOSED", "CONSUMED"), "CONSUMED_AFTER_FAILED_CLOSED"),
        (("RESERVED", "CONSUMED", "FAILED_CLOSED"), "FAILED_CLOSED_AFTER_CONSUMED"),
    ],
)
def test_lifecycle_violations_are_invalid(tmp_path, types, expected):
    value, path = location(tmp_path)
    create_db(path, lifecycle(*types), indexes=False)
    report = inspect(path, value)
    assert expected in codes(report)
    assert report.invalid_count == 1


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("UPDATE permit_use_events SET event_id='permit-1-event-1' "
         "WHERE ledger_sequence=2",
         "DUPLICATE_EVENT_ID"),
        ("UPDATE permit_use_events SET ledger_sequence=1 WHERE ledger_sequence=2",
         "DUPLICATE_SEQUENCE"),
        ("UPDATE permit_use_events SET ledger_sequence=3 WHERE ledger_sequence=2",
         "MISSING_SEQUENCE_GAP"),
        ("UPDATE permit_use_events SET previous_event_hash='bad' WHERE ledger_sequence=2",
         "BROKEN_PREVIOUS_EVENT_HASH"),
        ("UPDATE permit_use_events SET payload_digest='bad' WHERE ledger_sequence=1",
         "INVALID_PAYLOAD_DIGEST"),
        ("UPDATE permit_use_events SET event_hash='bad' WHERE ledger_sequence=1",
         "INVALID_EVENT_HASH"),
        ("UPDATE permit_use_events SET permit_digest='other' WHERE ledger_sequence=2",
         "PERMIT_DIGEST_MISMATCH"),
        ("UPDATE permit_use_events SET activation_id='other' WHERE ledger_sequence=2",
         "ACTIVATION_ID_MISMATCH"),
        ("UPDATE permit_use_events SET event_type='UNKNOWN' WHERE ledger_sequence=1",
         "UNKNOWN_EVENT_TYPE"),
    ],
)
def test_event_integrity_violations(tmp_path, mutation, expected):
    value, path = location(tmp_path)
    create_db(path, lifecycle("RESERVED", "CONSUMED"), indexes=False)
    mutate(path, mutation)
    assert expected in codes(inspect(path, value))


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ({"payload": {"access_token": "never-expose"}}, "SECRET_BEARING_PAYLOAD"),
        ({"payload": {"nonce": "never-expose"}}, "SECRET_BEARING_PAYLOAD"),
        ({"production_authorized": 1}, "PRODUCTION_AUTHORIZED_VIOLATION"),
        ({"environment": "production"}, "PRODUCTION_ENVIRONMENT"),
        ({"target_identity": "ubuntu-worker"}, "UBUNTU_TARGET_OWNERSHIP"),
    ],
)
def test_privacy_production_and_ownership_violations_are_redacted(
    tmp_path, change, expected,
):
    value, path = location(tmp_path)
    payload = change.pop("payload", {"scope": "sandbox"})
    row = event(1, "GENESIS", payload=payload, **change)
    create_db(path, [row])
    report = inspect(path, value)
    assert expected in codes(report)
    assert "never-expose" not in report.canonical_json()


def test_modified_payload_and_event_hash_are_both_detected(tmp_path):
    value, path = location(tmp_path)
    create_db(path, lifecycle("RESERVED"))
    mutate(path, "UPDATE permit_use_events SET canonical_payload='{}'")
    assert {"MODIFIED_CANONICAL_PAYLOAD", "INVALID_EVENT_HASH"} <= codes(
        inspect(path, value)
    )


def test_corrupt_schema_mismatch_missing_table_index_and_trigger(tmp_path):
    value, path = location(tmp_path)
    path.write_bytes(b"corrupt")
    assert "INVALID_SQLITE_HEADER" in codes(inspect(path, value))
    path.unlink()
    create_db(path, version="wrong", indexes=False, triggers=False)
    assert {"SCHEMA_VERSION_MISMATCH", "MISSING_INDEX",
            "MISSING_IMMUTABILITY_TRIGGER"} <= codes(inspect(path, value))
    other = path.with_name("missing.sqlite3")
    connection = sqlite3.connect(other)
    connection.execute("CREATE TABLE permit_replay_meta(schema_version TEXT)")
    connection.commit()
    connection.close()
    assert "MISSING_TABLE" in codes(inspect(other, value))


def test_path_policy_rejections_include_symlink_parent_and_filename(tmp_path):
    value, real = location(tmp_path)
    create_db(real)
    link = real.with_name("link.sqlite3")
    link.symlink_to(real)
    candidates = (
        Path("relative.sqlite3"), Path.cwd() / "permit.sqlite3",
        Path("/System/permit.sqlite3"), Path("/Volumes/network/permit.sqlite3"),
        Path("/home/ubuntu/permit.sqlite3"),
        real.with_name("access-token.sqlite3"), link,
    )
    for candidate in candidates:
        assert value.validate(candidate)
    actual = value.user_home / "actual"
    actual.mkdir()
    parent = value.user_home / "Library" / "Application Support" / "linked"
    parent.symlink_to(actual, target_is_directory=True)
    assert "SYMLINK_PATH_COMPONENT" in value.validate(parent / "permit.sqlite3")


def test_no_mutation_command_network_api_worker_or_writer_dependency():
    root = Path("core/deployment/permit_replay_sqlite")
    sources = tuple(root.glob("*.py"))
    text = "\n".join(path.read_text() for path in sources)
    inspector = Path(root / "inspector.py").read_text()
    tree = ast.parse(text)
    imports = {
        node.names[0].name if isinstance(node, ast.Import) else node.module
        for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
    }
    assert "mode=ro" in inspector and "PRAGMA query_only=ON" in inspector
    assert not any(str(value).startswith((
        "subprocess", "socket", "requests", "paramiko", "core.api", "core.worker",
        "core.deployment.audit_sqlite_writer",
    )) for value in imports)
    inspector_tree = ast.parse(inspector)
    forbidden_calls = {"executescript", "commit", "rollback"}
    assert not any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr in forbidden_calls for node in ast.walk(inspector_tree)
    )
    upper = inspector.upper()
    assert not any(value in upper for value in (
        "CREATE TABLE", "ALTER TABLE", "DROP TABLE", "INSERT INTO",
        "UPDATE PERMIT", "DELETE FROM", "PRAGMA JOURNAL_MODE=",
    ))
    assert validate_dependency_boundaries(
        repository_root=Path.cwd()
    )["overall_result"] == "PASS"
