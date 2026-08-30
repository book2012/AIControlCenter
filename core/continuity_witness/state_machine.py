"""Deterministic, repository-local lifecycle state machine.

This module models authority consumption; it performs no infrastructure I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from .contracts import ImmutableHistoryObservation, TransitionIntent
from .domain import ContinuityHostId, LifecycleOperation, LifecycleOperationId, TransitionId


class LifecycleState(str, Enum):
    ACTIVE = "ACTIVE"
    DECOMMISSIONED = "DECOMMISSIONED"


class DatabaseStatus(str, Enum):
    NOT_COMMITTED = "NOT_COMMITTED"
    COMMITTED = "COMMITTED"
    FAILED = "FAILED"


class EffectiveStatus(str, Enum):
    PROVEN_SUCCESS = "PROVEN_SUCCESS"
    FAILED_CONSUMED = "FAILED_CONSUMED"
    UNCERTAIN_CONSUMED = "UNCERTAIN_CONSUMED"


class ReconciliationResult(str, Enum):
    EXACT = "EXACT"
    MISSING = "MISSING"
    CONFLICTING = "CONFLICTING"
    UNVERIFIABLE = "UNVERIFIABLE"


@dataclass(frozen=True, slots=True)
class LifecycleRecord:
    continuity_host_id: ContinuityHostId
    enrollment_generation: int
    record_generation: int
    state: LifecycleState
    version_maxima: Mapping[str, int]
    predecessor_continuity_host_id: ContinuityHostId | None = None

    def __post_init__(self) -> None:
        maxima: dict[str, int] = {}
        for key, value in self.version_maxima.items():
            if not isinstance(key, str) or not key:
                raise ValueError("version maxima keys must be non-empty str")
            if type(value) is not int or value < 0:
                raise ValueError("version maxima values must be non-negative exact int")
            maxima[key] = value
        object.__setattr__(self, "version_maxima", MappingProxyType(maxima))


@dataclass(frozen=True, slots=True)
class LifecycleTransition:
    transition_id: TransitionId
    operation_id: LifecycleOperationId
    ordinal: int
    role: str
    before: LifecycleRecord | None
    after: LifecycleRecord


@dataclass(frozen=True, slots=True)
class LifecycleResult:
    operation_id: LifecycleOperationId
    transitions: tuple[LifecycleTransition, ...]
    database_status: DatabaseStatus
    database_result: ReconciliationResult
    checkpoint_result: ReconciliationResult
    effective_status: EffectiveStatus


class LifecycleDenied(ValueError):
    """The supplied evidence or current state cannot authorize the operation."""


def reconcile_effective_status(
    *, database_status: DatabaseStatus, database_result: ReconciliationResult,
    checkpoint_result: ReconciliationResult, identifiers_match: bool = True,
    digests_match: bool = True,
) -> EffectiveStatus:
    if (database_status is DatabaseStatus.COMMITTED
            and database_result is ReconciliationResult.EXACT
            and checkpoint_result is ReconciliationResult.EXACT
            and identifiers_match and digests_match):
        return EffectiveStatus.PROVEN_SUCCESS
    if database_status in {DatabaseStatus.NOT_COMMITTED, DatabaseStatus.FAILED}:
        return EffectiveStatus.FAILED_CONSUMED
    return EffectiveStatus.UNCERTAIN_CONSUMED


class LifecycleStateMachine:
    """Pure transition planner. Persistence is supplied by the fake store."""

    def __init__(self) -> None:
        self._next_host = 0x100
        self._next_transition = 0x1000

    def _host_id(self) -> ContinuityHostId:
        self._next_host += 1
        return ContinuityHostId(f"01890f3c-4b2a-7cc1-8c00-{self._next_host:012x}")

    def _transition_id(self) -> TransitionId:
        self._next_transition += 1
        return TransitionId(f"01890f3c-4b2a-7cc1-8c00-{self._next_transition:012x}")

    @staticmethod
    def _maxima(current: LifecycleRecord | None, proposed: Mapping[str, int] | None) -> dict[str, int]:
        result = dict(current.version_maxima if current else {})
        for key, value in (proposed or {}).items():
            if value < result.get(key, 0):
                raise LifecycleDenied("version maxima cannot decrease")
            result[key] = value
        return result

    def plan(self, intent: TransitionIntent, *, current: LifecycleRecord | None = None,
             history: ImmutableHistoryObservation | None = None,
             version_maxima: Mapping[str, int] | None = None) -> tuple[LifecycleTransition, ...]:
        operation = intent.operation_type
        if operation is LifecycleOperation.GENESIS_ENROLLMENT:
            if current is not None or history is None or not history.proves_historical_absence:
                raise LifecycleDenied("GENESIS requires complete verified historical absence")
            after = LifecycleRecord(self._host_id(), 1, 1, LifecycleState.ACTIVE,
                                    self._maxima(None, version_maxima))
            return (self._transition(intent, 1, "TARGET", None, after),)

        if current is None:
            raise LifecycleDenied("exact current lifecycle record is required")
        if current.state is LifecycleState.DECOMMISSIONED:
            raise LifecycleDenied("DECOMMISSIONED is terminal")
        expected_id = (intent.expected_predecessor_continuity_host_id
                       if operation is LifecycleOperation.MIGRATION
                       else intent.expected_continuity_host_id)
        if expected_id != current.continuity_host_id or intent.expected_record_generation != current.record_generation:
            raise LifecycleDenied("host or record generation does not match current state")
        maxima = self._maxima(current, version_maxima)

        if operation is LifecycleOperation.RECOVERY:
            after = LifecycleRecord(current.continuity_host_id, current.enrollment_generation,
                                    current.record_generation + 1, LifecycleState.ACTIVE, maxima,
                                    current.predecessor_continuity_host_id)
            return (self._transition(intent, 1, "TARGET", current, after),)
        if operation is LifecycleOperation.DECOMMISSION:
            after = LifecycleRecord(current.continuity_host_id, current.enrollment_generation,
                                    current.record_generation + 1, LifecycleState.DECOMMISSIONED,
                                    maxima, current.predecessor_continuity_host_id)
            return (self._transition(intent, 1, "TARGET", current, after),)

        predecessor = LifecycleRecord(current.continuity_host_id, current.enrollment_generation,
                                      current.record_generation + 1, LifecycleState.DECOMMISSIONED,
                                      maxima, current.predecessor_continuity_host_id)
        successor = LifecycleRecord(self._host_id(), 1, 1, LifecycleState.ACTIVE, maxima,
                                    current.continuity_host_id)
        return (self._transition(intent, 1, "PREDECESSOR", current, predecessor),
                self._transition(intent, 2, "SUCCESSOR", None, successor))

    def _transition(self, intent: TransitionIntent, ordinal: int, role: str,
                    before: LifecycleRecord | None, after: LifecycleRecord) -> LifecycleTransition:
        return LifecycleTransition(self._transition_id(), intent.operation_id, ordinal, role, before, after)
