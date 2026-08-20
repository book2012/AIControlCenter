"""Closed symbolic protected-source profiles for external evidence."""

from dataclasses import dataclass, field, fields
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    EvidenceReferenceIdentityClass,
    RecoverEvidenceGate,
    SemanticsChangeRequired,
)
from core.secrets.mariadb_continuity_evidence_source_binding import (
    CATEGORY_TO_BUNDLE_MAPPING_IS_VERIFICATION_REQUIREMENT_SCOPE,
    ProtectedSourceBundlePolicy,
    _canonical_bundle,
)


class ProtectedExternalEvidenceSourceProfileIdentity(str, Enum):
    """Repository-owned symbolic profiles; never locations or bundle identities."""

    AUTH_PLUGIN_PROTECTED_SOURCE_PROFILE = "AUTH_PLUGIN_PROTECTED_SOURCE_PROFILE"
    PYMYSQL_PROTECTED_SOURCE_PROFILE = "PYMYSQL_PROTECTED_SOURCE_PROFILE"
    DATA_IDENTITY_PROTECTED_SOURCE_PROFILE = (
        "DATA_IDENTITY_PROTECTED_SOURCE_PROFILE"
    )
    CONTINUITY_LINEAGE_PROTECTED_SOURCE_PROFILE = (
        "CONTINUITY_LINEAGE_PROTECTED_SOURCE_PROFILE"
    )


class OfflineAcquisitionAssessment(str, Enum):
    """The sole assessment supported by current repository facts."""

    UNKNOWN = "UNKNOWN"


BUNDLE_TO_PROTECTED_SOURCE_PROFILE_MAPPING: Mapping[
    EvidenceReferenceIdentityClass, ProtectedExternalEvidenceSourceProfileIdentity
] = MappingProxyType({
    EvidenceReferenceIdentityClass.AUTH_PLUGIN_HISTORICAL_ATTESTATION:
        ProtectedExternalEvidenceSourceProfileIdentity.AUTH_PLUGIN_PROTECTED_SOURCE_PROFILE,
    EvidenceReferenceIdentityClass.PYMYSQL_COMPATIBILITY_ATTESTATION:
        ProtectedExternalEvidenceSourceProfileIdentity.PYMYSQL_PROTECTED_SOURCE_PROFILE,
    EvidenceReferenceIdentityClass.DATA_IDENTITY_ATTESTATION:
        ProtectedExternalEvidenceSourceProfileIdentity.DATA_IDENTITY_PROTECTED_SOURCE_PROFILE,
    EvidenceReferenceIdentityClass.CONTINUITY_LINEAGE_ATTESTATION:
        ProtectedExternalEvidenceSourceProfileIdentity.CONTINUITY_LINEAGE_PROTECTED_SOURCE_PROFILE,
})


@dataclass(frozen=True, slots=True, init=False)
class ProtectedExternalEvidenceSourceProfile:
    """One symbolic profile bound to the existing protected bundle policy."""

    identity: ProtectedExternalEvidenceSourceProfileIdentity = field(init=False)
    bundle_policy: ProtectedSourceBundlePolicy = field(init=False)
    profile_is_symbolic: bool = field(default=True, init=False)
    mac_control_plane_owned: bool = field(default=True, init=False)
    concrete_source_location_established: bool = field(default=False, init=False)
    source_path_defined: bool = field(default=False, init=False)
    source_exists: bool = field(default=False, init=False)
    source_metadata_inspected: bool = field(default=False, init=False)
    source_metadata_safe: bool = field(default=False, init=False)
    content_acquired: bool = field(default=False, init=False)
    evidence_admitted: bool = field(default=False, init=False)
    evidence_verified: bool = field(default=False, init=False)
    authority: bool = field(default=False, init=False)

    def __init__(self) -> None:
        raise TypeError(
            "ProtectedExternalEvidenceSourceProfile is constructed only by "
            "canonical repository policy"
        )


def _canonical_profile(
    bundle_identity: EvidenceReferenceIdentityClass,
) -> ProtectedExternalEvidenceSourceProfile:
    profile = object.__new__(ProtectedExternalEvidenceSourceProfile)
    object.__setattr__(
        profile,
        "identity",
        BUNDLE_TO_PROTECTED_SOURCE_PROFILE_MAPPING[bundle_identity],
    )
    object.__setattr__(profile, "bundle_policy", _canonical_bundle(bundle_identity))
    for profile_field in fields(ProtectedExternalEvidenceSourceProfile):
        if profile_field.name not in {"identity", "bundle_policy"}:
            object.__setattr__(profile, profile_field.name, profile_field.default)
    return profile


def _canonical_profiles() -> tuple[ProtectedExternalEvidenceSourceProfile, ...]:
    return tuple(_canonical_profile(identity) for identity in EvidenceReferenceIdentityClass)


@dataclass(frozen=True, slots=True)
class MariaDBContinuityEvidenceSourceProfileContract:
    """Repository-only profile identities without source or authority promotion."""

    profiles: tuple[ProtectedExternalEvidenceSourceProfile, ...] = field(
        default_factory=_canonical_profiles, init=False
    )
    bundle_to_profile_mapping: Mapping[
        EvidenceReferenceIdentityClass,
        ProtectedExternalEvidenceSourceProfileIdentity,
    ] = field(default=BUNDLE_TO_PROTECTED_SOURCE_PROFILE_MAPPING, init=False)
    exact_four_profiles: bool = field(default=True, init=False)
    repository_only: bool = field(default=True, init=False)
    value_free: bool = field(default=True, init=False)
    fail_closed: bool = field(default=True, init=False)
    zero_authority: bool = field(default=True, init=False)
    descriptor_classification_distinct: bool = field(default=True, init=False)
    source_bundle_identity_distinct: bool = field(default=True, init=False)
    protected_source_profile_identity_distinct: bool = field(default=True, init=False)
    concrete_source_location_established: bool = field(default=False, init=False)
    source_exists: bool = field(default=False, init=False)
    historical_evidence_exists: bool = field(default=False, init=False)
    source_metadata_safe: bool = field(default=False, init=False)
    content_acquired: bool = field(default=False, init=False)
    evidence_admitted: bool = field(default=False, init=False)
    evidence_verified: bool = field(default=False, init=False)
    authority: bool = field(default=False, init=False)
    offline_acquisition_assessment: OfflineAcquisitionAssessment = field(
        default=OfflineAcquisitionAssessment.UNKNOWN, init=False
    )
    production_access_currently_justified: bool = field(default=False, init=False)
    category_to_bundle_mapping_is_verification_requirement_scope: bool = field(
        default=CATEGORY_TO_BUNDLE_MAPPING_IS_VERIFICATION_REQUIREMENT_SCOPE,
        init=False,
    )
    io_allowed: bool = field(default=False, init=False)
    metadata_inspection_allowed: bool = field(default=False, init=False)
    source_resolution_allowed: bool = field(default=False, init=False)
    content_acquisition_allowed: bool = field(default=False, init=False)
    admission_allowed: bool = field(default=False, init=False)
    verification_allowed: bool = field(default=False, init=False)
    network_allowed: bool = field(default=False, init=False)
    process_allowed: bool = field(default=False, init=False)
    sql_allowed: bool = field(default=False, init=False)
    production_access_allowed: bool = field(default=False, init=False)
    runtime_mutation_allowed: bool = field(default=False, init=False)
    ubuntu_access_allowed: bool = field(default=False, init=False)
    recover_evidence_gate: RecoverEvidenceGate = field(
        default=RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT, init=False
    )
    sm_01b_02d_06_semantics_change_required: SemanticsChangeRequired = field(
        default=SemanticsChangeRequired.NO, init=False
    )
    rotate_authorized: bool = field(default=False, init=False)
    replace_authorized: bool = field(default=False, init=False)
    strategy_executed: bool = field(default=False, init=False)
    production_validation_ready: bool = field(default=False, init=False)
    shopping_runtime_activated: bool = field(default=False, init=False)


def canonical_mariadb_continuity_evidence_source_profile_contract(
) -> MariaDBContinuityEvidenceSourceProfileContract:
    return MariaDBContinuityEvidenceSourceProfileContract()
