"""Pure validators and canonical plans for M3-A4A."""

from __future__ import annotations

from .models import (
    OperationalActivationError,
    OperationalBootstrapPlan,
    OperationalBootstrapStep,
    OperationalPathPlan,
    OperationalPermissionPlan,
    OperationalRollbackPlan,
)


_RESPONSIBILITIES = (
    "audit_database", "audit_backup_root", "permit_replay_database",
    "permit_replay_backup_root", "monitoring_evidence_root",
)
_SECRET_NAMES = ("secret", "password", "token", "private_key", "credential", "cookie")
_PROTECTED = ("/System", "/Library", "/bin", "/sbin", "/usr", "/etc", "/var")


class OperationalPathPlanValidator:
    def validate(self, plan: OperationalPathPlan, *, repository_root: str,
                 user_home: str) -> tuple[str, ...]:
        reasons: list[str] = []
        values = [getattr(plan, name) for name in _RESPONSIBILITIES]
        expected_prefix = user_home.rstrip("/") + "/Library/Application Support/AIControlCenter/"
        for name, path in zip(_RESPONSIBILITIES, values, strict=True):
            if not path.startswith("/"):
                reasons.append(f"{name.upper()}_NOT_ABSOLUTE")
            if not path.startswith(expected_prefix):
                reasons.append(f"{name.upper()}_NOT_MAC_APP_STATE")
            if path == repository_root or path.startswith(repository_root.rstrip("/") + "/"):
                reasons.append(f"{name.upper()}_IN_REPOSITORY")
            if path.startswith(_PROTECTED):
                reasons.append(f"{name.upper()}_PROTECTED")
            if any(marker in path.lower() for marker in _SECRET_NAMES):
                reasons.append(f"{name.upper()}_SECRET_BEARING")
        if len(values) != len(set(values)):
            reasons.append("PATH_RESPONSIBILITIES_NOT_SEPARATED")
        if plan.symlink_paths:
            reasons.append("SYMLINK_PATH_REJECTED")
        if not plan.mac_control_plane_owned or plan.ubuntu_owned:
            reasons.append("MAC_CONTROL_PLANE_OWNERSHIP_REQUIRED")
        if plan.network_or_removable:
            reasons.append("NETWORK_OR_REMOVABLE_PATH_REJECTED")
        return tuple(sorted(set(reasons)))


class OperationalPermissionPlanValidator:
    def validate(self, plan: OperationalPermissionPlan) -> tuple[str, ...]:
        expected = {
            "application_state_parent_mode": 0o700,
            "audit_directory_mode": 0o700,
            "security_directory_mode": 0o700,
            "monitoring_directory_mode": 0o700,
            "sqlite_database_mode": 0o600,
            "backup_database_mode": 0o600,
            "manifest_file_mode": 0o600,
        }
        reasons = [f"{name.upper()}_INVALID" for name, mode in expected.items()
                   if getattr(plan, name) != mode or getattr(plan, name) & 0o022]
        if plan.owner != "AIControlCenter Mac operator" or plan.ubuntu_owned:
            reasons.append("MAC_OPERATOR_OWNERSHIP_REQUIRED")
        if plan.network_filesystem:
            reasons.append("NETWORK_FILESYSTEM_REJECTED")
        return tuple(sorted(set(reasons)))


_BOOTSTRAP_DESCRIPTIONS = (
    ("REVALIDATE_GIT", "Revalidate Git clean state and approved commit."),
    ("REVALIDATE_TESTS", "Revalidate full regression and safety counters."),
    ("REQUIRE_APPROVAL", "Require explicit non-production operator approval."),
    ("CREATE_PARENT_DIRECTORIES", "Create Mac application-state parent directories."),
    ("APPLY_DIRECTORY_PERMISSIONS", "Apply restrictive directory permissions."),
    ("CREATE_AUDIT_DATABASE", "Create audit ledger using an authorized bootstrap adapter."),
    ("APPLY_AUDIT_SCHEMA", "Apply append-only audit schema and controls."),
    ("INSPECT_AUDIT_READ_ONLY", "Inspect the audit database read-only."),
    ("CREATE_REPLAY_DATABASE", "Create permit/replay using an authorized bootstrap adapter."),
    ("APPLY_REPLAY_SCHEMA", "Apply replay schema, indexes and immutable triggers."),
    ("INSPECT_REPLAY_READ_ONLY", "Inspect the replay database read-only."),
    ("BACKUP_AUDIT", "Create the baseline audit backup."),
    ("BACKUP_REPLAY", "Create the baseline replay backup."),
    ("VALIDATE_RESTORES", "Validate both restores in temporary validation targets."),
    ("GENERATE_MONITORING_SNAPSHOT", "Generate a PRE_ACTIVATION monitoring snapshot."),
    ("VERIFY_LOGICAL_ALERT_ROUTING", "Verify alert routing without external dispatch."),
    ("KEEP_WRITERS_DISABLED", "Keep operational writers disabled."),
    ("RETURN_BOOTSTRAP_EVIDENCE", "Return evidence for a separate activation decision."),
)


def canonical_bootstrap_plan() -> OperationalBootstrapPlan:
    return OperationalBootstrapPlan(tuple(
        OperationalBootstrapStep(index, code, description)
        for index, (code, description) in enumerate(_BOOTSTRAP_DESCRIPTIONS, 1)
    ))


class OperationalBootstrapPlanValidator:
    def validate(self, plan: OperationalBootstrapPlan) -> tuple[str, ...]:
        reasons: list[str] = []
        expected = canonical_bootstrap_plan()
        if tuple((step.sequence, step.code) for step in plan.steps) != tuple(
                (step.sequence, step.code) for step in expected.steps):
            reasons.append("BOOTSTRAP_STEP_ORDER_INVALID")
        if any((plan.production_authorized, plan.external_dispatch_authorized,
                plan.ubuntu_participation, plan.api_write_route, plan.service_restart,
                plan.writer_activation, plan.activation_performed)):
            reasons.append("BOOTSTRAP_PLAN_IMPLICIT_ACTIVATION")
        return tuple(reasons)


def validate_rollback_plan(plan: OperationalRollbackPlan) -> tuple[str, ...]:
    if not isinstance(plan, OperationalRollbackPlan):
        raise OperationalActivationError("rollback plan is required")
    return () if all(plan.as_dict().values()) else ("ROLLBACK_PLAN_INCOMPLETE",)
