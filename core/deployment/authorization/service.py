"""Deterministic, default-deny DPL-03C approval and authorization services."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

from core.deployment.contracts import (
    load_schema_registry,
    sha256_digest,
    validate_contract_payload,
)
from core.deployment.planning.validation import validate_deployment_plan

from core.deployment.authorization.ports import (
    ApprovalEvidenceVerifier,
    NonceReplayGuard,
)

_FORBIDDEN_KEYS = {
    "argv", "command", "credential", "password", "private_key", "script",
    "secret", "shell", "ssh_command", "token",
}


class AuthorizationInputError(ValueError):
    """Raised without reflecting potentially sensitive input content."""


def _security_check(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise AuthorizationInputError("unsafe or unsupported authorization input")
            normalized = key.lower()
            if normalized in _FORBIDDEN_KEYS or any(
                marker in normalized
                for marker in ("credential", "secret_key", "_password", "_secret", "_token")
            ):
                raise AuthorizationInputError("unsafe or unsupported authorization input")
            _security_check(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            _security_check(child)
    elif isinstance(value, str):
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts:
            raise AuthorizationInputError("unsafe or unsupported authorization input")


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as error:
        raise AuthorizationInputError("invalid authorization timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AuthorizationInputError("invalid authorization timestamp")
    return parsed.astimezone(timezone.utc)


def _stable_id(prefix: str, value: Mapping[str, Any]) -> str:
    return prefix + sha256_digest(value)[7:39]


def _validate(name: str, value: Mapping[str, Any]) -> None:
    validate_contract_payload(
        registry=load_schema_registry(), contract_name=name, payload=value
    )


def create_approval_request(
    *,
    plan: Mapping[str, Any],
    environment: str,
    requested_action_scope: Sequence[str],
    requester_identity: str,
    approver_identity: str,
    context_identity: str,
    reason: str,
    requested_timestamp: str,
    issued_timestamp: str,
    expiry_timestamp: str,
    nonce: str,
    maximum_uses: int = 1,
    production_requested: bool = False,
) -> dict[str, Any]:
    """Create a deterministic request; timestamps and nonce are caller inputs."""
    _security_check(
        {
            "plan": plan, "environment": environment,
            "requested_action_scope": requested_action_scope,
            "requester_identity": requester_identity,
            "approver_identity": approver_identity,
            "context_identity": context_identity, "reason": reason,
            "requested_timestamp": requested_timestamp,
            "issued_timestamp": issued_timestamp, "expiry_timestamp": expiry_timestamp,
            "nonce": nonce,
        }
    )
    plan_copy = copy.deepcopy(dict(plan))
    validate_deployment_plan(plan_copy)
    issued, requested, expiry = (
        _timestamp(issued_timestamp), _timestamp(requested_timestamp),
        _timestamp(expiry_timestamp),
    )
    if requested != issued or expiry <= issued:
        raise AuthorizationInputError("invalid approval request timestamp ordering")
    scope = sorted(set(requested_action_scope))
    available = {item["action_id"] for item in plan_copy["actions"]}
    if not scope or set(scope) - available:
        raise AuthorizationInputError("approval scope does not match plan")
    semantic = {
        "schema_version": "dpl/v1",
        "package_digest": plan_copy["package_digest"],
        "plan_digest": plan_copy["plan_digest"],
        "target_identity": plan_copy["target_identity"],
        "environment": environment,
        "requested_action_scope": scope,
        "requester_identity": requester_identity,
        "approver_identity": approver_identity,
        "context_identity": context_identity,
        "reason": reason,
        "requested_timestamp": requested_timestamp,
        "issued_timestamp": issued_timestamp,
        "expiry_timestamp": expiry_timestamp,
        "nonce": nonce,
        "maximum_uses": maximum_uses,
        "production_requested": production_requested,
        "execution_authorized": False,
    }
    request = {"request_id": _stable_id("apr-", semantic), **semantic}
    _validate("ApprovalRequest", request)
    return request


def create_approval_decision(
    *,
    request: Mapping[str, Any],
    decision: str,
    decision_reason: str,
    issued_timestamp: str,
    expiry_timestamp: str,
    nonce: str,
    approver_identity: str,
    maximum_uses: int = 1,
    production_authorized: bool = False,
) -> dict[str, Any]:
    """Record approval evidence without granting execution capability."""
    _security_check(
        {
            "request": request, "decision": decision, "decision_reason": decision_reason,
            "issued_timestamp": issued_timestamp, "expiry_timestamp": expiry_timestamp,
            "nonce": nonce, "approver_identity": approver_identity,
        }
    )
    request_copy = copy.deepcopy(dict(request))
    _validate("ApprovalRequest", request_copy)
    issued, expiry = _timestamp(issued_timestamp), _timestamp(expiry_timestamp)
    if expiry <= issued or approver_identity != request_copy["approver_identity"]:
        raise AuthorizationInputError("approval decision binding mismatch")
    semantic = {
        "schema_version": "dpl/v1",
        "request_id": request_copy["request_id"],
        "package_digest": request_copy["package_digest"],
        "plan_digest": request_copy["plan_digest"],
        "target_identity": request_copy["target_identity"],
        "environment": request_copy["environment"],
        "action_scope": list(request_copy["requested_action_scope"]),
        "requester_identity": request_copy["requester_identity"],
        "approver_identity": approver_identity,
        "decision": decision,
        "decision_reason": decision_reason,
        "issued_timestamp": issued_timestamp,
        "expiry_timestamp": expiry_timestamp,
        "nonce": nonce,
        "maximum_uses": maximum_uses,
        "production_authorized": production_authorized,
        "execution_authorized": False,
    }
    result = {"decision_id": _stable_id("apd-", semantic), **semantic}
    _validate("ApprovalDecision", result)
    return result


def materialize_execution_authorization(
    *,
    request: Mapping[str, Any],
    decision: Mapping[str, Any],
    plan: Mapping[str, Any],
    now: str,
    verifier: ApprovalEvidenceVerifier | None,
    replay_guard: NonceReplayGuard | None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Validate evidence and return an unconsumed, one-use capability or denial."""
    request_copy = copy.deepcopy(dict(request))
    decision_copy = copy.deepcopy(dict(decision))
    plan_copy = copy.deepcopy(dict(plan))
    reasons: list[str] = []
    status = "DENIED"
    try:
        _security_check({"request": request_copy, "decision": decision_copy, "plan": plan_copy})
        _validate("ApprovalRequest", request_copy)
        _validate("ApprovalDecision", decision_copy)
        validate_deployment_plan(plan_copy)
        current = _timestamp(now)
        issued = _timestamp(decision_copy["issued_timestamp"])
        expiry = _timestamp(decision_copy["expiry_timestamp"])
    except Exception:
        reasons.append("INVALID_INPUT")
        status = "INVALID"
        current = issued = expiry = None

    if not reasons:
        bindings = (
            ("REQUEST_ID_MISMATCH", decision_copy["request_id"], request_copy["request_id"]),
            ("PACKAGE_DIGEST_MISMATCH", decision_copy["package_digest"], plan_copy["package_digest"]),
            ("PACKAGE_DIGEST_MISMATCH", decision_copy["package_digest"], request_copy["package_digest"]),
            ("PLAN_DIGEST_MISMATCH", decision_copy["plan_digest"], plan_copy["plan_digest"]),
            ("PLAN_DIGEST_MISMATCH", decision_copy["plan_digest"], request_copy["plan_digest"]),
            ("TARGET_IDENTITY_MISMATCH", decision_copy["target_identity"], plan_copy["target_identity"]),
            ("TARGET_IDENTITY_MISMATCH", decision_copy["target_identity"], request_copy["target_identity"]),
            ("ACTION_SCOPE_MISMATCH", decision_copy["action_scope"], request_copy["requested_action_scope"]),
            ("REQUESTER_IDENTITY_MISMATCH", decision_copy["requester_identity"], request_copy["requester_identity"]),
            ("APPROVER_IDENTITY_MISMATCH", decision_copy["approver_identity"], request_copy["approver_identity"]),
            ("ENVIRONMENT_MISMATCH", decision_copy["environment"], request_copy["environment"]),
        )
        reasons.extend(code for code, left, right in bindings if left != right)
        if decision_copy["decision"] != "APPROVED":
            reasons.append("DECISION_NOT_APPROVED")
        if decision_copy["requester_identity"] == decision_copy["approver_identity"]:
            reasons.append("REQUESTER_APPROVER_SEPARATION_FAILED")
        if plan_copy["overall_status"] != "READY_FOR_APPROVAL":
            reasons.append("PLAN_NOT_READY_FOR_APPROVAL")
        if plan_copy["risk_level"] == "CRITICAL" or any(
            action["risk"] == "CRITICAL" for action in plan_copy["actions"]
        ):
            reasons.append("PLAN_CONTAINS_CRITICAL_RISK")
        if issued is not None and current is not None and issued > current:
            reasons.append("ISSUED_IN_FUTURE")
        if expiry is not None and current is not None and expiry <= current:
            reasons.append("AUTHORIZATION_EXPIRED")
            status = "EXPIRED"
        if verifier is None:
            reasons.append("VERIFIER_UNAVAILABLE")
            status = "INCOMPLETE"
        elif not verifier.verify(decision_copy):
            reasons.append("APPROVAL_EVIDENCE_INVALID")
        if replay_guard is None:
            reasons.append("REPLAY_GUARD_UNAVAILABLE")
            status = "INCOMPLETE"
        elif replay_guard.was_consumed(decision_copy["nonce"]):
            reasons.append("NONCE_REPLAYED")
            status = "REPLAYED"

    reasons = sorted(set(reasons))
    authorization: dict[str, Any] | None = None
    if not reasons:
        semantic = {
            "schema_version": "dpl/v1",
            "request_id": request_copy["request_id"],
            "decision_id": decision_copy["decision_id"],
            "package_digest": decision_copy["package_digest"],
            "plan_digest": decision_copy["plan_digest"],
            "target_identity": decision_copy["target_identity"],
            "environment": decision_copy["environment"],
            "action_scope": list(decision_copy["action_scope"]),
            "requester_identity": decision_copy["requester_identity"],
            "approver_identity": decision_copy["approver_identity"],
            "nonce": decision_copy["nonce"],
            "issued_timestamp": decision_copy["issued_timestamp"],
            "expiry_timestamp": decision_copy["expiry_timestamp"],
            "maximum_uses": 1,
            "execution_authorized": True,
            "production_authorized": False,
            "executor_invoked": False,
            "production_writes": 0,
            "ubuntu_changes": 0,
        }
        authorization = {
            "authorization_id": _stable_id("exa-", semantic), **semantic
        }
        _validate("ExecutionAuthorization", authorization)
        status = "AUTHORIZED"
    report = {
        "schema_version": "dpl/v1",
        "status": status,
        "reason_codes": reasons,
        "request_id": request_copy.get("request_id", "apr-" + "0" * 32),
        "decision_id": decision_copy.get("decision_id"),
        "authorization_id": authorization["authorization_id"] if authorization else None,
        "authorization_digest": sha256_digest(authorization) if authorization else None,
        "execution_authorized": authorization is not None,
        "production_authorized": False,
        "executor_invoked": False,
        "production_writes": 0,
        "ubuntu_changes": 0,
    }
    _validate("AuthorizationValidationReport", report)
    return authorization, report


__all__ = (
    "AuthorizationInputError",
    "create_approval_decision",
    "create_approval_request",
    "materialize_execution_authorization",
)
