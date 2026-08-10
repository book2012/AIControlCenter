"""Pure immutable SEC-02 consumption, execution, and postcondition facts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
import re
from typing import Any

from .failures import (
    InvalidPostconditionModel,
    InvalidReceiptCounts,
    InvalidReceiptModel,
)


class ConsumptionTransactionStatus(StrEnum):
    COMMITTED = "COMMITTED"


class ExecutionStatus(StrEnum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    UNCERTAIN = "UNCERTAIN"


class PostconditionDecision(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


_ACTION_TYPE = re.compile(r"^[A-Z][A-Z0-9]*(?:[_:.][A-Z0-9]+)+$")
_REASON_CODE = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$")
_GENERIC_ACTION_TYPES = frozenset({"ACTION", "EXECUTE", "MUTATE", "WRITE"})


def _text(value: str, field_name: str, error_type: type[ValueError]) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise error_type(f"{field_name} must be non-empty canonical text")
    return value


def _utc(value: datetime, field_name: str, error_type: type[ValueError]) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise error_type(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(timezone.utc)


def _optional_text(value: str | None, field_name: str, error_type: type[ValueError]) -> None:
    if value is not None:
        _text(value, field_name, error_type)


def _reasons(value: tuple[str, ...], error_type: type[ValueError]) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise error_type("reason_codes must be a tuple")
    for reason in value:
        _text(reason, "reason_code", error_type)
        if _REASON_CODE.fullmatch(reason) is None:
            raise error_type("reason_code must be a stable code")
    if len(value) != len(set(value)):
        raise error_type("reason_codes must not contain duplicates")
    return tuple(sorted(value))


def _count(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InvalidReceiptCounts(f"{field_name} must be a non-negative integer")
    return value


@dataclass(frozen=True, slots=True)
class GovernanceAuthorizationConsumptionReceipt:
    schema_version: str
    claim_id: str
    lifecycle_id: str
    authorization_id: str
    mutation_budget_id: str
    execution_request_id: str
    consumed_at: datetime
    transaction_status: ConsumptionTransactionStatus
    replay_sequence: int | None = None
    replay_hash: str | None = None

    def __post_init__(self) -> None:
        for name in ("schema_version", "claim_id", "lifecycle_id", "authorization_id",
                     "mutation_budget_id", "execution_request_id"):
            _text(getattr(self, name), name, InvalidReceiptModel)
        object.__setattr__(self, "consumed_at", _utc(self.consumed_at, "consumed_at", InvalidReceiptModel))
        if self.transaction_status is not ConsumptionTransactionStatus.COMMITTED:
            raise InvalidReceiptModel("transaction_status must be COMMITTED")
        if self.replay_sequence is not None and (
            isinstance(self.replay_sequence, bool)
            or not isinstance(self.replay_sequence, int)
            or self.replay_sequence < 0
        ):
            raise InvalidReceiptModel("replay_sequence must be a non-negative integer")
        _optional_text(self.replay_hash, "replay_hash", InvalidReceiptModel)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "claim_id": self.claim_id,
            "lifecycle_id": self.lifecycle_id, "authorization_id": self.authorization_id,
            "mutation_budget_id": self.mutation_budget_id,
            "execution_request_id": self.execution_request_id,
            "consumed_at": self.consumed_at.isoformat(),
            "transaction_status": self.transaction_status.value,
            "replay_sequence": self.replay_sequence, "replay_hash": self.replay_hash,
        }


@dataclass(frozen=True, slots=True)
class GovernanceExecutionRequest:
    schema_version: str
    execution_request_id: str
    lifecycle_id: str
    authorization_id: str
    claim_id: str
    mutation_budget_id: str
    action_type: str
    target: str
    plan_digest: str
    requested_at: datetime

    def __post_init__(self) -> None:
        for name in ("schema_version", "execution_request_id", "lifecycle_id",
                     "authorization_id", "claim_id", "mutation_budget_id", "action_type",
                     "target", "plan_digest"):
            _text(getattr(self, name), name, InvalidReceiptModel)
        if self.action_type in _GENERIC_ACTION_TYPES or _ACTION_TYPE.fullmatch(self.action_type) is None:
            raise InvalidReceiptModel("action_type must be an explicit stable capability identifier")
        object.__setattr__(self, "requested_at", _utc(self.requested_at, "requested_at", InvalidReceiptModel))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "execution_request_id": self.execution_request_id,
            "lifecycle_id": self.lifecycle_id, "authorization_id": self.authorization_id,
            "claim_id": self.claim_id, "mutation_budget_id": self.mutation_budget_id,
            "action_type": self.action_type, "target": self.target,
            "plan_digest": self.plan_digest, "requested_at": self.requested_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class GovernanceExecutionReceipt:
    schema_version: str
    receipt_id: str
    lifecycle_id: str
    execution_request_id: str
    authorization_id: str
    claim_id: str
    mutation_budget_id: str
    action_type: str
    status: ExecutionStatus
    actual_invocation_count: int
    completed_count: int
    uncertain_count: int
    started_at: datetime
    completed_at: datetime | None
    result_digest: str | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("schema_version", "receipt_id", "lifecycle_id", "execution_request_id",
                     "authorization_id", "claim_id", "mutation_budget_id", "action_type"):
            _text(getattr(self, name), name, InvalidReceiptModel)
        if self.action_type in _GENERIC_ACTION_TYPES or _ACTION_TYPE.fullmatch(self.action_type) is None:
            raise InvalidReceiptModel("action_type must be an explicit stable capability identifier")
        if not isinstance(self.status, ExecutionStatus):
            raise InvalidReceiptModel("status must be ExecutionStatus")
        for name in ("actual_invocation_count", "completed_count", "uncertain_count"):
            _count(getattr(self, name), name)
        if self.completed_count > self.actual_invocation_count:
            raise InvalidReceiptCounts("completed_count exceeds actual_invocation_count")
        if self.uncertain_count > self.actual_invocation_count:
            raise InvalidReceiptCounts("uncertain_count exceeds actual_invocation_count")
        if self.completed_count + self.uncertain_count > self.actual_invocation_count:
            raise InvalidReceiptCounts("completed_count plus uncertain_count exceeds actual_invocation_count")
        object.__setattr__(self, "started_at", _utc(self.started_at, "started_at", InvalidReceiptModel))
        if self.completed_at is not None:
            completed = _utc(self.completed_at, "completed_at", InvalidReceiptModel)
            if completed < self.started_at:
                raise InvalidReceiptModel("completed_at must not precede started_at")
            object.__setattr__(self, "completed_at", completed)
        _optional_text(self.result_digest, "result_digest", InvalidReceiptModel)
        object.__setattr__(self, "reason_codes", _reasons(self.reason_codes, InvalidReceiptModel))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "receipt_id": self.receipt_id,
            "lifecycle_id": self.lifecycle_id, "execution_request_id": self.execution_request_id,
            "authorization_id": self.authorization_id, "claim_id": self.claim_id,
            "mutation_budget_id": self.mutation_budget_id, "action_type": self.action_type,
            "status": self.status.value, "actual_invocation_count": self.actual_invocation_count,
            "completed_count": self.completed_count, "uncertain_count": self.uncertain_count,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result_digest": self.result_digest, "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True, slots=True)
class GovernancePostconditionReport:
    schema_version: str
    report_id: str
    lifecycle_id: str
    execution_receipt_id: str
    validator_id: str
    decision: PostconditionDecision
    reason_codes: tuple[str, ...]
    expected_state_reference: str
    observed_state_reference: str
    report_digest: str
    evaluated_at: datetime

    def __post_init__(self) -> None:
        for name in ("schema_version", "report_id", "lifecycle_id", "execution_receipt_id",
                     "validator_id", "expected_state_reference", "observed_state_reference",
                     "report_digest"):
            _text(getattr(self, name), name, InvalidPostconditionModel)
        if not isinstance(self.decision, PostconditionDecision):
            raise InvalidPostconditionModel("decision must be PostconditionDecision")
        object.__setattr__(self, "reason_codes", _reasons(self.reason_codes, InvalidPostconditionModel))
        object.__setattr__(self, "evaluated_at", _utc(self.evaluated_at, "evaluated_at", InvalidPostconditionModel))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "report_id": self.report_id,
            "lifecycle_id": self.lifecycle_id, "execution_receipt_id": self.execution_receipt_id,
            "validator_id": self.validator_id, "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "expected_state_reference": self.expected_state_reference,
            "observed_state_reference": self.observed_state_reference,
            "report_digest": self.report_digest, "evaluated_at": self.evaluated_at.isoformat(),
        }
