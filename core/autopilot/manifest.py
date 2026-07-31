"""Default-deny sprint manifest construction and validation."""

from __future__ import annotations

from dataclasses import replace
import re

from .models import (
    ApprovalRequirement,
    ApprovalState,
    AutonomyLevel,
    AutopilotPolicyError,
    SprintManifest,
    SprintManifestValidationResult,
)

_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_LEVEL = {level: index for index, level in enumerate(AutonomyLevel)}
_FORBIDDEN_SECRETS = (".env", "secret", "token", "credential")


def build_manifest(manifest: SprintManifest) -> SprintManifest:
    candidate = replace(manifest, canonical_manifest_digest="")
    digest = candidate.calculated_digest()
    candidate = replace(candidate, canonical_manifest_digest=digest)
    result = validate_manifest(candidate)
    if not result.valid:
        raise AutopilotPolicyError(result.errors[0])
    return candidate


def validate_manifest(manifest: SprintManifest) -> SprintManifestValidationResult:
    errors: list[str] = []
    if not str(manifest.task_id).strip():
        errors.append("EMPTY_TASK_ID")
    if not manifest.baseline.branch.strip():
        errors.append("MISSING_BRANCH")
    if not _COMMIT.fullmatch(manifest.baseline.commit):
        errors.append("BASELINE_NOT_EXACT_COMMIT")
    if _LEVEL[manifest.autonomy_level] > _LEVEL[manifest.maximum_autonomy_level]:
        errors.append("AUTONOMY_SELF_ESCALATION")
    if manifest.production and manifest.autonomy_level is not AutonomyLevel.L5_PRODUCTION_ACTIVATION:
        errors.append("PRODUCTION_PROHIBITED_BELOW_L5")
    if manifest.autonomy_level is AutonomyLevel.L4_CONTROLLED_OPERATIONAL_WRITE:
        if manifest.approval.requirement not in (
            ApprovalRequirement.INDEPENDENT_HUMAN,
            ApprovalRequirement.OPERATIONAL_WRITE,
        ) or not manifest.approval.independent_approver_required:
            errors.append("L4_REQUIRES_HUMAN_APPROVAL")
    if manifest.autonomy_level is AutonomyLevel.L5_PRODUCTION_ACTIVATION:
        if manifest.approval.requirement is not ApprovalRequirement.PRODUCTION:
            errors.append("L5_REQUIRES_PRODUCTION_APPROVAL")
    if manifest.approval.environment_authorization_allowed:
        errors.append("ENVIRONMENT_ONLY_AUTHORIZATION")
    if manifest.ubuntu_participation not in ("NONE", "STATELESS_INFRASTRUCTURE_WORKER"):
        errors.append("UBUNTU_CONTROL_PLANE_OWNERSHIP")
    for authority in (
        manifest.control_plane_owner,
        manifest.governance_authority,
        manifest.approval_authority,
        manifest.retry_authority,
    ):
        if authority != "AIControlCenter":
            errors.append("CONTROL_PLANE_AUTHORITY_INVALID")
            break
    if not manifest.git_gates.require_exact_baseline or not manifest.git_gates.require_remote_commit_verification:
        errors.append("MISSING_GIT_GATE")
    if not manifest.test_gates.required_commands:
        errors.append("MISSING_TEST_GATE")
    if not manifest.documentation_gates.required_documents:
        errors.append("MISSING_DOCUMENTATION_GATE")
    if not manifest.retry.pre_claim_recovery_requires_evidence:
        errors.append("PRE_CLAIM_EVIDENCE_REQUIRED")
    if manifest.retry.automatic_post_claim_retry_allowed:
        errors.append("AUTOMATIC_POST_CLAIM_RETRY")
    if not manifest.forbidden_operations:
        errors.append("EMPTY_FORBIDDEN_OPERATIONS")
    if any(path in ("*", "**", "/*") for path in manifest.scope.allowed_paths) and not manifest.scope.wildcard_paths_explicitly_approved:
        errors.append("WILDCARD_ALLOWED_PATH")
    secret_values = (*manifest.secret_dependencies, *manifest.scope.allowed_paths)
    if any(marker in value.lower() for marker in _FORBIDDEN_SECRETS for value in secret_values):
        errors.append("SECRET_DEPENDENCY")
    if manifest.canonical_manifest_digest and manifest.canonical_manifest_digest != manifest.calculated_digest():
        errors.append("MANIFEST_DIGEST_MISMATCH")
    return SprintManifestValidationResult(
        valid=not errors,
        errors=tuple(sorted(set(errors))),
        canonical_json=manifest.canonical_json(),
        digest=manifest.calculated_digest(),
    )
