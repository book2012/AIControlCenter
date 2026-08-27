"""Reconstruct signed immutable Governance facts without consuming or executing."""

from __future__ import annotations

from datetime import datetime, timezone
from collections.abc import Mapping, Sequence
from typing import Any

from ..domain.authorization import (AuthorizationDecision, AuthorizationState, GovernanceAuthorization,
    GovernanceAuthorizationDecision, GovernanceAuthorizationReceipt, GovernanceAuthorizationRequest)
from ..domain.identity import GovernanceIdentity
from ..domain.mutation_budget import GovernanceMutationBudget, MutationBudgetLineItem, MutationBudgetStatus
from ..domain.receipts import GovernanceExecutionRequest
from ..ports.authorization_consumption import AuthorizationConsumptionCommand
from .models import IntakeError, TrustedAuthorizationFacts, VerifiedAuthorizationEvidence
from .operator_identity import TrustedMacOperatorObserver, observe_operator
from .operator_identity import ProductionMacOperatorObserver
from .path_policy import read_trust_registry
from .verification import verify_authorization_envelope

_PROTECTED_FIELDS = frozenset({"envelope_version","key_id","issuer_id","algorithm","authorization_request",
    "authorization_decision","authorization_receipt","mutation_budget","execution_intent","expected_operator",
    "lifecycle_id","request_id","decision_id","authorization_id","mutation_budget_id","execution_request_id",
    "claim_id","action_type","target","plan_digest","expected_precondition_snapshot_digest","approved_scope",
    "expires_at","allowed_invocation_count"})
_REQUEST = frozenset({"schema_version","request_id","lifecycle_id","requester","operation_type","target","environment","reason","requested_scope","requested_mutation_budget_id","requested_at"})
_DECISION = frozenset({"schema_version","decision_id","request_id","approver","decision","reason_codes","decided_at","expiry","approved_scope","approved_mutation_budget_id","precondition_snapshot_digest"})
_RECEIPT = frozenset({"schema_version","authorization_id","request_id","decision_id","lifecycle_id","state","approved_scope","mutation_budget_id","precondition_snapshot_digest","issued_at","expires_at"})
_BUDGET = frozenset({"schema_version","budget_id","authorization_id","status","line_items","remaining_count","violation_reason_code"})
_LINE = frozenset({"action_type","allowed_count","actual_invocation_count","completed_count","uncertain_count","remaining_count","status"})
_EXECUTION = frozenset({"schema_version","execution_request_id","lifecycle_id","authorization_id","claim_id","mutation_budget_id","action_type","target","plan_digest","requested_at"})
_IDENTITY = frozenset({"identity_id","identity_type"})


def _exact(value: Any, fields: frozenset[str], name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or frozenset(value) != fields:
        raise IntakeError(f"{name} fields are not exact")
    return dict(value)


def _identity(value: Any, name: str) -> GovernanceIdentity:
    item = _exact(value, _IDENTITY, name)
    return GovernanceIdentity(item["identity_id"], item["identity_type"])


def _time(value: Any) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise IntakeError("time must be canonical UTC")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
    except ValueError as error:
        raise IntakeError("invalid time") from error


def intake_trusted_authorization(raw_envelope: bytes) -> TrustedAuthorizationFacts:
    """Production authority-producing intake; raw signed envelope is its only input."""
    return _intake_trusted_authorization(
        raw_envelope,
        registry_reader=read_trust_registry,
        clock=lambda: datetime.now(timezone.utc),
        operator_observer=ProductionMacOperatorObserver(),
    )


def _intake_trusted_authorization(
    raw_envelope: bytes,
    *,
    registry_reader: Any,
    clock: Any,
    operator_observer: TrustedMacOperatorObserver,
) -> TrustedAuthorizationFacts:
    """Deterministic test seam for the internally composed Production path."""
    if not isinstance(raw_envelope, bytes):
        raise IntakeError("raw signed envelope must be bytes")
    evidence = verify_authorization_envelope(
        raw_envelope, registry_reader(), now=clock()
    )
    return _reconstruct_verified_facts(evidence, operator_observer=operator_observer)


def _reconstruct_verified_facts(
    evidence: VerifiedAuthorizationEvidence,
    *,
    operator_observer: TrustedMacOperatorObserver,
) -> TrustedAuthorizationFacts:
    p = _exact(dict(evidence.protected), _PROTECTED_FIELDS, "protected")
    r, d, rc = _exact(p["authorization_request"], _REQUEST, "request"), _exact(p["authorization_decision"], _DECISION, "decision"), _exact(p["authorization_receipt"], _RECEIPT, "receipt")
    b, x = _exact(p["mutation_budget"], _BUDGET, "mutation_budget"), _exact(p["execution_intent"], _EXECUTION, "execution_intent")
    expected_operator = _identity(p["expected_operator"], "expected_operator")
    observed = observe_operator(operator_observer)
    if observed.governance_identity != expected_operator:
        raise IntakeError("observed operator does not match signed expected operator")
    requester, approver = _identity(r["requester"], "requester"), _identity(d["approver"], "approver")
    identities = {(item.identity_type, item.identity_id) for item in (requester, approver, expected_operator)}
    if len(identities) != 3:
        raise IntakeError("requester, approver, and operator must be pairwise distinct")
    try:
        request = GovernanceAuthorizationRequest(r["schema_version"], r["request_id"], r["lifecycle_id"], requester, r["operation_type"], r["target"], r["environment"], r["reason"], tuple(r["requested_scope"]), r["requested_mutation_budget_id"], _time(r["requested_at"]))
        decision = GovernanceAuthorizationDecision(d["schema_version"], d["decision_id"], d["request_id"], approver, AuthorizationDecision(d["decision"]), tuple(d["reason_codes"]), _time(d["decided_at"]), _time(d["expiry"]) if d["expiry"] else None, tuple(d["approved_scope"]) if d["approved_scope"] else None, d["approved_mutation_budget_id"], d["precondition_snapshot_digest"])
        receipt = GovernanceAuthorizationReceipt(rc["schema_version"], rc["authorization_id"], rc["request_id"], rc["decision_id"], rc["lifecycle_id"], AuthorizationState(rc["state"]), tuple(rc["approved_scope"]), rc["mutation_budget_id"], rc["precondition_snapshot_digest"], _time(rc["issued_at"]), _time(rc["expires_at"]))
        authorization = GovernanceAuthorization(request, AuthorizationState.AUTHORIZED, rc["authorization_id"], decision, receipt)
        if not isinstance(b["line_items"], Sequence) or isinstance(b["line_items"], (str, bytes)) or len(b["line_items"]) != 1:
            raise IntakeError("mutation budget must contain exactly one line item")
        line = _exact(b["line_items"][0], _LINE, "mutation line")
        if (b["status"], line["status"], line["allowed_count"], line["actual_invocation_count"], line["completed_count"], line["uncertain_count"], line["remaining_count"], b["remaining_count"], b["violation_reason_code"]) != ("AVAILABLE","AVAILABLE",1,0,0,0,1,1,None):
            raise IntakeError("mutation budget is not pristine single-invocation authority")
        budget = GovernanceMutationBudget(b["schema_version"], b["budget_id"], b["authorization_id"], (MutationBudgetLineItem(line["action_type"], 1, 0, 0, 0, MutationBudgetStatus.AVAILABLE),), MutationBudgetStatus.AVAILABLE)
        execution = GovernanceExecutionRequest(x["schema_version"], x["execution_request_id"], x["lifecycle_id"], x["authorization_id"], x["claim_id"], x["mutation_budget_id"], x["action_type"], x["target"], x["plan_digest"], _time(x["requested_at"]))
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, IntakeError): raise
        raise IntakeError("signed Governance value reconstruction failed") from error
    bindings = ((p["lifecycle_id"], r["lifecycle_id"], rc["lifecycle_id"], x["lifecycle_id"]),
        (p["request_id"], r["request_id"], d["request_id"], rc["request_id"]), (p["decision_id"], d["decision_id"], rc["decision_id"]),
        (p["authorization_id"], rc["authorization_id"], b["authorization_id"], x["authorization_id"]),
        (p["mutation_budget_id"], r["requested_mutation_budget_id"], d["approved_mutation_budget_id"], rc["mutation_budget_id"], b["budget_id"], x["mutation_budget_id"]),
        (p["execution_request_id"], x["execution_request_id"]), (p["claim_id"], x["claim_id"]),
        (p["action_type"], r["operation_type"], line["action_type"], x["action_type"]), (p["target"], r["target"], x["target"]),
        (p["plan_digest"], x["plan_digest"]), (p["expected_precondition_snapshot_digest"], d["precondition_snapshot_digest"], rc["precondition_snapshot_digest"]),
        (tuple(p["approved_scope"]), tuple(d["approved_scope"]), tuple(rc["approved_scope"])), (p["expires_at"], d["expiry"], rc["expires_at"]),
        (p["allowed_invocation_count"], line["allowed_count"]))
    if any(any(value != group[0] for value in group[1:]) for group in bindings):
        raise IntakeError("signed cross-binding mismatch")
    try:
        AuthorizationConsumptionCommand(authorization, budget, execution)
    except ValueError as error:
        raise IntakeError("facts are incompatible with authorization consumption") from error
    return TrustedAuthorizationFacts(authorization, budget, execution, expected_operator, evidence)
