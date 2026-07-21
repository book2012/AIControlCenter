from datetime import datetime, timezone

from core.api.routes import governance_audit
from core.api.services.governance_audit_operations import (
    build_governance_audit_operations_payload,
)
from core.governance.operations.adapters.sqlite import (
    SQLiteOperationsEventRepository,
)
from core.governance.operations.domain.events import (
    Operation,
    scheduled_event,
    started_event,
    succeeded_event,
)


def utc(
    hour: int,
    minute: int = 0,
    second: int = 0,
) -> datetime:
    return datetime(
        2026,
        7,
        21,
        hour,
        minute,
        second,
        tzinfo=timezone.utc,
    )


def test_missing_database_returns_unknown_read_only_payload(
    tmp_path,
):
    payload = build_governance_audit_operations_payload(
        tmp_path / "missing.sqlite3",
        generated_at=utc(10),
    )

    assert payload["read_only"] is True
    assert payload["write_actions"] == []
    assert (
        payload["production_database_migrated"]
        is False
    )
    assert payload["overall_health"] == "unknown"
    assert len(payload["operations"]) == 2
    assert {
        item["unavailable_reason"]
        for item in payload["operations"]
    } == {"database-not-found"}


def test_empty_operations_schema_returns_unknown_projections(
    tmp_path,
):
    database = tmp_path / "operations.sqlite3"
    repository = SQLiteOperationsEventRepository(
        database
    )
    repository.initialize_schema()

    payload = build_governance_audit_operations_payload(
        database,
        generated_at=utc(10),
    )

    assert (
        payload["production_database_migrated"]
        is True
    )
    assert payload["overall_health"] == "unknown"
    assert {
        item["latest_state"]
        for item in payload["operations"]
    } == {None}
    assert {
        item["freshness_state"]
        for item in payload["operations"]
    } == {"unknown"}
    assert {
        item["availability"]
        for item in payload["operations"]
    } == {"available"}


def test_populated_database_returns_health_aware_projections(
    tmp_path,
):
    database = tmp_path / "operations.sqlite3"
    repository = SQLiteOperationsEventRepository(
        database
    )
    repository.initialize_schema()

    snapshot_scheduled = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(8),
    )
    snapshot_started = started_event(
        snapshot_scheduled,
        utc(8, 0, 2),
    )
    snapshot_succeeded = succeeded_event(
        snapshot_started,
        utc(8, 0, 6),
        evidence={
            "record_count": 4,
            "snapshot_id": "snapshot-001",
        },
    )

    backup_scheduled = scheduled_event(
        Operation.SQLITE_ONLINE_BACKUP_VERIFICATION,
        utc(9),
    )
    backup_started = started_event(
        backup_scheduled,
        utc(9, 0, 1),
    )
    backup_succeeded = succeeded_event(
        backup_started,
        utc(9, 0, 4),
        evidence={
            "automatic_restore": False,
            "backup_path": "/tmp/verified.sqlite3",
            "backup_sha256": "a" * 64,
            "quick_check": ["ok"],
            "row_counts_match": True,
        },
    )

    for event in (
        snapshot_scheduled,
        snapshot_started,
        snapshot_succeeded,
        backup_scheduled,
        backup_started,
        backup_succeeded,
    ):
        repository.append(event)

    payload = build_governance_audit_operations_payload(
        database,
        generated_at=utc(9, 5),
    )

    operations = {
        item["operation"]: item
        for item in payload["operations"]
    }
    snapshot = operations[
        "governance_audit_snapshot"
    ]
    backup = operations[
        "sqlite_online_backup_verification"
    ]

    assert snapshot["latest_state"] == "succeeded"
    assert snapshot["freshness_state"] == "critical"
    assert snapshot["overall_health"] == "unhealthy"
    assert snapshot["duration_ms"] == 4000
    assert snapshot["scheduling_latency_ms"] == 2000
    assert snapshot["last_success_at"] is not None

    assert backup["latest_state"] == "succeeded"
    assert backup["freshness_state"] == "fresh"
    assert backup["overall_health"] == "healthy"
    assert (
        backup["backup_verification"]["quick_check"]
        == ["ok"]
    )

    assert payload["overall_health"] == "unhealthy"


def test_operations_route_calls_strict_shared_service(
    monkeypatch,
):
    sentinel = {
        "schema_version": "test",
        "read_only": True,
    }

    monkeypatch.setattr(
        governance_audit,
        "build_governance_audit_operations_payload",
        lambda: sentinel,
    )

    assert (
        governance_audit
        .get_governance_audit_operations()
        == sentinel
    )


def test_operations_route_is_get_only():
    matches = [
        route
        for route in governance_audit.router.routes
        if str(
            getattr(route, "path", "")
        ).endswith("/operations")
    ]

    assert len(matches) == 1
    assert matches[0].methods == {"GET"}


def test_operations_payload_exposes_no_write_actions(
    tmp_path,
):
    payload = build_governance_audit_operations_payload(
        tmp_path / "missing.sqlite3",
        generated_at=utc(10),
    )

    assert payload["write_actions"] == []
    assert "actions" not in payload
