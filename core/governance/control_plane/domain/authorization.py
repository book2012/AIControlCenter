"""Pure immutable SEC-02 authorization models and state transitions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any

from .failures import (
    ApprovalRequired,
    AuthorizationBindingMismatch,
    InvalidAuthorizationInput,
    InvalidAuthorizationTransition,
    RequestDecisionBindingMismatch,
    TerminalAuthorizationReuse,
)
from .identity import GovernanceIdentity, require_text


class AuthorizationState(StrEnum):
    REQUESTED = "REQUESTED"
    AUTHORIZED = "AUTHORIZED"
    STALE = "STALE"
    CONSUMED = "CONSUMED"
    REJECTED = "REJECTED"


class AuthorizationDecision(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


TERMINAL_STATES = frozenset(
    {AuthorizationState.STALE, AuthorizationState.CONSUMED, AuthorizationState.REJECTED}
)
ALLOWED_TRANSITIONS = frozenset(
    {
        (AuthorizationState.REQUESTED, AuthorizationState.AUTHORIZED),
        (AuthorizationState.REQUESTED, AuthorizationState.REJECTED),
        (AuthorizationState.AUTHORIZED, AuthorizationState.STALE),
        (AuthorizationState.AUTHORIZED, AuthorizationState.CONSUMED),
    }
)


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise InvalidAuthorizationInput(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise InvalidAuthorizationInput(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(timezone.utc)


def _scope(value: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not value:
        raise InvalidAuthorizationInput(f"{field_name} must not be empty")
    for item in value:
        require_text(item, field_name)
    if len(set(value)) != len(value):
        raise InvalidAuthorizationInput(f"{field_name} must not contain duplicates")
    return value


@dataclass(frozen=True, slots=True)
class GovernanceAuthorizationRequest:
    schema_version: str
    request_id: str
    lifecycle_id: str
    requester: GovernanceIdentity
    operation_type: str
    target: str
    environment: str
    reason: str
    requested_scope: tuple[str, ...]
    requested_mutation_budget_id: str
    requested_at: datetime

    def __post_init__(self) -> None:
        for name in (
            "schema_version", "request_id", "lifecycle_id", "operation_type",
            "target", "environment", "reason", "requested_mutation_budget_id",
        ):
            require_text(getattr(self, name), name)
        if not isinstance(self.requester, GovernanceIdentity):
            raise InvalidAuthorizationInput("requester must be GovernanceIdentity")
        _scope(self.requested_scope, "requested_scope")
        object.__setattr__(self, "requested_at", _utc(self.requested_at, "requested_at"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "request_id": self.request_id,
            "lifecycle_id": self.lifecycle_id, "requester": self.requester.to_dict(),
            "operation_type": self.operation_type, "target": self.target,
            "environment": self.environment, "reason": self.reason,
            "requested_scope": list(self.requested_scope),
            "requested_mutation_budget_id": self.requested_mutation_budget_id,
            "requested_at": self.requested_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class GovernanceAuthorizationDecision:
    schema_version: str
    decision_id: str
    request_id: str
    approver: GovernanceIdentity
    decision: AuthorizationDecision
    reason_codes: tuple[str, ...]
    decided_at: datetime
    expiry: datetime | None
    approved_scope: tuple[str, ...] | None
    approved_mutation_budget_id: str | None
    precondition_snapshot_digest: str | None

    def __post_init__(self) -> None:
        for name in ("schema_version", "decision_id", "request_id"):
            require_text(getattr(self, name), name)
        if not isinstance(self.approver, GovernanceIdentity):
            raise InvalidAuthorizationInput("approver must be GovernanceIdentity")
        if not isinstance(self.decision, AuthorizationDecision):
            raise InvalidAuthorizationInput("decision must be AuthorizationDecision")
        _scope(self.reason_codes, "reason_codes")
        object.__setattr__(self, "decided_at", _utc(self.decided_at, "decided_at"))
        if self.expiry is not None:
            object.__setattr__(self, "expiry", _utc(self.expiry, "expiry"))
        if self.decision is AuthorizationDecision.APPROVED:
            if self.expiry is None:
                raise InvalidAuthorizationInput("approved decision requires expiry")
            if self.expiry <= self.decided_at:
                raise InvalidAuthorizationInput("expiry must follow decided_at")
            if self.approved_scope is None:
                raise InvalidAuthorizationInput("approved decision requires approved_scope")
            _scope(self.approved_scope, "approved_scope")
            require_text(self.approved_mutation_budget_id, "approved_mutation_budget_id")
            require_text(self.precondition_snapshot_digest, "precondition_snapshot_digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "decision_id": self.decision_id,
            "request_id": self.request_id, "approver": self.approver.to_dict(),
            "decision": self.decision.value, "reason_codes": list(self.reason_codes),
            "decided_at": self.decided_at.isoformat(),
            "expiry": self.expiry.isoformat() if self.expiry else None,
            "approved_scope": list(self.approved_scope) if self.approved_scope else None,
            "approved_mutation_budget_id": self.approved_mutation_budget_id,
            "precondition_snapshot_digest": self.precondition_snapshot_digest,
        }


@dataclass(frozen=True, slots=True)
class GovernanceAuthorizationReceipt:
    schema_version: str
    authorization_id: str
    request_id: str
    decision_id: str
    lifecycle_id: str
    state: AuthorizationState
    approved_scope: tuple[str, ...]
    mutation_budget_id: str
    precondition_snapshot_digest: str
    issued_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        for name in ("schema_version", "authorization_id", "request_id", "decision_id",
                     "lifecycle_id", "mutation_budget_id", "precondition_snapshot_digest"):
            require_text(getattr(self, name), name)
        if self.state not in {AuthorizationState.AUTHORIZED, AuthorizationState.STALE,
                              AuthorizationState.CONSUMED}:
            raise InvalidAuthorizationInput("receipt state must derive from AUTHORIZED")
        _scope(self.approved_scope, "approved_scope")
        object.__setattr__(self, "issued_at", _utc(self.issued_at, "issued_at"))
        object.__setattr__(self, "expires_at", _utc(self.expires_at, "expires_at"))
        if self.expires_at <= self.issued_at:
            raise InvalidAuthorizationInput("expires_at must follow issued_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "authorization_id": self.authorization_id,
            "request_id": self.request_id, "decision_id": self.decision_id,
            "lifecycle_id": self.lifecycle_id, "state": self.state.value,
            "approved_scope": list(self.approved_scope),
            "mutation_budget_id": self.mutation_budget_id,
            "precondition_snapshot_digest": self.precondition_snapshot_digest,
            "issued_at": self.issued_at.isoformat(), "expires_at": self.expires_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class GovernanceAuthorizationStateRecord:
    schema_version: str
    authorization_id: str
    previous_state: AuthorizationState
    current_state: AuthorizationState
    transition_reason: str
    transitioned_at: datetime
    precondition_comparison_digest: str | None = None
    audit_event_id: str | None = None

    def __post_init__(self) -> None:
        require_text(self.schema_version, "schema_version")
        require_text(self.authorization_id, "authorization_id")
        require_text(self.transition_reason, "transition_reason")
        if (self.previous_state, self.current_state) not in ALLOWED_TRANSITIONS:
            raise InvalidAuthorizationTransition("state record transition is not allowed")
        if self.precondition_comparison_digest is not None:
            require_text(self.precondition_comparison_digest, "precondition_comparison_digest")
        if self.audit_event_id is not None:
            require_text(self.audit_event_id, "audit_event_id")
        object.__setattr__(self, "transitioned_at", _utc(self.transitioned_at, "transitioned_at"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "authorization_id": self.authorization_id,
            "previous_state": self.previous_state.value, "current_state": self.current_state.value,
            "transition_reason": self.transition_reason,
            "transitioned_at": self.transitioned_at.isoformat(),
            "precondition_comparison_digest": self.precondition_comparison_digest,
            "audit_event_id": self.audit_event_id,
        }


@dataclass(frozen=True, slots=True)
class GovernanceAuthorization:
    request: GovernanceAuthorizationRequest
    state: AuthorizationState = AuthorizationState.REQUESTED
    authorization_id: str | None = None
    decision: GovernanceAuthorizationDecision | None = None
    receipt: GovernanceAuthorizationReceipt | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.request, GovernanceAuthorizationRequest):
            raise InvalidAuthorizationInput("request must be GovernanceAuthorizationRequest")
        if self.state is AuthorizationState.REQUESTED:
            if any(
                value is not None
                for value in (self.authorization_id, self.decision, self.receipt)
            ):
                raise InvalidAuthorizationInput("requested authorization cannot contain authority")
        elif self.state is AuthorizationState.REJECTED:
            if (
                self.decision is None
                or self.decision.decision is not AuthorizationDecision.REJECTED
            ):
                raise InvalidAuthorizationInput("rejected authorization requires rejected decision")
            if self.decision.request_id != self.request.request_id:
                raise RequestDecisionBindingMismatch("request_id does not match decision binding")
            if self.receipt is not None:
                raise InvalidAuthorizationInput("rejected authorization cannot contain receipt")
        else:
            if self.receipt is None or self.receipt.state is not self.state:
                raise InvalidAuthorizationInput("authorization state must match receipt")
            if (
                self.decision is None
                or self.decision.decision is not AuthorizationDecision.APPROVED
            ):
                raise ApprovalRequired("authority requires an APPROVED decision")
            if self.decision.request_id != self.request.request_id:
                raise RequestDecisionBindingMismatch("request_id does not match decision binding")
            if (
                self.receipt.request_id != self.request.request_id
                or self.receipt.lifecycle_id != self.request.lifecycle_id
                or self.receipt.decision_id != self.decision.decision_id
            ):
                raise AuthorizationBindingMismatch("receipt identity binding does not match")
            if not set(self.receipt.approved_scope).issubset(self.request.requested_scope):
                raise AuthorizationBindingMismatch("receipt scope exceeds requested scope")
            if self.receipt.approved_scope != self.decision.approved_scope:
                raise AuthorizationBindingMismatch("approved scope binding changed")
            if (
                self.receipt.mutation_budget_id != self.request.requested_mutation_budget_id
                or self.receipt.mutation_budget_id != self.decision.approved_mutation_budget_id
            ):
                raise AuthorizationBindingMismatch("mutation budget identity changed")
            if (
                self.receipt.precondition_snapshot_digest
                != self.decision.precondition_snapshot_digest
            ):
                raise AuthorizationBindingMismatch("precondition snapshot digest changed")

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": self.request.to_dict(), "state": self.state.value,
            "authorization_id": self.authorization_id,
            "decision": self.decision.to_dict() if self.decision else None,
            "receipt": self.receipt.to_dict() if self.receipt else None,
        }


@dataclass(frozen=True, slots=True)
class AuthorizationTransitionResult:
    authorization: GovernanceAuthorization
    state_record: GovernanceAuthorizationStateRecord


def transition_authorization(
    current: GovernanceAuthorization,
    next_state: AuthorizationState,
    transition_reason: str,
    transitioned_at: datetime,
    *,
    decision: GovernanceAuthorizationDecision | None = None,
    authorization_id: str | None = None,
    precondition_comparison_digest: str | None = None,
    audit_event_id: str | None = None,
) -> AuthorizationTransitionResult:
    """Return a newly transitioned aggregate and record; never mutate input."""
    require_text(transition_reason, "transition_reason")
    transitioned_at = _utc(transitioned_at, "transitioned_at")
    if current.state in TERMINAL_STATES:
        raise TerminalAuthorizationReuse("terminal authorization cannot transition")
    if (current.state, next_state) not in ALLOWED_TRANSITIONS:
        raise InvalidAuthorizationTransition("requested state transition is not allowed")

    active_id = current.authorization_id
    next_decision = current.decision
    next_receipt = current.receipt
    if current.state is AuthorizationState.REQUESTED:
        if decision is None:
            raise InvalidAuthorizationInput("decision is required for requested transition")
        if decision.request_id != current.request.request_id:
            raise RequestDecisionBindingMismatch("request_id does not match decision binding")
        if next_state is AuthorizationState.AUTHORIZED:
            if decision.decision is not AuthorizationDecision.APPROVED:
                raise ApprovalRequired("AUTHORIZED requires an APPROVED decision")
            active_id = require_text(authorization_id, "authorization_id")
            approved_scope = decision.approved_scope or ()
            if not set(approved_scope).issubset(current.request.requested_scope):
                raise AuthorizationBindingMismatch("approved scope exceeds requested scope")
            if decision.approved_mutation_budget_id != current.request.requested_mutation_budget_id:
                raise AuthorizationBindingMismatch("mutation budget identity changed")
            next_receipt = GovernanceAuthorizationReceipt(
                schema_version=decision.schema_version, authorization_id=active_id,
                request_id=current.request.request_id, decision_id=decision.decision_id,
                lifecycle_id=current.request.lifecycle_id, state=next_state,
                approved_scope=approved_scope,
                mutation_budget_id=decision.approved_mutation_budget_id or "",
                precondition_snapshot_digest=decision.precondition_snapshot_digest or "",
                issued_at=transitioned_at, expires_at=decision.expiry or transitioned_at,
            )
        else:
            if decision.decision is not AuthorizationDecision.REJECTED:
                raise InvalidAuthorizationTransition("REJECTED requires a REJECTED decision")
            active_id = require_text(authorization_id, "authorization_id")
            next_receipt = None
        next_decision = decision
    else:
        active_id = require_text(active_id, "authorization_id")
        if decision is not None or authorization_id is not None:
            raise AuthorizationBindingMismatch("issued authorization bindings cannot change")
        assert next_receipt is not None
        next_receipt = GovernanceAuthorizationReceipt(
            schema_version=next_receipt.schema_version,
            authorization_id=next_receipt.authorization_id,
            request_id=next_receipt.request_id, decision_id=next_receipt.decision_id,
            lifecycle_id=next_receipt.lifecycle_id, state=next_state,
            approved_scope=next_receipt.approved_scope,
            mutation_budget_id=next_receipt.mutation_budget_id,
            precondition_snapshot_digest=next_receipt.precondition_snapshot_digest,
            issued_at=next_receipt.issued_at, expires_at=next_receipt.expires_at,
        )

    record = GovernanceAuthorizationStateRecord(
        schema_version=current.request.schema_version, authorization_id=active_id,
        previous_state=current.state, current_state=next_state,
        transition_reason=transition_reason, transitioned_at=transitioned_at,
        precondition_comparison_digest=precondition_comparison_digest,
        audit_event_id=audit_event_id,
    )
    return AuthorizationTransitionResult(
        authorization=GovernanceAuthorization(
            request=current.request, state=next_state, authorization_id=active_id,
            decision=next_decision, receipt=next_receipt,
        ),
        state_record=record,
    )
