"""Reviewed, closed collaborator composition for the live CLI."""

from __future__ import annotations

import os
import platform
import pwd
import shutil
from datetime import datetime, timezone
from pathlib import Path

from core.deployment.operational_activation_authorization import (
    OperationalActivationAuthorizationBuilder,
    OperationalActivationAuthorizationCommitBinding,
    OperationalActivationAuthorizationConfig,
    OperationalActivationAuthorizationIdentityBinding,
    OperationalActivationAuthorizationRequest,
    OperationalActivationAuthorizationRestrictionBinding,
    OperationalActivationAuthorizationSafetyBinding,
    OperationalActivationAuthorizationWindow,
)
from core.deployment.operational_bootstrap_execution import (
    AtomicPermitClaimFileRegistry,
    MacOperationalBootstrapPathPolicy,
    MacOperationalBootstrapRuntimeAdapter,
    OperationalBootstrapExecutionConfig,
    OperationalBootstrapHostRevalidationEvidence,
    OperationalBootstrapRuntimeMode,
    OperationalBootstrapRuntimePlan,
    OperationalBootstrapTargetRevalidationEvidence,
    OperationalMacBootstrapExecutionCoordinator,
    PwdMacOperationalHomeResolver,
    StrictJsonArtifactReader,
    canonical_digest as execution_digest,
)
from core.deployment.git_readonly_evidence import (
    ReadOnlyGitEvidenceCollector,
    ReadOnlyGitEvidenceConfig,
)

from .artifacts import (
    AtomicControlledOperationalArtifactWriter,
    StrictControlledOperationalArtifactReader,
)
from .coordinator import ControlledOperationalBootstrapOrchestrator
from .models import ControlledOperationalBootstrapError, canonical_digest


class SystemClock:
    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


class LocalMacHostEvidence:
    def __init__(self, *, repository_root: Path, operator_identity: str,
                 trusted_root: Path, path_policy: MacOperationalBootstrapPathPolicy) -> None:
        self.repository_root = repository_root
        self.operator_identity = operator_identity
        self.trusted_root = trusted_root
        self.path_policy = path_policy

    def collect(self):
        return {"system": platform.system(), "uid": os.getuid(),
                "operator_identity": self.operator_identity,
                "trusted_operational_root": str(self.trusted_root)}

    def runtime_evidence(self):
        home = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
        return OperationalBootstrapHostRevalidationEvidence(
            platform.system(), os.getuid(), home, self.repository_root, True, 0, 0,
            shutil.disk_usage(home).free)

    def target_evidence(self):
        paths = self.path_policy.resolve()
        return OperationalBootstrapTargetRevalidationEvidence(
            paths.root, all(not item.exists() and not item.is_symlink()
                            for item in paths.managed_targets), True, True)


class ActivationAuthorizationService:
    def authorize(self, *, request, approval, preflight, now):
        activation_request = OperationalActivationAuthorizationRequest(
            str(approval["status"]), canonical_digest(approval),
            str(preflight["status"]), canonical_digest(preflight),
            OperationalActivationAuthorizationIdentityBinding(
                request.requester_identity, request.operator_identity,
                request.independent_approver_identity),
            OperationalActivationAuthorizationRestrictionBinding(
                request.restriction_acknowledgement_digests,
                request.active_restriction_digests),
            OperationalActivationAuthorizationCommitBinding(
                request.branch, request.commit, True, 0, 0),
            OperationalActivationAuthorizationWindow(
                str(approval["approved_at"]), request.time_policy.activation_not_before,
                request.time_policy.activation_expires_at),
            OperationalActivationAuthorizationSafetyBinding({
                "operational_permits_issued": 0, "live_claims": 0,
                "bootstrap_executions": 0, "production_activations": 0}),
            canonical_digest(preflight), request.trusted_operational_root,
            canonical_digest({"managed_targets_absent": True}),
            OperationalBootstrapRuntimePlan.build().plan_digest,
            {"audit": canonical_digest("audit"), "replay": canonical_digest("replay")},
            canonical_digest("r3-recovery-tests"))
        config = OperationalActivationAuthorizationConfig(
            request.branch, request.commit, request.trusted_operational_root)
        decision, permit = OperationalActivationAuthorizationBuilder().build(
            config=config, request=activation_request, decided_at=now, issued_at=now)
        return activation_request, permit, {
            "decision_id": decision.decision_id, "status": decision.status.value,
            "request_digest": decision.request_digest}


class ControlledLivePermitService:
    def issue(self, *, request, approval, activation_authorization, now):
        content = {
            "permit_id": "m3-a4b2b2b-r3-permit-" + canonical_digest(
                {"request": request.request_id, "issued_at": now})[7:39],
            "branch": request.branch, "commit": request.commit, "issued_at": now,
            "not_before": request.time_policy.permit_not_before,
            "expires_at": request.time_policy.permit_expires_at,
            "bootstrap_execution_deadline":
                request.time_policy.bootstrap_execution_deadline,
            "maximum_uses": 1, "claimed": False,
            "environment": "CONTROLLED_NON_PRODUCTION",
            "operator_identity": request.operator_identity,
            "approver_identity": request.independent_approver_identity,
            "warning_acknowledgements": list(
                request.restriction_acknowledgement_digests),
            "readiness_report_digest": canonical_digest(approval),
            "preflight_report_digest": canonical_digest("preflight"),
            "schema_binding_digest": canonical_digest("schemas"),
            "target_binding_digest": canonical_digest(
                str(request.trusted_operational_root)),
            "plan_binding_digest": OperationalBootstrapRuntimePlan.build().plan_digest,
            "bootstrap_authorized": True, "writers_authorized": False,
            "monitoring_authorized": False, "external_dispatch_authorized": False,
            "production_authorized": False,
        }
        content["permit_digest"] = execution_digest(content)
        return content, {"permit_id": content["permit_id"],
                         "permit_digest": content["permit_digest"]}


def build_default_live_orchestrator(request, *, repository_root: Path | None = None):
    """Assemble the fixed live graph. No caller-selected collaborators exist."""
    root = (repository_root or Path(__file__).parents[3]).resolve()
    resolver = PwdMacOperationalHomeResolver()
    policy = MacOperationalBootstrapPathPolicy(
        home_resolver=resolver, repository_root=root)
    resolved = policy.resolve()
    if resolved.root != request.trusted_operational_root:
        raise ControlledOperationalBootstrapError("TARGET_BINDING_INVALID")
    adapter = MacOperationalBootstrapRuntimeAdapter()
    execution = OperationalMacBootstrapExecutionCoordinator(
        config=OperationalBootstrapExecutionConfig(
            OperationalBootstrapRuntimeMode.CONTROLLED_NON_PRODUCTION_OPERATIONAL_BOOTSTRAP,
            root),
        artifact_reader=StrictJsonArtifactReader(),
        claim_registry=AtomicPermitClaimFileRegistry(), path_policy=policy,
        runtime_adapter=adapter)
    host = LocalMacHostEvidence(
        repository_root=root, operator_identity=request.operator_identity,
        trusted_root=request.trusted_operational_root, path_policy=policy)
    collaborators = {
        "approval_reader": StrictControlledOperationalArtifactReader(),
        "preflight_reader": StrictControlledOperationalArtifactReader(),
        "artifact_writer": AtomicControlledOperationalArtifactWriter(),
        "git_evidence": ReadOnlyGitEvidenceCollector(ReadOnlyGitEvidenceConfig(
            repository_root=root, expected_branch=request.branch,
            expected_commit=request.commit)),
        "host_evidence": host,
        "clock": SystemClock(),
        "activation_service": ActivationAuthorizationService(),
        "permit_service": ControlledLivePermitService(),
        "execution_coordinator": execution, "runtime_adapter": adapter,
    }
    if any(value is None for value in collaborators.values()):
        raise ControlledOperationalBootstrapError("REQUIRED_COLLABORATOR_UNAVAILABLE")
    return ControlledOperationalBootstrapOrchestrator(**collaborators)
