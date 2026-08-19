"""Immutable, value-free requirements for external continuity evidence references."""

from dataclasses import dataclass, field
from enum import Enum

from core.secrets.mariadb_continuity_sources import (
    ContinuityEvidenceCategory,
    DataIdentityCategory,
)


class EvidenceRequirementCategory(str, Enum):
    AUTH_PLUGIN_HISTORICAL_EVIDENCE = "AUTH_PLUGIN_HISTORICAL_EVIDENCE"
    PYMYSQL_1_2_0_COMPATIBILITY_EVIDENCE = "PYMYSQL_1_2_0_COMPATIBILITY_EVIDENCE"
    EXPECTED_DATABASE_IDENTITY = "EXPECTED_DATABASE_IDENTITY"
    EXPECTED_ACCOUNT_IDENTITY = "EXPECTED_ACCOUNT_IDENTITY"
    REQUIRED_GRANTS_PROFILE = "REQUIRED_GRANTS_PROFILE"


class VerificationState(str, Enum):
    UNAVAILABLE = "UNAVAILABLE"
    REFERENCED_UNVERIFIED = "REFERENCED_UNVERIFIED"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    VERIFIED_EXTERNAL_REFERENCE = "VERIFIED_EXTERNAL_REFERENCE"


@dataclass(frozen=True, slots=True)
class VerifiedExternalReferenceSemantics:
    """Meaning of verification at the reference-local boundary only."""

    verification_state: VerificationState = field(
        default=VerificationState.VERIFIED_EXTERNAL_REFERENCE, init=False
    )
    evidence_exists_authoritatively: bool = field(default=False, init=False)
    provenance_valid: bool = field(default=False, init=False)
    authority: bool = field(default=False, init=False)
    canonical_available: bool = field(default=False, init=False)
    compatible: bool = field(default=False, init=False)
    reference_readiness_established: bool = field(default=False, init=False)
    recover_evidence_sufficient: bool = field(default=False, init=False)


@dataclass(frozen=True, slots=True)
class EvidenceReferenceManifest:
    """Closed requirements without evidence values, locations, or authority."""

    evidence_requirements: tuple[EvidenceRequirementCategory, ...] = field(
        default=tuple(EvidenceRequirementCategory), init=False
    )
    data_identity_requirements: tuple[DataIdentityCategory, ...] = field(
        default=tuple(DataIdentityCategory), init=False
    )
    continuity_requirements: tuple[ContinuityEvidenceCategory, ...] = field(
        default=tuple(ContinuityEvidenceCategory), init=False
    )
    evidence_reference_state: VerificationState = field(
        default=VerificationState.VERIFICATION_REQUIRED, init=False
    )
    evidence_exists: bool = field(default=False, init=False)
    provenance_valid: bool = field(default=False, init=False)
    authority: bool = field(default=False, init=False)
    compatible: bool = field(default=False, init=False)
    reference_readiness_established: bool = field(default=False, init=False)
    recover_evidence_sufficient: bool = field(default=False, init=False)
    manifest_value_free: bool = field(default=True, init=False)
    reference_can_be_caller_supplied: bool = field(default=False, init=False)
    reference_asserts_existence: bool = field(default=False, init=False)
    reference_asserts_authority: bool = field(default=False, init=False)
    reference_asserts_compatibility: bool = field(default=False, init=False)
    reference_asserts_readiness: bool = field(default=False, init=False)
    reference_can_contain_secret_value: bool = field(default=False, init=False)
    reference_can_contain_credential_hash: bool = field(default=False, init=False)
    reference_can_contain_arbitrary_free_text: bool = field(default=False, init=False)
    reference_can_contain_sql: bool = field(default=False, init=False)
    reference_can_trigger_io: bool = field(default=False, init=False)
    reference_can_trigger_network: bool = field(default=False, init=False)
    reference_can_trigger_production_access: bool = field(default=False, init=False)


def canonical_evidence_reference_manifest() -> EvidenceReferenceManifest:
    return EvidenceReferenceManifest()


def verified_external_reference_semantics() -> VerifiedExternalReferenceSemantics:
    return VerifiedExternalReferenceSemantics()
