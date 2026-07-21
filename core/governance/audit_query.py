"""Read-only governance audit query orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.governance.audit_comparison import (
    AuditComparisonError,
    compare_snapshots,
)
from core.governance.audit_repository import (
    DEFAULT_LIST_LIMIT,
    AuditRepository,
    AuditRepositoryError,
)
from core.governance.audit_snapshot import AuditSnapshot


SERVICE_NAME = "model-governance-audit"
MODE = "read-only"


class AuditQueryError(RuntimeError):
    """Raised when read-only audit queries fail safely."""


class AuditSnapshotNotFoundError(AuditQueryError):
    """Raised when an explicitly requested snapshot does not exist."""


@dataclass(frozen=True)
class LatestQueryResult:
    snapshot: AuditSnapshot | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": SERVICE_NAME,
            "mode": MODE,
            "snapshot": (
                None
                if self.snapshot is None
                else self.snapshot.to_dict()
            ),
            "empty": self.snapshot is None,
        }


@dataclass(frozen=True)
class SnapshotQueryResult:
    snapshot: AuditSnapshot

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": SERVICE_NAME,
            "mode": MODE,
            "snapshot": self.snapshot.to_dict(),
        }


@dataclass(frozen=True)
class SnapshotCursor:
    before_captured_at: str
    before_snapshot_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "before_captured_at":
                self.before_captured_at,
            "before_snapshot_id":
                self.before_snapshot_id,
        }


@dataclass(frozen=True)
class SnapshotListResult:
    items: tuple[AuditSnapshot, ...]
    next_cursor: SnapshotCursor | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": SERVICE_NAME,
            "mode": MODE,
            "items": [
                item.to_dict()
                for item in self.items
            ],
            "count": len(self.items),
            "next_cursor": (
                None
                if self.next_cursor is None
                else self.next_cursor.to_dict()
            ),
        }


@dataclass(frozen=True)
class ComparisonQueryResult:
    status: str
    previous_snapshot: AuditSnapshot | None
    current_snapshot: AuditSnapshot | None
    comparison: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": SERVICE_NAME,
            "mode": MODE,
            "status": self.status,
            "previous_snapshot": (
                None
                if self.previous_snapshot is None
                else self.previous_snapshot.to_dict()
            ),
            "current_snapshot": (
                None
                if self.current_snapshot is None
                else self.current_snapshot.to_dict()
            ),
            "comparison": self.comparison,
        }


class AuditQueryService:
    """Expose repository state through safe read-only queries."""

    def __init__(
        self,
        repository: AuditRepository,
    ) -> None:
        if not isinstance(repository, AuditRepository):
            raise AuditQueryError(
                "repository must implement AuditRepository"
            )

        self._repository = repository

    def get_latest(self) -> LatestQueryResult:
        try:
            snapshot = (
                self._repository.get_latest_snapshot()
            )
        except AuditRepositoryError as error:
            raise AuditQueryError(
                "latest audit snapshot query failed"
            ) from error

        return LatestQueryResult(
            snapshot=snapshot,
        )

    def get_snapshot(
        self,
        snapshot_id: str,
    ) -> SnapshotQueryResult:
        try:
            snapshot = self._repository.get_snapshot(
                snapshot_id
            )
        except AuditRepositoryError as error:
            raise AuditQueryError(
                "audit snapshot query failed"
            ) from error

        if snapshot is None:
            raise AuditSnapshotNotFoundError(
                "audit snapshot not found"
            )

        return SnapshotQueryResult(
            snapshot=snapshot,
        )

    def list_snapshots(
        self,
        *,
        limit: int = DEFAULT_LIST_LIMIT,
        before_captured_at: str | None = None,
        before_snapshot_id: str | None = None,
    ) -> SnapshotListResult:
        try:
            items = self._repository.list_snapshots(
                limit=limit,
                before_captured_at=before_captured_at,
                before_snapshot_id=before_snapshot_id,
            )
        except AuditRepositoryError as error:
            raise AuditQueryError(
                "audit snapshot list query failed"
            ) from error

        next_cursor: SnapshotCursor | None = None

        if len(items) == limit and items:
            last = items[-1]

            next_cursor = SnapshotCursor(
                before_captured_at=last.captured_at,
                before_snapshot_id=last.snapshot_id,
            )

        return SnapshotListResult(
            items=items,
            next_cursor=next_cursor,
        )

    def compare_latest(
        self,
    ) -> ComparisonQueryResult:
        try:
            snapshots = self._repository.list_snapshots(
                limit=2
            )
        except AuditRepositoryError as error:
            raise AuditQueryError(
                "latest audit comparison query failed"
            ) from error

        if not snapshots:
            return ComparisonQueryResult(
                status="NO_DATA",
                previous_snapshot=None,
                current_snapshot=None,
                comparison=None,
            )

        if len(snapshots) == 1:
            return ComparisonQueryResult(
                status="NO_BASELINE",
                previous_snapshot=None,
                current_snapshot=snapshots[0],
                comparison=None,
            )

        current = snapshots[0]
        previous = snapshots[1]

        return self._compare(
            previous=previous,
            current=current,
        )

    def compare_explicit(
        self,
        *,
        previous_snapshot_id: str,
        current_snapshot_id: str,
    ) -> ComparisonQueryResult:
        if previous_snapshot_id == current_snapshot_id:
            raise AuditQueryError(
                "comparison snapshot IDs must be different"
            )

        previous_result = self.get_snapshot(
            previous_snapshot_id
        )
        current_result = self.get_snapshot(
            current_snapshot_id
        )

        return self._compare(
            previous=previous_result.snapshot,
            current=current_result.snapshot,
        )

    @staticmethod
    def _compare(
        *,
        previous: AuditSnapshot,
        current: AuditSnapshot,
    ) -> ComparisonQueryResult:
        try:
            comparison = compare_snapshots(
                previous,
                current,
            )
        except AuditComparisonError as error:
            raise AuditQueryError(
                "audit snapshot comparison failed"
            ) from error

        return ComparisonQueryResult(
            status=comparison.status,
            previous_snapshot=previous,
            current_snapshot=current,
            comparison=comparison.to_dict(),
        )
