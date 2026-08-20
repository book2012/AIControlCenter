"""Value-free facts for one protected-source metadata inspection."""

from dataclasses import dataclass, field
from enum import Enum

from core.secrets.mariadb_continuity_evidence_concrete_source_location import (
    ProtectedExternalEvidenceConcreteSourceLocationIdentity,
)


class MetadataInspectionOutcome(str, Enum):
    SAFE_BOUND = "SAFE_BOUND"
    ABSENT = "ABSENT"
    UNSAFE = "UNSAFE"
    UNAVAILABLE = "UNAVAILABLE"
    UNCERTAIN = "UNCERTAIN"


class MetadataInspectionReason(str, Enum):
    METADATA_SAFE_AND_STABLY_BOUND = "METADATA_SAFE_AND_STABLY_BOUND"
    SOURCE_ABSENT = "SOURCE_ABSENT"
    PARENT_ABSENT = "PARENT_ABSENT"
    SYMLINK_REJECTED = "SYMLINK_REJECTED"
    WRONG_FILE_TYPE = "WRONG_FILE_TYPE"
    PARENT_MODE_MISMATCH = "PARENT_MODE_MISMATCH"
    LEAF_PERMISSIONS_TOO_BROAD = "LEAF_PERMISSIONS_TOO_BROAD"
    PARENT_UID_GID_MISMATCH = "PARENT_UID_GID_MISMATCH"
    LEAF_UID_GID_MISMATCH = "LEAF_UID_GID_MISMATCH"
    INODE_DEVICE_INSTABILITY = "INODE_DEVICE_INSTABILITY"
    PATH_REPLACEMENT_RACE = "PATH_REPLACEMENT_RACE"
    METADATA_ACCESS_FAILURE = "METADATA_ACCESS_FAILURE"
    AMBIGUOUS_METADATA_RESULT = "AMBIGUOUS_METADATA_RESULT"


class MetadataEvidenceProvenance(str, Enum):
    """Closed provenance categories; only inert classification is issuable here."""

    INERT_TEST_CLASSIFICATION = "INERT_TEST_CLASSIFICATION"
    HUMAN_AUTHORIZED_OPERATIONAL_INSPECTION = "HUMAN_AUTHORIZED_OPERATIONAL_INSPECTION"


OPERATIONAL_METADATA_EVIDENCE_ISSUER_IMPLEMENTED = False


_REASON_OUTCOME = {
    MetadataInspectionReason.METADATA_SAFE_AND_STABLY_BOUND: MetadataInspectionOutcome.SAFE_BOUND,
    MetadataInspectionReason.SOURCE_ABSENT: MetadataInspectionOutcome.ABSENT,
    MetadataInspectionReason.PARENT_ABSENT: MetadataInspectionOutcome.ABSENT,
    MetadataInspectionReason.SYMLINK_REJECTED: MetadataInspectionOutcome.UNSAFE,
    MetadataInspectionReason.WRONG_FILE_TYPE: MetadataInspectionOutcome.UNSAFE,
    MetadataInspectionReason.PARENT_MODE_MISMATCH: MetadataInspectionOutcome.UNSAFE,
    MetadataInspectionReason.LEAF_PERMISSIONS_TOO_BROAD: MetadataInspectionOutcome.UNSAFE,
    MetadataInspectionReason.PARENT_UID_GID_MISMATCH: MetadataInspectionOutcome.UNSAFE,
    MetadataInspectionReason.LEAF_UID_GID_MISMATCH: MetadataInspectionOutcome.UNSAFE,
    MetadataInspectionReason.INODE_DEVICE_INSTABILITY: MetadataInspectionOutcome.UNCERTAIN,
    MetadataInspectionReason.PATH_REPLACEMENT_RACE: MetadataInspectionOutcome.UNCERTAIN,
    MetadataInspectionReason.METADATA_ACCESS_FAILURE: MetadataInspectionOutcome.UNAVAILABLE,
    MetadataInspectionReason.AMBIGUOUS_METADATA_RESULT: MetadataInspectionOutcome.UNCERTAIN,
}


@dataclass(frozen=True, slots=True, init=False)
class ProtectedSourceMetadataInspectionRequest:
    """Repository-created request for one symbolic identity, never a path."""

    source_identity: ProtectedExternalEvidenceConcreteSourceLocationIdentity
    profile: str = field(default="MARIADB_CONTINUITY_PROTECTED_SOURCE_METADATA_V1", init=False)
    mutation_budget: int = field(default=0, init=False)

    def __init__(self, source_identity: object) -> None:
        del source_identity
        raise TypeError("metadata requests are constructed only by canonical repository policy")

    @classmethod
    def canonical(
        cls, source_identity: ProtectedExternalEvidenceConcreteSourceLocationIdentity
    ) -> "ProtectedSourceMetadataInspectionRequest":
        if type(source_identity) is not ProtectedExternalEvidenceConcreteSourceLocationIdentity:
            raise TypeError("exact symbolic source identity required")
        request = object.__new__(cls)
        object.__setattr__(request, "source_identity", source_identity)
        object.__setattr__(request, "profile", "MARIADB_CONTINUITY_PROTECTED_SOURCE_METADATA_V1")
        object.__setattr__(request, "mutation_budget", 0)
        return request


@dataclass(frozen=True, slots=True, init=False)
class ProtectedSourceMetadataEvidence:
    outcome: MetadataInspectionOutcome
    reason: MetadataInspectionReason
    source_exists: bool
    metadata_inspected: bool
    metadata_safe: bool
    provenance: MetadataEvidenceProvenance
    operationally_observed: bool
    human_authorized_operational_inspection: bool
    content_acquired: bool = field(default=False, init=False)
    evidence_admitted: bool = field(default=False, init=False)
    evidence_verified: bool = field(default=False, init=False)
    recover_evidence_sufficient: bool = field(default=False, init=False)
    production_validation_ready: bool = field(default=False, init=False)
    shopping_runtime_activated: bool = field(default=False, init=False)
    mutation_authority: bool = field(default=False, init=False)
    acquisition_authority: bool = field(default=False, init=False)
    admission_authority: bool = field(default=False, init=False)
    verification_authority: bool = field(default=False, init=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        raise TypeError("metadata evidence is constructed only by repository-owned classification")

    @property
    def is_operational_evidence(self) -> bool:
        return (
            self.provenance is MetadataEvidenceProvenance.HUMAN_AUTHORIZED_OPERATIONAL_INSPECTION
            and self.operationally_observed
            and self.human_authorized_operational_inspection
        )


def metadata_evidence_for_reason(
    reason: MetadataInspectionReason,
) -> ProtectedSourceMetadataEvidence:
    """Canonical and sole reason-to-outcome classification."""
    if type(reason) is not MetadataInspectionReason:
        raise TypeError("reason must be MetadataInspectionReason")
    outcome = _REASON_OUTCOME[reason]
    safe = outcome is MetadataInspectionOutcome.SAFE_BOUND
    evidence = object.__new__(ProtectedSourceMetadataEvidence)
    object.__setattr__(evidence, "outcome", outcome)
    object.__setattr__(evidence, "reason", reason)
    object.__setattr__(evidence, "source_exists", safe)
    object.__setattr__(evidence, "metadata_inspected", safe)
    object.__setattr__(evidence, "metadata_safe", safe)
    object.__setattr__(evidence, "provenance", MetadataEvidenceProvenance.INERT_TEST_CLASSIFICATION)
    object.__setattr__(evidence, "operationally_observed", False)
    object.__setattr__(evidence, "human_authorized_operational_inspection", False)
    for field_name in (
        "content_acquired", "evidence_admitted", "evidence_verified",
        "recover_evidence_sufficient", "production_validation_ready",
        "shopping_runtime_activated", "mutation_authority", "acquisition_authority",
        "admission_authority", "verification_authority",
    ):
        object.__setattr__(evidence, field_name, False)
    return evidence
