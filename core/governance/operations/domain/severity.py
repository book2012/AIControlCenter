"""Operational notification severity signals."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping
from uuid import UUID, uuid4

from .events import (
    DomainValidationError,
    Operation,
    immutable_mapping,
    require_utc,
)


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class OperationalCondition(str, Enum):
    SUCCESS = "successful_scheduled_observation"
    RECOVERY = "recovery"
    EXECUTION_FAILURE = "execution_failure"
    DURATION_WARNING = "duration_warning"
    LATENCY_WARNING = "latency_warning"
    FRESHNESS_WARNING = "freshness_warning"
    MISSED_RUN = "missed_run"
    BACKUP_VERIFICATION_FAILURE = (
        "backup_verification_failure"
    )
    AUDIT_PERSISTENCE_UNAVAILABLE = (
        "audit_persistence_unavailable"
    )
    APPEND_ONLY_INVARIANT_VIOLATION = (
        "append_only_invariant_violation"
    )
    CRITICAL_FRESHNESS = "critical_freshness"


_SEVERITY_BY_CONDITION = {
    OperationalCondition.SUCCESS: Severity.INFO,
    OperationalCondition.RECOVERY: Severity.INFO,
    OperationalCondition.EXECUTION_FAILURE: (
        Severity.WARNING
    ),
    OperationalCondition.DURATION_WARNING: (
        Severity.WARNING
    ),
    OperationalCondition.LATENCY_WARNING: (
        Severity.WARNING
    ),
    OperationalCondition.FRESHNESS_WARNING: (
        Severity.WARNING
    ),
    OperationalCondition.MISSED_RUN: Severity.CRITICAL,
    OperationalCondition.BACKUP_VERIFICATION_FAILURE: (
        Severity.CRITICAL
    ),
    OperationalCondition.AUDIT_PERSISTENCE_UNAVAILABLE: (
        Severity.CRITICAL
    ),
    OperationalCondition.APPEND_ONLY_INVARIANT_VIOLATION: (
        Severity.CRITICAL
    ),
    OperationalCondition.CRITICAL_FRESHNESS: (
        Severity.CRITICAL
    ),
}


def classify_severity(
    condition: OperationalCondition,
) -> Severity:
    if not isinstance(condition, OperationalCondition):
        raise DomainValidationError(
            "condition must be OperationalCondition"
        )

    return _SEVERITY_BY_CONDITION[condition]


@dataclass(frozen=True, slots=True)
class NotificationSignal:
    signal_id: UUID
    severity: Severity
    condition: OperationalCondition
    observed_at: datetime
    deduplication_key: str
    operation: Operation | None = None
    run_id: UUID | None = None
    evidence: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.signal_id, UUID):
            raise DomainValidationError(
                "signal_id must be UUID"
            )
        if not isinstance(self.severity, Severity):
            raise DomainValidationError(
                "severity must be Severity"
            )
        if not isinstance(
            self.condition,
            OperationalCondition,
        ):
            raise DomainValidationError(
                "condition must be OperationalCondition"
            )
        if not self.deduplication_key.strip():
            raise DomainValidationError(
                "deduplication_key must not be empty"
            )

        object.__setattr__(
            self,
            "observed_at",
            require_utc(
                self.observed_at,
                "observed_at",
            ),
        )
        object.__setattr__(
            self,
            "evidence",
            immutable_mapping(self.evidence),
        )


def build_signal(
    condition: OperationalCondition,
    observed_at: datetime,
    deduplication_key: str,
    *,
    operation: Operation | None = None,
    run_id: UUID | None = None,
    evidence: Mapping[str, Any] | None = None,
    signal_id: UUID | None = None,
) -> NotificationSignal:
    return NotificationSignal(
        signal_id=signal_id or uuid4(),
        severity=classify_severity(condition),
        condition=condition,
        observed_at=observed_at,
        deduplication_key=deduplication_key,
        operation=operation,
        run_id=run_id,
        evidence=evidence or {},
    )
