"""Pure validators for operational bootstrap host evidence."""

from __future__ import annotations

from pathlib import PurePosixPath

from .models import (
    OperationalBootstrapCapacityEvidence,
    OperationalBootstrapHostPreflightConfig,
    OperationalBootstrapTargetEvidence,
)


class OperationalBootstrapTargetEvidenceValidator:
    def validate(self, name: str, evidence: OperationalBootstrapTargetEvidence,
                 config: OperationalBootstrapHostPreflightConfig) -> tuple[str, ...]:
        reasons: list[str] = []
        expected = config.expected_targets.get(name)
        path = PurePosixPath(evidence.normalized_identity)
        if expected != evidence.normalized_identity or not path.is_absolute() or ".." in path.parts:
            reasons.append("TARGET_IDENTITY_INVALID")
        if evidence.responsibility != name:
            reasons.append("TARGET_RESPONSIBILITY_INVALID")
        if evidence.exists and not evidence.authorized_prior_bootstrap_receipt:
            reasons.append("UNAUTHORIZED_EXISTING_TARGET")
        if evidence.symlink:
            reasons.append("TARGET_SYMLINK_REJECTED")
        if evidence.parent_component_symlink:
            reasons.append("PARENT_SYMLINK_REJECTED")
        if evidence.repository_overlap:
            reasons.append("REPOSITORY_OVERLAP_REJECTED")
        if evidence.ubuntu_linux_owned:
            reasons.append("UBUNTU_OWNERSHIP_REJECTED")
        if evidence.protected_path:
            reasons.append("PROTECTED_PATH_REJECTED")
        if evidence.network or evidence.removable or not evidence.local_filesystem:
            reasons.append("NONLOCAL_FILESYSTEM_REJECTED")
        expected_mode = 0o700 if name.endswith("root") else 0o600
        if evidence.permission_mode != expected_mode:
            reasons.append("PERMISSION_PLAN_REJECTED")
        if evidence.expected_owner_identity != "AIControlCenter Mac operator":
            reasons.append("OWNER_PLAN_REJECTED")
        return tuple(sorted(set(reasons)))


class OperationalBootstrapFilesystemEvidenceValidator:
    def validate(self, evidence: OperationalBootstrapTargetEvidence) -> tuple[str, ...]:
        return (() if evidence.local_filesystem and not evidence.network
                and not evidence.removable and evidence.filesystem_identity else
                ("FILESYSTEM_POLICY_REJECTED",))


class OperationalBootstrapCapacityValidator:
    def validate(self, evidence: OperationalBootstrapCapacityEvidence,
                 config: OperationalBootstrapHostPreflightConfig) -> tuple[str, ...]:
        required = (
            config.estimated_audit_database_allocation
            + config.estimated_replay_database_allocation
            + config.estimated_baseline_backup_allocation
            + config.estimated_restore_validation_allocation
            + config.safety_reserve
        )
        if (not evidence.filesystem_identity or evidence.total_bytes <= 0
                or evidence.available_bytes < config.minimum_available_bytes
                or evidence.available_bytes < required
                or evidence.available_percentage < config.minimum_available_percentage):
            return ("INSUFFICIENT_LOCAL_CAPACITY",)
        return ()
