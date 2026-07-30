"""Pure deterministic M3-A4B2B1B approval and in-memory issuance boundary."""

from __future__ import annotations

from dataclasses import asdict, replace

from core.deployment.operational_bootstrap_authorization import (
    OperationalBootstrapAuthorizationConfig,
    OperationalBootstrapAuthorizationService,
    OperationalBootstrapAuthorizationStage,
    canonical_digest,
)
from core.deployment.operational_permit_issuance import (
    OperationalPermitIssuanceValidator,
    parse_timestamp,
)
from core.deployment.operational_activation_authorization import (
    OperationalActivationAuthorizationConfig,
    OperationalActivationAuthorizationPermit,
    OperationalActivationAuthorizationStatus,
    OperationalActivationAuthorizationValidator,
)

from .models import *

CHECK_ORDER = (
    "REVIEW_PACKAGE", "GIT_BINDING", "IDENTITIES", "IDENTITY_INDEPENDENCE",
    "APPROVAL_DECISION", "RESTRICTION_ACKNOWLEDGEMENTS", "EXECUTION_WINDOW",
    "SAFETY", "TARGET_ABSENCE", "PRODUCTION_SCOPE",
)


class OperationalPermitIdentityValidator:
    @staticmethod
    def reasons(value: OperationalPermitApprovalInput) -> list[str]:
        identities = (value.requester, value.mac_operator, value.independent_approver)
        reasons: list[str] = []
        if value.independent_approver is None:
            return ["MISSING_INDEPENDENT_APPROVER"]
        expected = (
            OperationalPermitIdentityRole.REQUESTER, OperationalPermitIdentityRole.MAC_OPERATOR,
            OperationalPermitIdentityRole.INDEPENDENT_APPROVER)
        if any(item.role is not role for item, role in zip(identities, expected)):
            reasons.append("IDENTITY_ROLE_INVALID")
        operator = value.mac_operator
        approver = value.independent_approver
        if operator.identity_id == approver.identity_id:
            reasons.append("OPERATOR_APPROVER_NOT_DISTINCT")
        aliases = {
            item.casefold() for item in (
                operator.identity_id, operator.local_account_binding or "", operator.display_label)
            if item
        }
        approver_aliases = {
            item.casefold() for item in (
                approver.identity_id, approver.local_account_binding or "", approver.display_label)
            if item
        }
        if aliases & approver_aliases:
            reasons.append("OPERATOR_APPROVER_ALIAS_OVERLAP")
        if value.requester.identity_id == approver.identity_id:
            reasons.append("SELF_APPROVAL_REJECTED")
        return reasons


class OperationalPermitRestrictionAcknowledgementValidator:
    @staticmethod
    def reasons(config, value) -> list[str]:
        reasons: list[str] = []
        approver = value.independent_approver
        expected_ids = {item.restriction_id for item in value.review_package.restrictions}
        if config.required_warning_restriction_id not in expected_ids:
            reasons.append("WARNING_427_RESTRICTION_OMITTED")
        actual = value.restriction_acknowledgements
        required_people = {value.mac_operator.identity_id}
        if approver is not None:
            required_people.add(approver.identity_id)
        for restriction in value.review_package.restrictions:
            matches = [item for item in actual if item.restriction_id == restriction.restriction_id]
            if {item.acknowledging_identity_id for item in matches} != required_people:
                reasons.append("MISSING_INDEPENDENT_ACKNOWLEDGEMENT")
                continue
            for item in matches:
                if (item.source_report_id != restriction.source_report_id
                        or item.source_report_digest != restriction.source_report_digest
                        or item.exact_summary_digest != restriction.canonical_summary_digest
                        or item.severity != restriction.severity
                        or item.remediation_reference != restriction.remediation_reference
                        or item.canonical_acknowledgement_digest != canonical_digest(item.content())):
                    reasons.append("RESTRICTION_ACKNOWLEDGEMENT_INVALID")
        if {item.restriction_id for item in actual} - expected_ids:
            reasons.append("UNKNOWN_RESTRICTION_ACKNOWLEDGEMENT")
        return reasons


class OperationalPermitExecutionWindowValidator:
    @staticmethod
    def reasons(value) -> list[str]:
        if value.execution_window is None:
            return ["EFFECTIVE_EXECUTION_WINDOW_MISSING"]
        if parse_timestamp(value.evaluated_at) >= parse_timestamp(
                value.execution_window.expires_at_timestamp):
            return ["EXECUTION_WINDOW_EXPIRED"]
        return []


class OperationalPermitApprovalGate:
    def evaluate(self, *, config: OperationalPermitApprovalConfig,
                 approval_input: OperationalPermitApprovalInput) -> OperationalPermitApprovalReport:
        review = approval_input.review_package
        reasons: dict[str, list[str]] = {code: [] for code in CHECK_ORDER}
        validation = OperationalPermitIssuanceValidator().validate(review)
        if validation.status.value != "PASS":
            reasons["REVIEW_PACKAGE"].append("REVIEW_PACKAGE_TAMPERED")
        if review.branch != config.approved_branch or review.commit != config.approved_commit:
            reasons["GIT_BINDING"].append("GIT_BINDING_INVALID")
        identity_reasons = OperationalPermitIdentityValidator.reasons(approval_input)
        for reason in identity_reasons:
            key = "IDENTITY_INDEPENDENCE" if any(
                marker in reason for marker in ("DISTINCT", "ALIAS", "SELF")) else "IDENTITIES"
            reasons[key].append(reason)
        if approval_input.approval_decision is not OperationalPermitApprovalDecision.APPROVED:
            reasons["APPROVAL_DECISION"].append(
                "APPROVAL_DENIED" if approval_input.approval_decision is OperationalPermitApprovalDecision.DENIED
                else "APPROVAL_NOT_APPROVED")
        reasons["RESTRICTION_ACKNOWLEDGEMENTS"].extend(
            OperationalPermitRestrictionAcknowledgementValidator.reasons(config, approval_input))
        reasons["EXECUTION_WINDOW"].extend(
            OperationalPermitExecutionWindowValidator.reasons(approval_input))
        if any(review.safety_snapshot.values()):
            reasons["SAFETY"].append("SAFETY_COUNTER_NONZERO")
        if review.production_authorized or config.production_authorized:
            reasons["PRODUCTION_SCOPE"].append("PRODUCTION_AUTHORIZATION_REJECTED")
        all_reasons = sorted({item for values in reasons.values() for item in values})
        decision = approval_input.approval_decision
        if all_reasons and decision is OperationalPermitApprovalDecision.APPROVED:
            decision = OperationalPermitApprovalDecision.BLOCKED
        status = (OperationalPermitApprovalStatus.PASS if not all_reasons
                  else OperationalPermitApprovalStatus.DENIED
                  if decision is OperationalPermitApprovalDecision.DENIED
                  else OperationalPermitApprovalStatus.BLOCKED)
        checks = tuple(OperationalPermitApprovalCheck(
            code, OperationalPermitApprovalStatus.PASS if not reasons[code] else status)
            for code in CHECK_ORDER)
        findings = tuple(OperationalPermitApprovalFinding(item) for item in all_reasons)
        identities = tuple(sorted(item.identity_id for item in (
            approval_input.requester, approval_input.mac_operator,
            approval_input.independent_approver) if item is not None))
        acknowledgements = tuple(sorted(
            item.canonical_acknowledgement_digest
            for item in approval_input.restriction_acknowledgements))
        effective = not reasons["EXECUTION_WINDOW"] and not all_reasons
        content = {
            "stage": config.stage, "decision": decision, "status": status,
            "checks": [asdict(item) for item in checks],
            "findings": [asdict(item) for item in findings],
            "identity_ids": identities, "acknowledgement_digests": acknowledgements,
            "effective_execution_window": effective,
            "operational_permit_issued": False, "bootstrap_authorized": False,
            "production_authorized": False,
        }
        digest = canonical_digest(content)
        return OperationalPermitApprovalReport(
            "m3-a4b2b1b-" + digest[7:39], digest, config.stage, decision, status,
            checks, findings, identities, acknowledgements, effective)


class OperationalPermitIssuanceCoordinator:
    def issue(self, *, config: OperationalPermitApprovalConfig,
              request: OperationalPermitIssuanceRequest, adapter: object | None = None,
              filesystem_adapter: object | None = None, database_adapter: object | None = None,
              registry_adapter: object | None = None, notification_adapter: object | None = None,
              activation_authorization: OperationalActivationAuthorizationPermit | None = None,
              ) -> OperationalPermitIssuanceResult:
        if any(item is not None for item in (
                adapter, filesystem_adapter, database_adapter, registry_adapter,
                notification_adapter)):
            raise OperationalPermitApprovalError("OPERATIONAL_ADAPTER_REJECTED")
        if (request.permit_claim_requested or request.bootstrap_execution_requested
                or request.production_authorized):
            raise OperationalPermitApprovalError("PRIVILEGED_ACTION_REJECTED")
        report = OperationalPermitApprovalGate().evaluate(
            config=config, approval_input=request.approval_input)
        if report.status is not OperationalPermitApprovalStatus.PASS:
            return OperationalPermitIssuanceResult(report, None, None)
        identities = request.approval_input
        synthetic_approval = all(item.synthetic for item in (
            identities.requester, identities.mac_operator, identities.independent_approver))
        if not synthetic_approval:
            reason = None
            if activation_authorization is None:
                reason = "ACTIVATION_AUTHORIZATION_REQUIRED"
            elif activation_authorization.request.identity.synthetic:
                reason = "SYNTHETIC_ACTIVATION_AUTHORIZATION_REJECTED"
            else:
                activation = OperationalActivationAuthorizationValidator().validate(
                    config=OperationalActivationAuthorizationConfig(
                        config.approved_branch, config.approved_commit,
                        activation_authorization.request.operational_target_path),
                    permit=activation_authorization, validated_at=request.issued_at,
                    approval_report_id=report.report_id,
                    approval_report_digest=report.report_digest,
                    operator_identity=identities.mac_operator.identity_id)
                if activation.status is not OperationalActivationAuthorizationStatus.AUTHORIZED:
                    reason = activation.reason_codes[0]
            if reason:
                return OperationalPermitIssuanceResult(
                    replace(report, status=OperationalPermitApprovalStatus.BLOCKED,
                            decision=OperationalPermitApprovalDecision.BLOCKED,
                            findings=report.findings + (
                                OperationalPermitApprovalFinding(reason),)),
                    None, None)
        auth_request = request.authorization_request
        if (auth_request.branch != config.approved_branch
                or auth_request.commit != config.approved_commit
                or auth_request.requester_identity != identities.requester.identity_id
                or auth_request.operator_identity != identities.mac_operator.identity_id
                or auth_request.approver_identity != identities.independent_approver.identity_id):
            return OperationalPermitIssuanceResult(
                replace(report, status=OperationalPermitApprovalStatus.BLOCKED,
                        decision=OperationalPermitApprovalDecision.BLOCKED,
                        findings=report.findings + (
                            OperationalPermitApprovalFinding("AUTHORIZATION_BINDING_INVALID"),)),
                None, None)
        decision, permit = OperationalBootstrapAuthorizationService().authorize(
            config=OperationalBootstrapAuthorizationConfig(
                OperationalBootstrapAuthorizationStage.CONTROLLED_NON_PRODUCTION_BOOTSTRAP_AUTHORIZATION),
            request=auth_request, approval=request.authorization_approval,
            decided_at=request.decided_at, issued_at=request.issued_at)
        return OperationalPermitIssuanceResult(
            report, decision.decision_id, permit if permit is not None else None)


def current_recommended_review(
        review_package, *, evaluated_at: str = "2026-07-30T11:00:00+09:00"
        ) -> OperationalPermitApprovalInput:
    requester = OperationalPermitIdentity(
        "mac-account:kyouhan", "LOCAL_ACCOUNT", "kyouhan", "Mac requester",
        OperationalPermitIdentityRole.REQUESTER, "mac-account:kyouhan",
        evaluated_at)
    operator = OperationalPermitIdentity(
        "mac-account:kyouhan", "LOCAL_ACCOUNT", "kyouhan", "Mac operator",
        OperationalPermitIdentityRole.MAC_OPERATOR, "mac-account:kyouhan",
        evaluated_at)
    return OperationalPermitApprovalInput(
        review_package, requester, operator, None, OperationalPermitApprovalDecision.DENIED,
        (), None, evaluated_at)
