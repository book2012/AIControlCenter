from pathlib import Path

import pytest

from core.governance.audit_query import (
    AuditQueryError,
    AuditQueryService,
    AuditSnapshotNotFoundError,
)
from core.governance.audit_repository import (
    AuditRepository,
    AuditRepositoryError,
    AppendResult,
    SQLiteAuditRepository,
)
from core.governance.audit_snapshot import (
    AuditSnapshot,
    GovernanceSummary,
)


SOURCE_COMMIT = "0146cc0bfcd882902f8c1ecc34e565b0a1b6bad4"
RUNTIME_RELEASE = "39fe04e3330e"
MIGRATED_AT = "2026-07-21T17:00:00Z"


def snapshot(
    captured_at: str,
    *,
    severity: str = "INFO",
    violation_count: int = 0,
    unapproved_count: int = 0,
) -> AuditSnapshot:
    observed_count = (
        1
        if violation_count
        else 0
    )

    models = (
        [
            {
                "name": "unknown-model",
                "compliance_status": "UNAPPROVED",
            }
        ]
        if violation_count
        else []
    )

    return AuditSnapshot.create(
        captured_at=captured_at,
        source_commit=SOURCE_COMMIT,
        runtime_release=RUNTIME_RELEASE,
        governance={
            "service": "model-governance",
            "mode": "read-only",
            "default_policy": "DENY",
            "approved_count": 0,
            "observed_count": observed_count,
            "compliant_count": 0,
            "violation_count": violation_count,
            "models": models,
            "write_operations_allowed": False,
        },
        summary=GovernanceSummary(
            severity=severity,
            approved_count=0,
            observed_count=observed_count,
            compliant_count=0,
            violation_count=violation_count,
            unapproved_count=unapproved_count,
            missing_count=0,
            digest_mismatch_count=0,
            resource_policy_violation_count=0,
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


def append(
    repo: SQLiteAuditRepository,
    item: AuditSnapshot,
) -> None:
    repo.append_snapshot(
        item,
        created_at=item.captured_at,
    )


def test_latest_empty_state(
    tmp_path: Path,
) -> None:
    service = AuditQueryService(
        repository(tmp_path / "audit.sqlite3")
    )

    result = service.get_latest()
    payload = result.to_dict()

    assert result.snapshot is None
    assert payload["empty"] is True
    assert payload["snapshot"] is None
    assert payload["mode"] == "read-only"


def test_latest_returns_snapshot(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )
    item = snapshot(
        "2026-07-21T17:01:00Z"
    )
    append(repo, item)

    result = AuditQueryService(
        repo
    ).get_latest()

    assert result.snapshot == item
    assert result.to_dict()["empty"] is False


def test_detail_returns_snapshot(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )
    item = snapshot(
        "2026-07-21T17:01:00Z"
    )
    append(repo, item)

    result = AuditQueryService(
        repo
    ).get_snapshot(item.snapshot_id)

    assert result.snapshot == item


def test_detail_missing_raises_not_found(
    tmp_path: Path,
) -> None:
    service = AuditQueryService(
        repository(tmp_path / "audit.sqlite3")
    )

    with pytest.raises(
        AuditSnapshotNotFoundError,
        match="not found",
    ):
        service.get_snapshot("a" * 64)


def test_list_returns_cursor_when_page_is_full(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )

    first = snapshot(
        "2026-07-21T17:01:00Z"
    )
    second = snapshot(
        "2026-07-21T17:02:00Z",
        severity="CRITICAL",
        violation_count=1,
        unapproved_count=1,
    )

    append(repo, first)
    append(repo, second)

    result = AuditQueryService(
        repo
    ).list_snapshots(limit=1)

    assert result.items == (second,)
    assert result.next_cursor is not None
    assert (
        result.next_cursor.before_snapshot_id
        == second.snapshot_id
    )


def test_list_has_no_cursor_for_short_page(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )
    item = snapshot(
        "2026-07-21T17:01:00Z"
    )
    append(repo, item)

    result = AuditQueryService(
        repo
    ).list_snapshots(limit=2)

    assert result.items == (item,)
    assert result.next_cursor is None


def test_compare_latest_no_data(
    tmp_path: Path,
) -> None:
    result = AuditQueryService(
        repository(tmp_path / "audit.sqlite3")
    ).compare_latest()

    assert result.status == "NO_DATA"
    assert result.comparison is None
    assert result.current_snapshot is None


def test_compare_latest_no_baseline(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )
    item = snapshot(
        "2026-07-21T17:01:00Z"
    )
    append(repo, item)

    result = AuditQueryService(
        repo
    ).compare_latest()

    assert result.status == "NO_BASELINE"
    assert result.previous_snapshot is None
    assert result.current_snapshot == item
    assert result.comparison is None


def test_compare_latest_returns_comparison(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )

    previous = snapshot(
        "2026-07-21T17:01:00Z"
    )
    current = snapshot(
        "2026-07-21T17:02:00Z",
        severity="CRITICAL",
        violation_count=1,
        unapproved_count=1,
    )

    append(repo, previous)
    append(repo, current)

    result = AuditQueryService(
        repo
    ).compare_latest()

    assert result.status == "NEW_VIOLATION"
    assert result.previous_snapshot == previous
    assert result.current_snapshot == current
    assert result.comparison is not None


def test_explicit_comparison(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )

    previous = snapshot(
        "2026-07-21T17:01:00Z"
    )
    current = snapshot(
        "2026-07-21T17:02:00Z",
        severity="CRITICAL",
        violation_count=1,
        unapproved_count=1,
    )

    append(repo, previous)
    append(repo, current)

    result = AuditQueryService(
        repo
    ).compare_explicit(
        previous_snapshot_id=previous.snapshot_id,
        current_snapshot_id=current.snapshot_id,
    )

    assert result.status == "NEW_VIOLATION"


def test_explicit_comparison_rejects_same_id(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )
    item = snapshot(
        "2026-07-21T17:01:00Z"
    )
    append(repo, item)

    with pytest.raises(
        AuditQueryError,
        match="must be different",
    ):
        AuditQueryService(
            repo
        ).compare_explicit(
            previous_snapshot_id=item.snapshot_id,
            current_snapshot_id=item.snapshot_id,
        )


class FailingRepository(AuditRepository):
    def append_snapshot(
        self,
        snapshot: AuditSnapshot,
        *,
        created_at: str,
    ) -> AppendResult:
        raise AuditRepositoryError("hidden database path")

    def get_snapshot(
        self,
        snapshot_id: str,
    ) -> AuditSnapshot | None:
        raise AuditRepositoryError("hidden database path")

    def get_latest_snapshot(
        self,
    ) -> AuditSnapshot | None:
        raise AuditRepositoryError("hidden database path")

    def list_snapshots(
        self,
        *,
        limit: int = 100,
        before_captured_at: str | None = None,
        before_snapshot_id: str | None = None,
    ) -> tuple[AuditSnapshot, ...]:
        raise AuditRepositoryError("hidden database path")


def test_repository_error_is_normalized() -> None:
    service = AuditQueryService(
        FailingRepository()
    )

    with pytest.raises(
        AuditQueryError,
        match="latest audit snapshot query failed",
    ) as captured:
        service.get_latest()

    assert "database path" not in str(captured.value)
