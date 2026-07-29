"""Pure evidence validation and injected controlled rollback orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Protocol

from .models import (
    ACTIVATION_STEPS, ROLLBACK_STEPS, SAFETY_COUNTERS, PilotEvidenceBundle,
    PilotEvidenceFinding, PilotEvidenceManifest, PilotEvidenceValidationReport,
    PilotRollbackDecision, PilotRollbackPlan, PilotRollbackReceipt,
    PilotRollbackRequest, PilotRollbackStatus, PilotRollbackStep, digest,
)


class SandboxRollbackPort(Protocol):
    def rollback(self, *, plan: PilotRollbackPlan) -> Mapping[str, Any]: ...


class PilotRollbackUseRegistry(Protocol):
    def reserve(self, evidence_bundle_id: str, plan_id: str) -> bool: ...


class InMemoryPilotRollbackUseRegistry:
    """Process-local registry permitted only for isolated tests."""

    def __init__(self) -> None:
        self._uses: dict[str, str] = {}

    def reserve(self, evidence_bundle_id: str, plan_id: str) -> bool:
        if evidence_bundle_id in self._uses:
            return False
        self._uses[evidence_bundle_id] = plan_id
        return True


def _semantic(bundle: PilotEvidenceBundle) -> dict[str, Any]:
    value = bundle.to_dict()
    value.pop("bundle_id")
    value.pop("evidence_digest")
    return value


class PilotEvidenceService:
    def create(self, **values: Any) -> PilotEvidenceBundle:
        values = dict(values)
        values.setdefault("controlled_test_sandbox", True)
        values.setdefault("persistent_host_activation", False)
        values.setdefault("production_authorized", False)
        seed = dict(values)
        bundle_id = "peb-" + digest(seed).split(":", 1)[1][:32]
        temporary = PilotEvidenceBundle(bundle_id=bundle_id, evidence_digest="", **values)
        return PilotEvidenceBundle(bundle_id=bundle_id, evidence_digest=digest(_semantic(temporary)), **values)

    def validate(self, bundle: PilotEvidenceBundle, *, expected: Mapping[str, Any], validated_at: str) -> PilotEvidenceValidationReport:
        findings: list[PilotEvidenceFinding] = []
        if bundle.ordered_activation_steps != ACTIVATION_STEPS:
            findings.append(PilotEvidenceFinding("ACTIVATION_STEP_ORDER_INVALID", "ordered_activation_steps"))
        if len(bundle.ordered_executor_result_ids) != len(ACTIVATION_STEPS) or len(bundle.ordered_executor_result_digests) != len(ACTIVATION_STEPS):
            findings.append(PilotEvidenceFinding("EXECUTOR_RESULT_ORDER_INVALID", "ordered_executor_results"))
        if len(set(bundle.ordered_executor_result_ids)) != len(bundle.ordered_executor_result_ids):
            findings.append(PilotEvidenceFinding("DUPLICATE_EXECUTOR_RESULT", "ordered_executor_result_ids"))
        if len(set(bundle.manifest.artifact_digests)) != len(bundle.manifest.artifact_digests):
            findings.append(PilotEvidenceFinding("DUPLICATE_EVIDENCE_DIGEST", "artifact_digests"))
        for field in (
            "permit_id", "permit_digest", "execution_authorization_id",
            "readiness_report_id", "readiness_report_digest", "activation_id",
            "activation_receipt_digest", "package_digest", "plan_digest",
            "target_identity", "environment", "sandbox_root_identity_digest",
        ):
            if field in expected and getattr(bundle, field) != expected[field]:
                findings.append(PilotEvidenceFinding(field.upper() + "_MISMATCH", field))
        if bundle.evidence_digest != digest(_semantic(bundle)):
            findings.append(PilotEvidenceFinding("EVIDENCE_DIGEST_MISMATCH", "evidence_digest"))
        if not bundle.controlled_test_sandbox or bundle.persistent_host_activation:
            findings.append(PilotEvidenceFinding("PERSISTENT_HOST_ACTIVATION_DENIED", "controlled_test_sandbox"))
        if bundle.production_authorized:
            findings.append(PilotEvidenceFinding("PRODUCTION_AUTHORIZATION_DENIED", "production_authorized"))
        for key in SAFETY_COUNTERS:
            if bundle.safety_counters.get(key) != 0:
                findings.append(PilotEvidenceFinding("NONZERO_SAFETY_COUNTER", key))
        ordered = tuple(sorted(set(findings), key=lambda item: (item.code, item.field)))
        return PilotEvidenceValidationReport(
            PilotRollbackStatus.EVIDENCE_INVALID if ordered else PilotRollbackStatus.EVIDENCE_VALID,
            ordered, validated_at,
        )


class PilotRollbackPlanningService:
    ALLOWED_APPROVER_ROLES = frozenset({"deployment-approver", "rollback-approver"})

    def plan(self, *, request: PilotRollbackRequest, bundle: PilotEvidenceBundle, report: PilotEvidenceValidationReport) -> PilotRollbackDecision:
        reasons: list[str] = []
        try:
            requested = datetime.fromisoformat(request.requested_at.replace("Z", "+00:00")).astimezone(timezone.utc)
            expires = datetime.fromisoformat(request.expires_at.replace("Z", "+00:00")).astimezone(timezone.utc)
            if requested >= expires:
                reasons.append("ROLLBACK_REQUEST_EXPIRED")
        except Exception:
            reasons.append("MALFORMED_TIMESTAMP")
        if report.status is not PilotRollbackStatus.EVIDENCE_VALID:
            reasons.append("EVIDENCE_NOT_VALIDATED")
        if request.evidence_bundle_id != bundle.bundle_id or request.evidence_digest != bundle.evidence_digest:
            reasons.append("EVIDENCE_BINDING_MISMATCH")
        if not request.operator_identity or not request.rollback_approver_identity or request.operator_identity == request.rollback_approver_identity:
            reasons.append("SEPARATION_OF_DUTIES_DENIED")
        if request.rollback_approver_role not in self.ALLOWED_APPROVER_ROLES:
            reasons.append("APPROVER_ROLE_DENIED")
        if request.production_authorized or request.persistent_host_rollback:
            reasons.append("ROLLBACK_SCOPE_DENIED")
        if reasons:
            return PilotRollbackDecision(PilotRollbackStatus.DENIED, tuple(sorted(set(reasons))), None, None)
        semantic = {
            "evidence_bundle_id": bundle.bundle_id, "evidence_digest": bundle.evidence_digest,
            "activation_id": bundle.activation_id,
            "activation_receipt_digest": bundle.activation_receipt_digest,
            "permit_id": bundle.permit_id,
            "sandbox_root_identity_digest": bundle.sandbox_root_identity_digest,
            "before_state_manifest_digest": bundle.manifest.before_state_manifest_digest,
            "after_activation_manifest_digest": bundle.manifest.after_activation_manifest_digest,
            "artifact_paths": list(bundle.manifest.artifact_paths),
            "operator_identity": request.operator_identity,
            "rollback_approver_identity": request.rollback_approver_identity,
            "reason_category": request.reason_category, "requested_at": request.requested_at,
            "steps": [{"sequence": i, "operation": op} for i, op in enumerate(ROLLBACK_STEPS, 1)],
            "production_authorized": False, "persistent_host_rollback": False,
        }
        plan = PilotRollbackPlan(
            plan_id="prp-" + digest(semantic).split(":", 1)[1][:32],
            steps=tuple(PilotRollbackStep(i, op) for i, op in enumerate(ROLLBACK_STEPS, 1)),
            **{key: value for key, value in semantic.items() if key not in {"steps", "artifact_paths"}},
            artifact_paths=tuple(bundle.manifest.artifact_paths),
        )
        return PilotRollbackDecision(PilotRollbackStatus.BLOCKED, (), plan, None)


class PilotRollbackValidationService:
    def __init__(self, *, adapter: SandboxRollbackPort | None, registry: PilotRollbackUseRegistry | None) -> None:
        self._adapter = adapter
        self._registry = registry

    def rollback(self, *, plan: PilotRollbackPlan, bundle: PilotEvidenceBundle) -> PilotRollbackDecision:
        if self._registry is None:
            return PilotRollbackDecision(PilotRollbackStatus.BLOCKED, ("MISSING_ROLLBACK_REGISTRY",), plan, None)
        if self._adapter is None:
            return PilotRollbackDecision(PilotRollbackStatus.BLOCKED, ("MISSING_ROLLBACK_ADAPTER",), plan, None)
        if not self._registry.reserve(bundle.bundle_id, plan.plan_id):
            return PilotRollbackDecision(PilotRollbackStatus.REPLAYED, ("ROLLBACK_ALREADY_CONSUMED",), plan, None)
        try:
            result = dict(self._adapter.rollback(plan=plan))
        except Exception:
            return PilotRollbackDecision(PilotRollbackStatus.FAILED, ("ROLLBACK_ADAPTER_FAILURE",), plan, None)
        required = {"plan_id", "sandbox_root_identity_digest", "after_rollback_manifest_digest", "evidence_digests", *SAFETY_COUNTERS}
        if not required.issubset(result):
            return PilotRollbackDecision(PilotRollbackStatus.FAILED, ("MALFORMED_ROLLBACK_RESULT",), plan, None)
        reasons = []
        if result["plan_id"] != plan.plan_id or result["sandbox_root_identity_digest"] != plan.sandbox_root_identity_digest:
            reasons.append("ROLLBACK_ADAPTER_BINDING_MISMATCH")
        if result["after_rollback_manifest_digest"] != plan.before_state_manifest_digest:
            reasons.append("PRE_ACTIVATION_STATE_NOT_RESTORED")
        if any(result[key] != 0 for key in SAFETY_COUNTERS):
            reasons.append("NONZERO_SAFETY_COUNTER")
        if reasons:
            return PilotRollbackDecision(PilotRollbackStatus.FAILED, tuple(sorted(set(reasons))), plan, None)
        semantic = {
            "rollback_id": "prb-" + plan.plan_id[4:],
            "evidence_bundle_id": bundle.bundle_id, "evidence_digest": bundle.evidence_digest,
            "activation_id": bundle.activation_id,
            "activation_receipt_digest": bundle.activation_receipt_digest,
            "permit_id": bundle.permit_id, "target_identity": bundle.target_identity,
            "environment": bundle.environment,
            "sandbox_root_identity_digest": bundle.sandbox_root_identity_digest,
            "before_state_manifest_digest": plan.before_state_manifest_digest,
            "after_activation_manifest_digest": plan.after_activation_manifest_digest,
            "after_rollback_manifest_digest": result["after_rollback_manifest_digest"],
            "ordered_rollback_steps": list(ROLLBACK_STEPS),
            "rollback_evidence_digests": sorted(result["evidence_digests"]),
            "rollback_status": PilotRollbackStatus.ROLLED_BACK.value,
            "rollback_request_consumed": True, "controlled_test_sandbox": True,
            "persistent_host_rollback": False, "production_authorized": False,
            "safety_counters": {key: 0 for key in SAFETY_COUNTERS},
        }
        receipt = PilotRollbackReceipt(
            **{key: value for key, value in semantic.items() if key not in {"ordered_rollback_steps", "rollback_evidence_digests", "rollback_status"}},
            ordered_rollback_steps=ROLLBACK_STEPS,
            rollback_evidence_digests=tuple(semantic["rollback_evidence_digests"]),
            rollback_status=PilotRollbackStatus.ROLLED_BACK,
            receipt_digest=digest(semantic),
        )
        return PilotRollbackDecision(PilotRollbackStatus.ROLLED_BACK, (), plan, receipt)
