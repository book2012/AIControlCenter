"""Pure deterministic live permit and runtime evidence validation."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from .models import *


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise OperationalBootstrapExecutionError("EXPLICIT_TIMESTAMP_REQUIRED") from exc
    if parsed.tzinfo is None:
        raise OperationalBootstrapExecutionError("TIMEZONE_REQUIRED")
    return parsed


class OperationalBootstrapLivePermitValidator:
    REQUIRED_FALSE = (
        "writers_authorized", "monitoring_authorized",
        "external_dispatch_authorized", "production_authorized",
    )
    REQUIRED_BINDINGS = (
        "readiness_report_digest", "preflight_report_digest", "schema_binding_digest",
        "target_binding_digest", "plan_binding_digest",
    )

    def validate(self, *, live: OperationalBootstrapLivePermitEvidence,
                 issuance: OperationalBootstrapIssuanceEvidence,
                 request: OperationalBootstrapRuntimeRequest) -> tuple[OperationalBootstrapRuntimeFinding, ...]:
        permit, evidence = live.permit, issuance.evidence
        reasons: list[str] = []
        if live.canonical_payload != canonical_json(permit):
            reasons.append("PERMIT_JSON_NOT_CANONICAL")
        content = dict(permit)
        supplied = content.pop("permit_digest", live.permit_digest)
        if canonical_digest(content) != supplied or supplied != live.permit_digest:
            reasons.append("PERMIT_DIGEST_MISMATCH")
        if issuance.canonical_payload != canonical_json(evidence):
            reasons.append("ISSUANCE_JSON_NOT_CANONICAL")
        if permit.get("permit_id") != evidence.get("permit_id") or supplied != evidence.get("permit_digest"):
            reasons.append("ISSUANCE_PERMIT_BINDING_MISMATCH")
        if permit.get("branch") != request.branch or permit.get("commit") != request.commit:
            reasons.append("GIT_BINDING_MISMATCH")
        now = _time(request.claim_at)
        if now < _time(str(permit.get("not_before", permit.get("issued_at", "")))):
            reasons.append("PERMIT_NOT_YET_VALID")
        if now >= _time(str(permit.get("expires_at", ""))):
            reasons.append("PERMIT_EXPIRED")
        if now >= _time(str(permit.get("bootstrap_execution_deadline", ""))):
            reasons.append("BOOTSTRAP_DEADLINE_EXPIRED")
        if permit.get("maximum_uses") != 1 or permit.get("claimed", False):
            reasons.append("PERMIT_USE_STATE_INVALID")
        if permit.get("environment") not in ("CONTROLLED_NON_PRODUCTION", "controlled non-production"):
            reasons.append("PERMIT_ENVIRONMENT_INVALID")
        if permit.get("operator_identity") == permit.get("approver_identity"):
            reasons.append("INDEPENDENT_APPROVER_REQUIRED")
        acknowledgements = permit.get("warning_acknowledgements", ())
        if not isinstance(acknowledgements, list) or len(acknowledgements) != 2:
            reasons.append("DUAL_WARNING_ACKNOWLEDGEMENTS_REQUIRED")
        if any(not permit.get(name) for name in self.REQUIRED_BINDINGS):
            reasons.append("PERMIT_BINDING_INCOMPLETE")
        if not permit.get("bootstrap_authorized", False) or any(
                permit.get(name) is not False for name in self.REQUIRED_FALSE):
            reasons.append("PERMIT_SCOPE_INVALID")
        return tuple(OperationalBootstrapRuntimeFinding(code) for code in sorted(set(reasons)))


class OperationalBootstrapRuntimeValidator:
    def validate(self, *, config: OperationalBootstrapExecutionConfig,
                 request: OperationalBootstrapRuntimeRequest,
                 host: OperationalBootstrapHostRevalidationEvidence,
                 target: OperationalBootstrapTargetRevalidationEvidence
                 ) -> tuple[OperationalBootstrapRuntimeFinding, ...]:
        reasons: list[str] = []
        if request.mode is not config.mode:
            reasons.append("MODE_BINDING_INVALID")
        if request.branch != config.approved_branch or not host.git_clean:
            reasons.append("GIT_STATE_INVALID")
        if host.upstream_ahead or host.upstream_behind:
            reasons.append("GIT_UPSTREAM_PARITY_INVALID")
        if host.system != "Darwin" or host.uid == 0:
            reasons.append("MAC_NON_ROOT_HOST_REQUIRED")
        if not target.targets_absent:
            reasons.append("OPERATIONAL_TARGET_EXISTS")
        if not target.symlink_free or not target.local_fixed_volume:
            reasons.append("OPERATIONAL_TARGET_POLICY_INVALID")
        if host.available_bytes < config.minimum_free_bytes:
            reasons.append("CAPACITY_INSUFFICIENT")
        return tuple(OperationalBootstrapRuntimeFinding(code) for code in sorted(set(reasons)))


class OperationalBootstrapRuntimeEvidenceValidator:
    def validate(self, bundle: OperationalBootstrapRuntimeEvidenceBundle
                 ) -> OperationalBootstrapRuntimeValidationReport:
        findings: list[OperationalBootstrapRuntimeFinding] = []
        receipt = bundle.receipt
        if canonical_digest(receipt.as_dict()) != bundle.receipt_digest:
            findings.append(OperationalBootstrapRuntimeFinding("RECEIPT_DIGEST_INVALID"))
        if any((receipt.writers_activated, receipt.monitoring_activated,
                receipt.external_dispatch_activated, receipt.production_authorized)):
            findings.append(OperationalBootstrapRuntimeFinding("ACTIVATION_CONTRADICTION"))
        status = OperationalBootstrapRuntimeStatus.COMPLETE if not findings else OperationalBootstrapRuntimeStatus.FAILED
        digest = canonical_digest({"status": status, "findings": [asdict(x) for x in findings]})
        return OperationalBootstrapRuntimeValidationReport(
            "m3-a4b2b2a-validation-" + digest[7:39], status, tuple(findings), digest)
