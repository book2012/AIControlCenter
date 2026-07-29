"""Deterministic default-deny M2-P1 pilot authorization policy."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

from core.deployment.contracts import (
    load_schema_registry,
    validate_contract_payload,
)
from core.deployment.executor_contracts import ExecutorOperation
from core.deployment.m2_readiness import M2ReadinessDecision, M2ReadinessReport

from .models import (
    PilotAuthorizationDecision,
    PilotAuthorizationRequest,
    PilotAuthorizationStatus,
    PilotOperatorApproval,
    PilotPermit,
    PilotPermitValidationReport,
    PilotRestriction,
    canonical_json,
    sha256_digest,
    stable_id,
    validate_safe,
)

MAXIMUM_LIFETIME = timedelta(hours=1)
ALLOWED_ENVIRONMENTS = frozenset({"development", "test", "staging"})
ALLOWED_APPROVER_ROLES = frozenset({"deployment-approver", "security-approver"})
ALLOWED_OPERATIONS = frozenset({
    ExecutorOperation.VERIFY_SANDBOX_TARGET.value,
    ExecutorOperation.PREPARE_SANDBOX.value,
    ExecutorOperation.COLLECT_EXECUTION_EVIDENCE.value,
})
ALLOWED_TARGET_OWNER = "mac-control-plane"
RESTRICTIONS = tuple(sorted(PilotRestriction, key=lambda item: item.value))


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError("invalid timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("invalid timestamp")
    return parsed.astimezone(timezone.utc)


def _digest_shape(value: str) -> bool:
    return (
        isinstance(value, str) and value.startswith("sha256:")
        and len(value) == 71 and all(character in "0123456789abcdef" for character in value[7:])
    )


def _readiness_digest(report: M2ReadinessReport) -> str:
    semantic = report.to_dict()
    semantic.pop("report_id")
    semantic.pop("report_digest")
    return sha256_digest(semantic)


class PilotAuthorizationService:
    """Create policy evidence only; this service cannot activate or consume a permit."""

    def authorize(
        self,
        *,
        request: PilotAuthorizationRequest | None,
        approval: PilotOperatorApproval | None,
        readiness_report: M2ReadinessReport | None,
        execution_authorization: Mapping[str, Any] | None,
        evaluated_at: str,
    ) -> PilotAuthorizationDecision:
        reasons: list[str] = []
        blocked = False
        try:
            now = _timestamp(evaluated_at)
        except ValueError:
            now = datetime.min.replace(tzinfo=timezone.utc)
            reasons.append("MALFORMED_EVIDENCE")
            blocked = True

        if request is None:
            reasons.append("MISSING_REQUEST")
            blocked = True
        if approval is None:
            reasons.append("MISSING_OPERATOR_APPROVAL")
            blocked = True
        if readiness_report is None:
            reasons.append("MISSING_READINESS_EVIDENCE")
            blocked = True
        if execution_authorization is None:
            reasons.append("MISSING_EXECUTION_AUTHORIZATION")
            blocked = True
        if blocked:
            return self._decision(reasons, evaluated_at, None, blocked=True)

        assert request is not None and approval is not None
        assert readiness_report is not None and execution_authorization is not None
        try:
            validate_safe({
                "request": request.to_dict(),
                "approval": approval.to_dict(),
                "readiness_report": readiness_report.to_dict(),
                "execution_evidence": dict(execution_authorization),
            })
            validate_contract_payload(
                registry=load_schema_registry(),
                contract_name="ExecutionAuthorization",
                payload=execution_authorization,
            )
            issued = _timestamp(request.issued_at)
            expires = _timestamp(request.expires_at)
            approval_issued = _timestamp(approval.issued_at)
            approval_expires = _timestamp(approval.expires_at)
        except Exception:
            return self._decision(["MALFORMED_EVIDENCE"], evaluated_at, None, blocked=True)

        if readiness_report.decision is not M2ReadinessDecision.READY_FOR_AUTHORIZED_NON_PRODUCTION_SANDBOX:
            reasons.append("READINESS_NOT_ACCEPTED")
        if request.readiness_report_id != readiness_report.report_id:
            reasons.append("READINESS_REPORT_ID_MISMATCH")
        if request.readiness_report_digest != readiness_report.report_digest:
            reasons.append("READINESS_REPORT_DIGEST_MISMATCH")
        if (
            readiness_report.report_digest != _readiness_digest(readiness_report)
            or readiness_report.report_id != "m2r-" + readiness_report.report_digest[7:39]
        ):
            reasons.append("READINESS_REPORT_INTEGRITY_INVALID")
        auth = execution_authorization
        bindings = (
            ("EXECUTION_AUTHORIZATION_MISMATCH", request.execution_authorization_id, auth["authorization_id"]),
            ("PACKAGE_DIGEST_MISMATCH", request.package_digest, auth["package_digest"]),
            ("PLAN_DIGEST_MISMATCH", request.plan_digest, auth["plan_digest"]),
            ("TARGET_IDENTITY_MISMATCH", request.target_identity, auth["target_identity"]),
            ("ENVIRONMENT_MISMATCH", request.environment, auth["environment"]),
            ("REQUESTER_IDENTITY_MISMATCH", request.requester_identity, auth["requester_identity"]),
        )
        reasons.extend(code for code, left, right in bindings if left != right)
        if not auth["execution_authorized"] or auth["production_authorized"]:
            reasons.append("EXECUTION_AUTHORIZATION_INVALID")
        if auth["maximum_uses"] != 1:
            reasons.append("EXECUTION_AUTHORIZATION_USE_LIMIT_INVALID")
        auth_issued = _timestamp(auth["issued_timestamp"])
        auth_expires = _timestamp(auth["expiry_timestamp"])
        if auth_issued > issued or auth_expires < expires or now >= auth_expires:
            reasons.append("EXECUTION_AUTHORIZATION_VALIDITY_MISMATCH")
        if auth["executor_invoked"] or auth["production_writes"] or auth["ubuntu_changes"]:
            reasons.append("EXECUTION_AUTHORIZATION_INVALID")
        if request.target_owner != ALLOWED_TARGET_OWNER:
            reasons.append("TARGET_OWNER_DENIED")
        if request.environment not in ALLOWED_ENVIRONMENTS:
            reasons.append("ENVIRONMENT_DENIED")
        if not request.operation_scope or set(request.operation_scope) - ALLOWED_OPERATIONS:
            reasons.append("OPERATION_SCOPE_DENIED")
        if not all((
            request.execution_authorization_id, request.readiness_report_id,
            request.readiness_report_digest, request.package_digest, request.plan_digest,
            request.target_identity, request.sandbox_root_identity_digest,
            request.requester_identity, request.operator_identity, request.nonce_reference,
            approval.approver_identity, approval.approver_role, approval.operator_identity,
        )):
            reasons.append("IDENTITY_OR_BINDING_EVIDENCE_MISSING")
        if not all(_digest_shape(item) for item in (
            request.readiness_report_digest, request.package_digest, request.plan_digest,
            request.sandbox_root_identity_digest,
        )):
            reasons.append("DIGEST_EVIDENCE_MALFORMED")
        if request.requester_identity == approval.approver_identity:
            reasons.append("REQUESTER_APPROVER_SEPARATION_FAILED")
        if request.operator_identity == approval.approver_identity:
            reasons.append("OPERATOR_APPROVER_SEPARATION_FAILED")
        if approval.operator_identity != request.operator_identity:
            reasons.append("OPERATOR_IDENTITY_MISMATCH")
        if approval.approver_role not in ALLOWED_APPROVER_ROLES:
            reasons.append("APPROVER_ROLE_DENIED")
        if not approval.approved:
            reasons.append("OPERATOR_APPROVAL_DENIED")
        if approval_issued > issued or approval_expires < expires:
            reasons.append("APPROVAL_VALIDITY_MISMATCH")
        if expires <= issued:
            reasons.append("INVALID_EXPIRATION")
        if expires - issued > MAXIMUM_LIFETIME:
            reasons.append("MAXIMUM_LIFETIME_EXCEEDED")
        if now < issued:
            reasons.append("NOT_YET_VALID")
        if now >= expires:
            reasons.append("REQUEST_EXPIRED")
        if request.max_uses != 1:
            reasons.append("MAX_USES_INVALID")
        if request.production_authorized:
            reasons.append("PRODUCTION_AUTHORIZATION_DENIED")
        if request.pilot_activation_requested:
            reasons.append("PILOT_ACTIVATION_DENIED")
        if request.persistent_sqlite_audit_operational:
            reasons.append("PERSISTENT_SQLITE_AUDIT_CLAIM_DENIED")
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value != 0
            for value in request.safety_counters.values()
        ):
            reasons.append("NONZERO_SAFETY_COUNTER")

        if reasons:
            return self._decision(reasons, evaluated_at, None)
        permit = self._permit(request, approval)
        return self._decision([], evaluated_at, permit)

    @staticmethod
    def _permit(
        request: PilotAuthorizationRequest, approval: PilotOperatorApproval
    ) -> PilotPermit:
        semantic: dict[str, Any] = {
            "execution_authorization_id": request.execution_authorization_id,
            "readiness_report_id": request.readiness_report_id,
            "readiness_report_digest": request.readiness_report_digest,
            "package_digest": request.package_digest,
            "plan_digest": request.plan_digest,
            "target_identity": request.target_identity,
            "target_owner": request.target_owner,
            "environment": request.environment,
            "operation_scope": list(request.operation_scope),
            "sandbox_root_identity_digest": request.sandbox_root_identity_digest,
            "requester_identity": request.requester_identity,
            "operator_identity": request.operator_identity,
            "approver_identity": approval.approver_identity,
            "approver_role": approval.approver_role,
            "nonce_reference": request.nonce_reference,
            "issued_at": request.issued_at,
            "expires_at": request.expires_at,
            "max_uses": 1,
            "production_authorized": False,
            "pilot_activation_started": False,
            "restrictions": [item.value for item in RESTRICTIONS],
        }
        permit_id = stable_id("m2p-", semantic)
        digest = sha256_digest({"permit_id": permit_id, **semantic})
        return PilotPermit(
            permit_id=permit_id, **{**semantic, "operation_scope": request.operation_scope,
            "restrictions": RESTRICTIONS}, permit_digest=digest,
        )

    @staticmethod
    def _decision(
        reasons: list[str], evaluated_at: str, permit: PilotPermit | None, *, blocked: bool = False
    ) -> PilotAuthorizationDecision:
        ordered = tuple(sorted(set(reasons)))
        status = (
            PilotAuthorizationStatus.BLOCKED if blocked
            else PilotAuthorizationStatus.DENIED if ordered
            else PilotAuthorizationStatus.AUTHORIZED
        )
        report = PilotPermitValidationReport(
            status=status,
            reason_codes=ordered,
            evaluated_at=evaluated_at,
            permit_id=permit.permit_id if permit else None,
            permit_digest=permit.permit_digest if permit else None,
        )
        return PilotAuthorizationDecision(status, ordered, RESTRICTIONS, permit, report)


__all__ = (
    "ALLOWED_APPROVER_ROLES", "ALLOWED_ENVIRONMENTS", "ALLOWED_OPERATIONS",
    "ALLOWED_TARGET_OWNER", "MAXIMUM_LIFETIME", "PilotAuthorizationService",
    "canonical_json",
)
