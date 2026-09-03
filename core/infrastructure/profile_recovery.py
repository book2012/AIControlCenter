"""Pure, fail-closed infrastructure-profile recovery decision policy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


SHOPPING_PROFILE = "aicontrolcenter-commerce"
SHOPPING_STATE_VOLUMES = (
    "ai-shopping-database",
    "ai-shopping-wordpress",
)


class ProfileHealth(str, Enum):
    HEALTHY = "HEALTHY"
    BROKEN = "BROKEN"
    UNKNOWN = "UNKNOWN"


class EvidenceState(str, Enum):
    PROVEN = "PROVEN"
    NOT_PROVEN = "NOT_PROVEN"
    UNKNOWN = "UNKNOWN"


class RecoveryOutcome(str, Enum):
    READY_FOR_LIFECYCLE_START = "READY_FOR_LIFECYCLE_START"
    RECOVERY_EVIDENCE_REQUIRED = "RECOVERY_EVIDENCE_REQUIRED"
    STORAGE_PRESERVATION_REQUIRED = "STORAGE_PRESERVATION_REQUIRED"
    MUTATION_UNDETERMINED = "MUTATION_UNDETERMINED"


class MutationCandidate(str, Enum):
    START_EXISTING_PROFILE_ONCE = "START_EXISTING_PROFILE_ONCE"


class DecisionReason(str, Enum):
    LIFECYCLE_ONLY_START_PROVEN = "LIFECYCLE_ONLY_START_PROVEN"
    LIFECYCLE_ONLY_START_UNPROVEN = "LIFECYCLE_ONLY_START_UNPROVEN"
    BROKEN_PROFILE_REQUIRES_RECOVERY_EVIDENCE = (
        "BROKEN_PROFILE_REQUIRES_RECOVERY_EVIDENCE"
    )
    STORAGE_PRESERVATION_UNPROVEN = "STORAGE_PRESERVATION_UNPROVEN"
    PROFILE_HEALTH_UNKNOWN = "PROFILE_HEALTH_UNKNOWN"
    PROFILE_EXISTENCE_UNRESOLVED = "PROFILE_EXISTENCE_UNRESOLVED"
    RUNTIME_STATE_UNRESOLVED = "RUNTIME_STATE_UNRESOLVED"
    PROFILE_ALREADY_RUNNING = "PROFILE_ALREADY_RUNNING"


@dataclass(frozen=True, slots=True)
class ProfileHealthFacts:
    """Value-free profile facts; raw status is diagnostic evidence only."""

    profile: str
    exists: bool | None
    raw_inventory_status: str | None
    runtime_running: bool | None
    health: ProfileHealth


@dataclass(frozen=True, slots=True)
class RecoveryEvidence:
    lifecycle_only_start: EvidenceState = EvidenceState.UNKNOWN
    storage_preservation: EvidenceState = EvidenceState.UNKNOWN
    verified_backup_restore: EvidenceState = EvidenceState.UNKNOWN

    def storage_is_protected(self) -> bool:
        return (
            self.storage_preservation is EvidenceState.PROVEN
            or self.verified_backup_restore is EvidenceState.PROVEN
        )


@dataclass(frozen=True, slots=True)
class ProfileRecoveryDecision:
    outcome: RecoveryOutcome
    reasons: tuple[DecisionReason, ...]
    candidate: MutationCandidate | None
    storage_protection_evidence_satisfied: bool
    destructive_recovery_available: bool

    def to_json_safe(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "authoritative_work_item": "SHOP-SERVICE-START-01B",
            "outcome": self.outcome.value,
            "reasons": [reason.value for reason in self.reasons],
            "candidate": self.candidate.value if self.candidate else None,
            "storage_protection_evidence_satisfied": (
                self.storage_protection_evidence_satisfied
            ),
            "destructive_recovery_available": self.destructive_recovery_available,
            "persistent_state_volumes": list(SHOPPING_STATE_VOLUMES),
            "mutation_selected": False,
            "automatic_retry": False,
            "production_authority": False,
            "ubuntu_authority": False,
        }


def decide_profile_recovery(
    facts: ProfileHealthFacts,
    evidence: RecoveryEvidence,
) -> ProfileRecoveryDecision:
    """Classify a candidate without authorizing or performing any mutation."""
    storage_protected = evidence.storage_is_protected()

    if facts.profile != SHOPPING_PROFILE or facts.exists is None:
        return ProfileRecoveryDecision(
            RecoveryOutcome.MUTATION_UNDETERMINED,
            (DecisionReason.PROFILE_EXISTENCE_UNRESOLVED,),
            None,
            storage_protected,
            False,
        )
    if facts.health is ProfileHealth.UNKNOWN:
        return ProfileRecoveryDecision(
            RecoveryOutcome.MUTATION_UNDETERMINED,
            (DecisionReason.PROFILE_HEALTH_UNKNOWN,),
            None,
            storage_protected,
            False,
        )
    if facts.health is ProfileHealth.BROKEN:
        reasons = [DecisionReason.BROKEN_PROFILE_REQUIRES_RECOVERY_EVIDENCE]
        outcome = RecoveryOutcome.RECOVERY_EVIDENCE_REQUIRED
        if not storage_protected:
            reasons.append(DecisionReason.STORAGE_PRESERVATION_UNPROVEN)
            outcome = RecoveryOutcome.STORAGE_PRESERVATION_REQUIRED
        return ProfileRecoveryDecision(
            outcome, tuple(reasons), None, storage_protected, False
        )
    if facts.exists is not True or facts.runtime_running is None:
        return ProfileRecoveryDecision(
            RecoveryOutcome.MUTATION_UNDETERMINED,
            (DecisionReason.RUNTIME_STATE_UNRESOLVED,),
            None,
            storage_protected,
            False,
        )
    if facts.runtime_running is True:
        return ProfileRecoveryDecision(
            RecoveryOutcome.MUTATION_UNDETERMINED,
            (DecisionReason.PROFILE_ALREADY_RUNNING,),
            None,
            storage_protected,
            False,
        )
    if evidence.lifecycle_only_start is not EvidenceState.PROVEN:
        return ProfileRecoveryDecision(
            RecoveryOutcome.RECOVERY_EVIDENCE_REQUIRED,
            (DecisionReason.LIFECYCLE_ONLY_START_UNPROVEN,),
            None,
            storage_protected,
            False,
        )
    return ProfileRecoveryDecision(
        RecoveryOutcome.READY_FOR_LIFECYCLE_START,
        (DecisionReason.LIFECYCLE_ONLY_START_PROVEN,),
        MutationCandidate.START_EXISTING_PROFILE_ONCE,
        storage_protected,
        False,
    )


__all__ = (
    "DecisionReason",
    "EvidenceState",
    "MutationCandidate",
    "ProfileHealth",
    "ProfileHealthFacts",
    "ProfileRecoveryDecision",
    "RecoveryEvidence",
    "RecoveryOutcome",
    "SHOPPING_PROFILE",
    "SHOPPING_STATE_VOLUMES",
    "decide_profile_recovery",
)
