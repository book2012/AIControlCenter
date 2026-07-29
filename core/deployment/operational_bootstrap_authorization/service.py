"""Deterministic authorization, permit issuance and validation services."""

from __future__ import annotations

from dataclasses import replace

from core.deployment.operational_activation_gate import ActivationReadinessDecision

from .models import (
    OperationalBootstrapApproval,
    OperationalBootstrapAuthorizationConfig,
    OperationalBootstrapAuthorizationDecision,
    OperationalBootstrapAuthorizationDecisionValue,
    OperationalBootstrapAuthorizationError,
    OperationalBootstrapAuthorizationRequest,
    OperationalBootstrapAuthorizationStage,
    OperationalBootstrapAuthorizationStatus,
    OperationalBootstrapPermit,
    OperationalBootstrapPermitValidationReport,
    canonical_digest,
    parse_timestamp,
)


class OperationalBootstrapAuthorizationService:
    """Pure later decision boundary; it never probes, persists or bootstraps."""

    def authorize(
        self, *, config: OperationalBootstrapAuthorizationConfig,
        request: OperationalBootstrapAuthorizationRequest,
        approval: OperationalBootstrapApproval, decided_at: str,
        issued_at: str, concrete_executor: object | None = None,
        write_requested: bool = False,
    ) -> tuple[OperationalBootstrapAuthorizationDecision, OperationalBootstrapPermit | None]:
        if config is None or request is None or approval is None:
            raise OperationalBootstrapAuthorizationError("configuration and evidence required")
        if concrete_executor is not None or write_requested:
            raise OperationalBootstrapAuthorizationError("executor and writes prohibited")
        parse_timestamp(decided_at)
        reasons = self._reasons(config, request, approval, issued_at)
        if not approval.approved:
            reasons.append("APPROVAL_DENIED")
        reasons = sorted(set(reasons))
        value = (OperationalBootstrapAuthorizationDecisionValue.AUTHORIZED_FOR_CONTROLLED_NON_PRODUCTION_BOOTSTRAP
                 if not reasons else OperationalBootstrapAuthorizationDecisionValue.DENIED
                 if reasons == ["APPROVAL_DENIED"] else
                 OperationalBootstrapAuthorizationDecisionValue.BLOCKED)
        status = (OperationalBootstrapAuthorizationStatus.AUTHORIZED if not reasons
                  else OperationalBootstrapAuthorizationStatus.DENIED
                  if value is OperationalBootstrapAuthorizationDecisionValue.DENIED
                  else OperationalBootstrapAuthorizationStatus.BLOCKED)
        request_digest = canonical_digest({
            "authorization_request_id": request.authorization_request_id,
            "branch": request.branch, "commit": request.commit,
            "readiness_report_digest": request.readiness_report_digest,
            "target_binding_digest": request.target_binding.binding_digest,
            "schema_binding_digest": request.schema_binding.binding_digest,
            "plan_binding_digest": request.plan_binding.binding_digest,
            "safety_snapshot_digest": request.safety_snapshot.snapshot_digest,
            "acknowledgements": [item.as_dict() for item in request.restriction_acknowledgements],
            "requester_identity": request.requester_identity,
            "operator_identity": request.operator_identity,
            "approver_identity": request.approver_identity,
            "requested_at": request.requested_at, "expires_at": request.expires_at,
            "maximum_uses": request.maximum_uses, "environment": request.environment,
            "production_authorized": request.production_authorized,
        })
        decision_content = {
            "status": status.value, "decision": value.value,
            "reason_codes": reasons, "authorization_request_id": request.authorization_request_id,
            "request_digest": request_digest, "decided_at": decided_at,
            "production_authorized": False,
        }
        decision_digest = canonical_digest(decision_content)
        decision = OperationalBootstrapAuthorizationDecision(
            "m3-a4b1-decision-" + decision_digest[7:39], status, value, tuple(reasons),
            request.authorization_request_id, request_digest, decided_at)
        if reasons:
            return decision, None
        permit_content = {
            "authorization_request_id": request.authorization_request_id,
            "authorization_decision_id": decision.decision_id,
            "stage": config.stage, "branch": request.branch, "commit": request.commit,
            "readiness_report_id": request.readiness_report.report_id,
            "readiness_report_digest": request.readiness_report_digest,
            "restriction_acknowledgement_digest": canonical_digest(
                [item.as_dict() for item in request.restriction_acknowledgements]),
            "target_binding_digest": request.target_binding.binding_digest,
            "schema_binding_digest": request.schema_binding.binding_digest,
            "plan_binding_digest": request.plan_binding.binding_digest,
            "safety_snapshot_digest": request.safety_snapshot.snapshot_digest,
            "requester_identity": request.requester_identity,
            "operator_identity": request.operator_identity,
            "approver_identity": request.approver_identity,
            "issued_at": issued_at, "expires_at": request.expires_at,
            "maximum_uses": 1, "environment": "controlled non-production",
            "bootstrap_authorized": True, "writers_authorized": False,
            "monitoring_authorized": False, "external_dispatch_authorized": False,
            "production_authorized": False,
        }
        identity_digest = canonical_digest(permit_content)
        permit_id = "m3-a4b1-permit-" + identity_digest[7:39]
        content = {"permit_id": permit_id, **permit_content}
        return decision, OperationalBootstrapPermit(
            **content, permit_digest=canonical_digest(content))

    @staticmethod
    def _reasons(config, request, approval, issued_at):
        reasons: list[str] = []
        report = request.readiness_report
        if request.readiness_report_digest != report.report_digest:
            reasons.append("READINESS_REPORT_DIGEST_INVALID")
        if report.readiness_decision not in (
                ActivationReadinessDecision.READY_WITH_RESTRICTIONS,
                ActivationReadinessDecision.READY_FOR_CONTROLLED_NON_PRODUCTION_BOOTSTRAP):
            reasons.append("READINESS_DECISION_INVALID")
        if report.failed_checks:
            reasons.append("READINESS_FAILED_CHECKS")
        if report.bootstrap_authorized or report.production_authorized:
            reasons.append("READINESS_AUTHORIZATION_CONTRADICTION")
        expected = {item.code: item for item in report.restrictions}
        actual = {item.restriction_code: item for item in request.restriction_acknowledgements}
        if set(expected) != set(actual):
            reasons.append("RESTRICTION_ACKNOWLEDGEMENT_INCOMPLETE")
        else:
            for code, restriction in expected.items():
                acknowledgement = actual[code]
                if (acknowledgement.restriction_text != restriction.summary
                        or acknowledgement.restriction_digest != canonical_digest(restriction.as_dict())
                        or acknowledgement.operator_identity != request.operator_identity
                        or acknowledgement.approver_identity != request.approver_identity):
                    reasons.append("RESTRICTION_ACKNOWLEDGEMENT_INVALID")
        if (request.branch != config.approved_branch or request.commit != approval.commit
                or request.branch != approval.branch):
            reasons.append("GIT_BINDING_INVALID")
        if (request.operator_identity != approval.operator_identity
                or request.approver_identity != approval.approver_identity
                or request.operator_identity == request.approver_identity):
            reasons.append("APPROVAL_IDENTITY_INVALID")
        if request.requester_identity == request.operator_identity and (
                request.requester_identity == request.approver_identity):
            reasons.append("SELF_APPROVAL_REJECTED")
        approved = parse_timestamp(approval.approved_at)
        issued = parse_timestamp(issued_at)
        expires = parse_timestamp(request.expires_at)
        if issued < approved or expires <= approved or expires <= issued:
            reasons.append("PERMIT_EXPIRY_INVALID")
        if (approval.environment != config.environment or approval.production_authorized
                or request.production_authorized):
            reasons.append("SCOPE_INVALID")
        return reasons


class OperationalBootstrapPermitValidator:
    def validate(
        self, *, permit: OperationalBootstrapPermit,
        request: OperationalBootstrapAuthorizationRequest,
        decision: OperationalBootstrapAuthorizationDecision,
        validated_at: str, branch: str, commit: str,
    ) -> OperationalBootstrapPermitValidationReport:
        now = parse_timestamp(validated_at)
        reasons: list[str] = []
        if canonical_digest(permit.content()) != permit.permit_digest:
            reasons.append("PERMIT_DIGEST_INVALID")
        if (permit.authorization_request_id != request.authorization_request_id
                or permit.authorization_decision_id != decision.decision_id):
            reasons.append("REQUEST_DECISION_BINDING_INVALID")
        if permit.branch != branch or permit.commit != commit:
            reasons.append("GIT_BINDING_INVALID")
        if (permit.readiness_report_id != request.readiness_report.report_id
                or permit.readiness_report_digest != request.readiness_report_digest):
            reasons.append("READINESS_BINDING_INVALID")
        expected = {
            "restriction_acknowledgement_digest": canonical_digest(
                [item.as_dict() for item in request.restriction_acknowledgements]),
            "target_binding_digest": request.target_binding.binding_digest,
            "schema_binding_digest": request.schema_binding.binding_digest,
            "plan_binding_digest": request.plan_binding.binding_digest,
            "safety_snapshot_digest": request.safety_snapshot.snapshot_digest,
        }
        if any(getattr(permit, key) != value for key, value in expected.items()):
            reasons.append("CONTRACT_BINDING_INVALID")
        if (permit.requester_identity != request.requester_identity
                or permit.operator_identity != request.operator_identity
                or permit.approver_identity != request.approver_identity):
            reasons.append("IDENTITY_BINDING_INVALID")
        if now < parse_timestamp(permit.issued_at) or now >= parse_timestamp(permit.expires_at):
            reasons.append("PERMIT_EXPIRED_OR_NOT_YET_VALID")
        if (permit.stage is not OperationalBootstrapAuthorizationStage.CONTROLLED_NON_PRODUCTION_BOOTSTRAP_AUTHORIZATION
                or permit.maximum_uses != 1 or permit.environment != "controlled non-production"
                or not permit.bootstrap_authorized or permit.writers_authorized
                or permit.monitoring_authorized or permit.external_dispatch_authorized
                or permit.production_authorized):
            reasons.append("PERMIT_SCOPE_INVALID")
        reasons = sorted(set(reasons))
        content = {"valid": not reasons, "reason_codes": reasons,
                   "permit_id": permit.permit_id, "validated_at": validated_at}
        digest = canonical_digest(content)
        return OperationalBootstrapPermitValidationReport(
            "m3-a4b1-validation-" + digest[7:39], not reasons, tuple(reasons),
            permit.permit_id, validated_at, digest)
