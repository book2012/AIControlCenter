import sqlite3
from pathlib import Path

import pytest

from core.governance.audit_repository import (
    MAX_LIST_LIMIT,
    AuditRepositoryError,
    SQLiteAuditRepository,
)
from core.governance.audit_snapshot import (
    AuditSnapshot,
    GovernanceSummary,
)


SOURCE_COMMIT = "1b40357e7585c0eddea09cbfb964636874fa56f8"
RUNTIME_RELEASE = "39fe04e3330e"
MIGRATED_AT = "2026-07-21T14:00:00Z"


def governance_payload(
    *,
    observed_count: int = 0,
    violation_count: int = 0,
) -> dict:
    return {
        "service": "model-governance",
        "mode": "read-only",
        "default_policy": "DENY",
        "approved_count": 0,
        "observed_count": observed_count,
        "compliant_count": 0,
        "violation_count": violation_count,
        "models": [],
        "write_operations_allowed": False,
    }


def summary(
    *,
    observed_count: int = 0,
    violation_count: int = 0,
    unapproved_count: int = 0,
) -> GovernanceSummary:
    severity = (
        "CRITICAL"
        if violation_count
        else "INFO"
    )

    return GovernanceSummary(
        severity=severity,
        approved_count=0,
        observed_count=observed_count,
        compliant_count=0,
        violation_count=violation_count,
        unapproved_count=unapproved_count,
        missing_count=0,
        digest_mismatch_count=0,
        resource_policy_violation_count=0,
    )


def snapshot(
    captured_at: str,
    *,
    observed_count: int = 0,
    violation_count: int = 0,
    unapproved_count: int = 0,
) -> AuditSnapshot:
    return AuditSnapshot.create(
        captured_at=captured_at,
        source_commit=SOURCE_COMMIT,
        runtime_release=RUNTIME_RELEASE,
        governance=governance_payload(
            observed_count=observed_count,
            violation_count=violation_count,
        ),
        summary=summary(
            observed_count=observed_count,
            violation_count=violation_count,
            unapproved_count=unapproved_count,
        ),
    )


def repository(
    path: Path,
) -> SQLiteAuditRepository:
    repo = SQLiteAuditRepository(
        path,
        application_commit=SOURCE_COMMIT,
        migrated_at=MIGRATED_AT,
    )
    repo.initialize()
    return repo


def test_append_and_get_snapshot(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )
    item = snapshot(
        "2026-07-21T14:01:00Z"
    )

    result = repo.append_snapshot(
        item,
        created_at="2026-07-21T14:01:01Z",
    )

    restored = repo.get_snapshot(
        item.snapshot_id
    )

    assert result.created is True
    assert result.snapshot == item
    assert restored == item


def test_duplicate_append_returns_existing(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )
    item = snapshot(
        "2026-07-21T14:01:00Z"
    )

    first = repo.append_snapshot(
        item,
        created_at="2026-07-21T14:01:01Z",
    )
    second = repo.append_snapshot(
        item,
        created_at="2026-07-21T14:05:00Z",
    )

    assert first.created is True
    assert second.created is False
    assert second.snapshot == item

    rows = repo.list_snapshots()

    assert rows == (item,)


def test_get_missing_snapshot_returns_none(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )

    assert repo.get_snapshot("a" * 64) is None
    assert repo.get_latest_snapshot() is None


def test_latest_snapshot_uses_timestamp_order(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )

    older = snapshot(
        "2026-07-21T14:01:00Z"
    )
    newer = snapshot(
        "2026-07-21T14:02:00Z",
        observed_count=1,
        violation_count=1,
        unapproved_count=1,
    )

    repo.append_snapshot(
        newer,
        created_at="2026-07-21T14:02:01Z",
    )
    repo.append_snapshot(
        older,
        created_at="2026-07-21T14:03:01Z",
    )

    assert repo.get_latest_snapshot() == newer


def test_list_snapshots_orders_and_limits(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )

    items = (
        snapshot("2026-07-21T14:01:00Z"),
        snapshot(
            "2026-07-21T14:02:00Z",
            observed_count=1,
            violation_count=1,
            unapproved_count=1,
        ),
        snapshot(
            "2026-07-21T14:03:00Z",
            observed_count=2,
            violation_count=2,
            unapproved_count=2,
        ),
    )

    for item in items:
        repo.append_snapshot(
            item,
            created_at=item.captured_at,
        )

    result = repo.list_snapshots(limit=2)

    assert result == (
        items[2],
        items[1],
    )


def test_list_snapshots_supports_cursor(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )

    first = snapshot(
        "2026-07-21T14:01:00Z"
    )
    second = snapshot(
        "2026-07-21T14:02:00Z",
        observed_count=1,
        violation_count=1,
        unapproved_count=1,
    )
    third = snapshot(
        "2026-07-21T14:03:00Z",
        observed_count=2,
        violation_count=2,
        unapproved_count=2,
    )

    for item in (first, second, third):
        repo.append_snapshot(
            item,
            created_at=item.captured_at,
        )

    page = repo.list_snapshots(
        limit=10,
        before_captured_at=third.captured_at,
        before_snapshot_id=third.snapshot_id,
    )

    assert page == (
        second,
        first,
    )


@pytest.mark.parametrize(
    "limit",
    [
        0,
        -1,
        MAX_LIST_LIMIT + 1,
        True,
        1.5,
    ],
)
def test_list_rejects_invalid_limit(
    tmp_path: Path,
    limit: object,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )

    with pytest.raises(AuditRepositoryError):
        repo.list_snapshots(limit=limit)


def test_cursor_requires_both_fields(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )

    with pytest.raises(
        AuditRepositoryError,
        match="both cursor fields",
    ):
        repo.list_snapshots(
            before_captured_at=(
                "2026-07-21T14:00:00Z"
            )
        )


def test_read_revalidates_snapshot_hash(
    tmp_path: Path,
) -> None:
    path = tmp_path / "audit.sqlite3"
    repo = repository(path)

    item = snapshot(
        "2026-07-21T14:01:00Z"
    )

    repo.append_snapshot(
        item,
        created_at="2026-07-21T14:01:01Z",
    )

    connection = sqlite3.connect(path)

    try:
        connection.execute(
            "DROP TRIGGER deny_audit_snapshot_update"
        )
        connection.execute(
            """
            UPDATE audit_snapshots
            SET governance_json = ?
            WHERE snapshot_id = ?
            """,
            (
                '{"mode":"write"}',
                item.snapshot_id,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(AuditRepositoryError):
        repo.get_snapshot(item.snapshot_id)


def test_sqlite_triggers_still_deny_update_and_delete(
    tmp_path: Path,
) -> None:
    path = tmp_path / "audit.sqlite3"
    repo = repository(path)

    item = snapshot(
        "2026-07-21T14:01:00Z"
    )

    repo.append_snapshot(
        item,
        created_at="2026-07-21T14:01:01Z",
    )

    connection = sqlite3.connect(path)

    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                UPDATE audit_snapshots
                SET captured_at = ?
                WHERE snapshot_id = ?
                """,
                (
                    "2026-07-21T15:00:00Z",
                    item.snapshot_id,
                ),
            )

        connection.rollback()

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                DELETE FROM audit_snapshots
                WHERE snapshot_id = ?
                """,
                (item.snapshot_id,),
            )
    finally:
        connection.close()
