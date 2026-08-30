"""Repository-only contract for the narrow SEC-02 governance remediation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import PurePath
from typing import Protocol

from .pre_bootstrap_filesystem import (
    ExistingObjectKind,
    FilesystemObservation,
    GOVERNANCE_COMPONENTS,
    GovernedPath,
    PreBootstrapFilesystemPlan,
    REQUIRED_DIRECTORY_MODE,
    classify_governed_directory,
    FilesystemClassification,
)

OBSERVED_REMEDIABLE_MODE = 0o755


class RemediationEligibility(Enum):
    ELIGIBLE = "ELIGIBLE"
    NOT_REQUIRED = "NOT_REQUIRED"
    DENIED = "DENIED"


class RemediationOperation(Enum):
    RESTRICT_GOVERNANCE_MODE_0755_TO_0700 = "RESTRICT_GOVERNANCE_MODE_0755_TO_0700"


@dataclass(frozen=True, slots=True)
class GovernanceRemediationPlan:
    target: str
    observed_mode: int
    required_mode: int
    owner_uid: int
    owner_gid: int
    operation: RemediationOperation = RemediationOperation.RESTRICT_GOVERNANCE_MODE_0755_TO_0700


@dataclass(frozen=True, slots=True)
class RemediationDecision:
    eligibility: RemediationEligibility
    plan: GovernanceRemediationPlan | None = None


@dataclass(frozen=True, slots=True)
class RemediationPostcondition:
    observation: FilesystemObservation


class GovernanceRemediationExecutionPort(Protocol):
    """Future single-attempt port; it conveys no approval or retry authority."""

    def attempt_once(self, plan: GovernanceRemediationPlan) -> RemediationPostcondition: ...


def _fixed_governance_target(filesystem_plan: PreBootstrapFilesystemPlan) -> str | None:
    identity = filesystem_plan.identity
    if type(identity.bound_uid) is not int or identity.bound_uid <= 0 or type(identity.bound_gid) is not int or identity.bound_gid < 0:
        return None
    if type(identity.passwd_home) is not str:
        return None
    expected_target = str(PurePath(identity.passwd_home).joinpath(*GOVERNANCE_COMPONENTS))
    if filesystem_plan.governance_path != expected_target or filesystem_plan.trust_path != expected_target + "/trust":
        return None
    return expected_target


def plan_governance_remediation(
    filesystem_plan: PreBootstrapFilesystemPlan,
    observation: FilesystemObservation,
) -> RemediationDecision:
    identity = filesystem_plan.identity
    expected_target = _fixed_governance_target(filesystem_plan)
    if expected_target is None:
        return RemediationDecision(RemediationEligibility.DENIED)
    classification = classify_governed_directory(observation, identity)
    if observation.path is not GovernedPath.GOVERNANCE:
        return RemediationDecision(RemediationEligibility.DENIED)
    if classification is FilesystemClassification.SAFE_EXISTING:
        return RemediationDecision(RemediationEligibility.NOT_REQUIRED)
    exact_current_shape = (
        classification is FilesystemClassification.UNSAFE_EXISTING
        and observation.object_kind is ExistingObjectKind.DIRECTORY
        and observation.descriptor_identity_proven
        and observation.uid == identity.bound_uid
        and observation.gid == identity.bound_gid
        and type(observation.mode) is int
        and observation.mode == OBSERVED_REMEDIABLE_MODE
    )
    if not exact_current_shape:
        return RemediationDecision(RemediationEligibility.DENIED)
    return RemediationDecision(
        RemediationEligibility.ELIGIBLE,
        GovernanceRemediationPlan(
            expected_target,
            OBSERVED_REMEDIABLE_MODE,
            REQUIRED_DIRECTORY_MODE,
            identity.bound_uid,
            identity.bound_gid,
        ),
    )


def validate_governance_remediation_plan(
    filesystem_plan: PreBootstrapFilesystemPlan,
    plan: GovernanceRemediationPlan,
) -> bool:
    """Validate the complete fixed mutation shape without executing it."""

    expected_target = _fixed_governance_target(filesystem_plan)
    identity = filesystem_plan.identity
    return (
        expected_target is not None
        and type(plan) is GovernanceRemediationPlan
        and plan.target == expected_target
        and type(plan.observed_mode) is int
        and plan.observed_mode == OBSERVED_REMEDIABLE_MODE
        and type(plan.required_mode) is int
        and plan.required_mode == REQUIRED_DIRECTORY_MODE
        and type(plan.owner_uid) is int
        and plan.owner_uid == identity.bound_uid
        and type(plan.owner_gid) is int
        and plan.owner_gid == identity.bound_gid
        and plan.operation
        is RemediationOperation.RESTRICT_GOVERNANCE_MODE_0755_TO_0700
    )


def validate_remediation_postcondition(
    filesystem_plan: PreBootstrapFilesystemPlan,
    postcondition: RemediationPostcondition,
) -> bool:
    return (
        _fixed_governance_target(filesystem_plan) is not None
        and postcondition.observation.path is GovernedPath.GOVERNANCE
        and classify_governed_directory(postcondition.observation, filesystem_plan.identity)
        is FilesystemClassification.SAFE_EXISTING
    )


__all__ = (
    "GovernanceRemediationExecutionPort", "GovernanceRemediationPlan",
    "OBSERVED_REMEDIABLE_MODE", "RemediationDecision", "RemediationEligibility",
    "RemediationOperation", "RemediationPostcondition", "plan_governance_remediation",
    "validate_governance_remediation_plan", "validate_remediation_postcondition",
)
