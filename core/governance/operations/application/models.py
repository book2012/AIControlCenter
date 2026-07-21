"""Application commands and immutable results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID

from ..domain.events import (
    ExecutionEvent,
    Operation,
    require_utc,
)
from ..domain.severity import NotificationSignal
from ..domain.state import ExecutionState

APPLICATION_CONTRACT_VERSION = "1.0.0"


def immutable_mapping(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


@dataclass(frozen=True, slots=True)
class DispatchCommand:
    job_id: str
    operation: Operation
    scheduled_for: datetime
    dispatch_id: UUID
    attempt: int = 1
    contract_version: str = (
        APPLICATION_CONTRACT_VERSION
    )

    def __post_init__(self) -> None:
        if not self.job_id.strip():
            raise ValueError(
                "job_id must not be empty"
            )

        if not isinstance(
            self.operation,
            Operation,
        ):
            raise TypeError(
                "operation must be Operation"
            )

        if not isinstance(
            self.dispatch_id,
            UUID,
        ):
            raise TypeError(
                "dispatch_id must be UUID"
            )

        if self.attempt < 1:
            raise ValueError(
                "attempt must be at least one"
            )

        if (
            self.contract_version
            != APPLICATION_CONTRACT_VERSION
        ):
            raise ValueError(
                "unsupported contract version"
            )

        object.__setattr__(
            self,
            "scheduled_for",
            require_utc(
                self.scheduled_for,
                "scheduled_for",
            ),
        )


@dataclass(frozen=True, slots=True)
class MissedRunObservationCommand:
    operation: Operation
    observed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(
            self.operation,
            Operation,
        ):
            raise TypeError(
                "operation must be Operation"
            )

        object.__setattr__(
            self,
            "observed_at",
            require_utc(
                self.observed_at,
                "observed_at",
            ),
        )


@dataclass(frozen=True, slots=True)
class SnapshotExecutionResult:
    snapshot_id: str
    snapshot_timestamp: datetime
    record_count: int
    evidence: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.snapshot_id.strip():
            raise ValueError(
                "snapshot_id must not be empty"
            )

        if self.record_count < 0:
            raise ValueError(
                "record_count must be non-negative"
            )

        object.__setattr__(
            self,
            "snapshot_timestamp",
            require_utc(
                self.snapshot_timestamp,
                "snapshot_timestamp",
            ),
        )
        object.__setattr__(
            self,
            "evidence",
            immutable_mapping(self.evidence),
        )

    def to_evidence(
        self,
    ) -> Mapping[str, Any]:
        return immutable_mapping(
            {
                "record_count": self.record_count,
                "snapshot_id": self.snapshot_id,
                "snapshot_timestamp": (
                    self.snapshot_timestamp.isoformat()
                ),
                **dict(self.evidence),
            }
        )


@dataclass(frozen=True, slots=True)
class BackupExecutionResult:
    backup_path: str
    backup_sha256: str
    quick_check: tuple[str, ...]
    row_counts_match: bool
    evidence: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.backup_path.strip():
            raise ValueError(
                "backup_path must not be empty"
            )

        if len(self.backup_sha256) != 64:
            raise ValueError(
                "backup_sha256 must be SHA-256"
            )

        if self.quick_check != ("ok",):
            raise ValueError(
                "quick_check must contain only ok"
            )

        if self.row_counts_match is not True:
            raise ValueError(
                "row counts must match"
            )

        object.__setattr__(
            self,
            "evidence",
            immutable_mapping(self.evidence),
        )

    def to_evidence(
        self,
    ) -> Mapping[str, Any]:
        return immutable_mapping(
            {
                "automatic_restore": False,
                "backup_path": self.backup_path,
                "backup_sha256": self.backup_sha256,
                "quick_check": list(
                    self.quick_check
                ),
                "row_counts_match": (
                    self.row_counts_match
                ),
                **dict(self.evidence),
            }
        )


@dataclass(frozen=True, slots=True)
class DispatchResult:
    run_id: UUID
    state: ExecutionState
    events: tuple[ExecutionEvent, ...]
    events_appended: int
    duplicate_dispatch: bool
    notification_signals: tuple[
        NotificationSignal,
        ...,
    ] = ()


@dataclass(frozen=True, slots=True)
class MissedRunObservationResult:
    operation: Operation
    observed_at: datetime
    missed_run_ids: tuple[UUID, ...]
    events_appended: int
    notification_signals: tuple[
        NotificationSignal,
        ...,
    ] = ()
