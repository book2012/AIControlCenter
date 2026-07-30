"""Pure builder, gate, validator and coordinator for controlled activation."""

from __future__ import annotations

from .models import *


class OperationalActivationAuthorizationValidator:
    def validate(self, *, config: OperationalActivationAuthorizationConfig,
                 permit: OperationalActivationAuthorizationPermit | None,
                 validated_at: str, approval_report_id: str | None = None,
                 approval_report_digest: str | None = None,
                 operator_identity: str | None = None
                 ) -> OperationalActivationAuthorizationValidationReport:
        reasons: list[str] = []
        if not isinstance(permit, OperationalActivationAuthorizationPermit):
            reasons.append("ACTIVATION_AUTHORIZATION_REQUIRED")
        else:
            request = permit.request
            if canonical_digest(permit.content()) != permit.authorization_digest:
                reasons.append("ACTIVATION_AUTHORIZATION_DIGEST_INVALID")
            if request.git.branch != config.approved_branch or request.git.commit != config.approved_commit:
                reasons.append("GIT_BINDING_MISMATCH")
            if request.operational_target_path != config.trusted_operational_path:
                reasons.append("TARGET_PATH_MISMATCH")
            if approval_report_id is not None and request.human_approval_report_id != approval_report_id:
                reasons.append("APPROVAL_BINDING_MISMATCH")
            if approval_report_digest is not None and request.human_approval_report_digest != approval_report_digest:
                reasons.append("APPROVAL_DIGEST_MISMATCH")
            if operator_identity is not None and request.identity.operator_identity != operator_identity:
                reasons.append("IDENTITY_MISMATCH")
            now = parse_timestamp(validated_at)
            if now < parse_timestamp(request.window.not_before):
                reasons.append("ACTIVATION_AUTHORIZATION_NOT_YET_VALID")
            if now >= parse_timestamp(request.window.expires_at):
                reasons.append("ACTIVATION_AUTHORIZATION_EXPIRED")
            if (request.window.maximum_permit_uses != 1
                    or request.environment != "CONTROLLED_NON_PRODUCTION"
                    or request.safety.production_authorized):
                reasons.append("ACTIVATION_SCOPE_INVALID")
        reasons = sorted(set(reasons))
        status = (OperationalActivationAuthorizationStatus.AUTHORIZED if not reasons
                  else OperationalActivationAuthorizationStatus.BLOCKED)
        digest = canonical_digest({"status": status, "reason_codes": reasons,
                                   "validated_at": validated_at})
        return OperationalActivationAuthorizationValidationReport(
            status, tuple(reasons), "m3-a4b2b2b-r2-validation-" + digest[7:39], digest)


class OperationalActivationAuthorizationGate:
    def evaluate(self, *, config: OperationalActivationAuthorizationConfig,
                 request: OperationalActivationAuthorizationRequest,
                 decided_at: str) -> OperationalActivationAuthorizationDecision:
        reasons: list[str] = []
        if request.git.branch != config.approved_branch or request.git.commit != config.approved_commit:
            reasons.append("GIT_BINDING_MISMATCH")
        if request.operational_target_path != config.trusted_operational_path:
            reasons.append("TARGET_PATH_MISMATCH")
        parse_timestamp(decided_at)
        digest = canonical_digest(request.as_dict())
        status = (OperationalActivationAuthorizationStatus.AUTHORIZED if not reasons
                  else OperationalActivationAuthorizationStatus.BLOCKED)
        decision_digest = canonical_digest({"status": status, "reason_codes": reasons,
                                            "request_digest": digest, "decided_at": decided_at})
        return OperationalActivationAuthorizationDecision(
            "m3-a4b2b2b-r2-decision-" + decision_digest[7:39], status,
            tuple(sorted(reasons)), digest, decided_at)


class OperationalActivationAuthorizationBuilder:
    def build(self, *, config: OperationalActivationAuthorizationConfig,
              request: OperationalActivationAuthorizationRequest,
              decided_at: str, issued_at: str
              ) -> tuple[OperationalActivationAuthorizationDecision,
                         OperationalActivationAuthorizationPermit | None]:
        decision = OperationalActivationAuthorizationGate().evaluate(
            config=config, request=request, decided_at=decided_at)
        if decision.status is not OperationalActivationAuthorizationStatus.AUTHORIZED:
            return decision, None
        content = {"authorization_id": "pending", "request": request.as_dict(),
                   "issued_at": issued_at,
                   "stage": OperationalActivationAuthorizationStage.CONTROLLED_NON_PRODUCTION_OPERATIONAL_ACTIVATION}
        seed = canonical_digest(content)
        authorization_id = "m3-a4b2b2b-r2-" + seed[7:39]
        content["authorization_id"] = authorization_id
        return decision, OperationalActivationAuthorizationPermit(
            authorization_id, canonical_digest(content), request, issued_at)


class OperationalActivationAuthorizationCoordinator(OperationalActivationAuthorizationBuilder):
    pass
