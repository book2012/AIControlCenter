"""Closed symbolic fixed source slots for protected external evidence."""

from dataclasses import dataclass, field, fields
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    RecoverEvidenceGate,
    SemanticsChangeRequired,
)
from core.secrets.mariadb_continuity_evidence_source_binding import (
    CATEGORY_TO_BUNDLE_MAPPING_IS_VERIFICATION_REQUIREMENT_SCOPE,
)
from core.secrets.mariadb_continuity_evidence_source_profile import (
    OfflineAcquisitionAssessment,
    ProtectedExternalEvidenceSourceProfileIdentity,
)


class ProtectedExternalEvidenceFixedSourceSlotIdentity(str, Enum):
    """Repository-owned symbolic slots; never concrete source locations."""

    AUTH_PLUGIN_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT = (
        "AUTH_PLUGIN_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT"
    )
    PYMYSQL_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT = (
        "PYMYSQL_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT"
    )
    DATA_IDENTITY_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT = (
        "DATA_IDENTITY_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT"
    )
    CONTINUITY_LINEAGE_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT = (
        "CONTINUITY_LINEAGE_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT"
    )


PROFILE_TO_FIXED_SOURCE_SLOT_MAPPING: Mapping[
    ProtectedExternalEvidenceSourceProfileIdentity,
    ProtectedExternalEvidenceFixedSourceSlotIdentity,
] = MappingProxyType({
    ProtectedExternalEvidenceSourceProfileIdentity.AUTH_PLUGIN_PROTECTED_SOURCE_PROFILE:
        ProtectedExternalEvidenceFixedSourceSlotIdentity.AUTH_PLUGIN_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT,
    ProtectedExternalEvidenceSourceProfileIdentity.PYMYSQL_PROTECTED_SOURCE_PROFILE:
        ProtectedExternalEvidenceFixedSourceSlotIdentity.PYMYSQL_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT,
    ProtectedExternalEvidenceSourceProfileIdentity.DATA_IDENTITY_PROTECTED_SOURCE_PROFILE:
        ProtectedExternalEvidenceFixedSourceSlotIdentity.DATA_IDENTITY_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT,
    ProtectedExternalEvidenceSourceProfileIdentity.CONTINUITY_LINEAGE_PROTECTED_SOURCE_PROFILE:
        ProtectedExternalEvidenceFixedSourceSlotIdentity.CONTINUITY_LINEAGE_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT,
})


@dataclass(frozen=True, slots=True, init=False)
class ProtectedExternalEvidenceFixedSourceSlot:
    """One symbolic slot carrying only future source-protection requirements."""

    profile_identity: ProtectedExternalEvidenceSourceProfileIdentity = field(init=False)
    identity: ProtectedExternalEvidenceFixedSourceSlotIdentity = field(init=False)
    mac_control_plane_owned: bool = field(default=True, init=False)
    outside_git_required: bool = field(default=True, init=False)
    protected_parent_exact_0700_required: bool = field(default=True, init=False)
    regular_non_symlink_leaf_required: bool = field(default=True, init=False)
    leaf_permissions_no_broader_than_0600_required: bool = field(
        default=True, init=False
    )
    explicit_trusted_uid_gid_required: bool = field(default=True, init=False)
    future_fd_inode_binding_required: bool = field(default=True, init=False)
    future_human_authorization_required: bool = field(default=True, init=False)
    future_one_shot_acquisition_required: bool = field(default=True, init=False)
    maximum_acquisitions_per_future_authorization: int = field(default=1, init=False)
    fallback_allowed: bool = field(default=False, init=False)
    enumeration_allowed: bool = field(default=False, init=False)
    candidate_iteration_allowed: bool = field(default=False, init=False)
    environment_home_authority_allowed: bool = field(default=False, init=False)
    argv_transport_allowed: bool = field(default=False, init=False)
    json_value_transport_allowed: bool = field(default=False, init=False)
    evidence_secret_logging_allowed: bool = field(default=False, init=False)
    evidence_secret_hashing_allowed: bool = field(default=False, init=False)

    def __init__(self) -> None:
        raise TypeError(
            "ProtectedExternalEvidenceFixedSourceSlot is constructed only by "
            "canonical repository policy"
        )


def _canonical_fixed_source_slot(
    profile_identity: ProtectedExternalEvidenceSourceProfileIdentity,
) -> ProtectedExternalEvidenceFixedSourceSlot:
    slot = object.__new__(ProtectedExternalEvidenceFixedSourceSlot)
    object.__setattr__(slot, "profile_identity", profile_identity)
    object.__setattr__(
        slot, "identity", PROFILE_TO_FIXED_SOURCE_SLOT_MAPPING[profile_identity]
    )
    for slot_field in fields(ProtectedExternalEvidenceFixedSourceSlot):
        if slot_field.name not in {"profile_identity", "identity"}:
            object.__setattr__(slot, slot_field.name, slot_field.default)
    return slot


def _canonical_fixed_source_slots(
) -> tuple[ProtectedExternalEvidenceFixedSourceSlot, ...]:
    return tuple(
        _canonical_fixed_source_slot(profile_identity)
        for profile_identity in ProtectedExternalEvidenceSourceProfileIdentity
    )


@dataclass(frozen=True, slots=True)
class MariaDBContinuityEvidenceFixedSourceSlotContract:
    """Repository-only symbolic slots without location or factual promotion."""

    slots: tuple[ProtectedExternalEvidenceFixedSourceSlot, ...] = field(
        default_factory=_canonical_fixed_source_slots, init=False
    )
    profile_to_fixed_source_slot_mapping: Mapping[
        ProtectedExternalEvidenceSourceProfileIdentity,
        ProtectedExternalEvidenceFixedSourceSlotIdentity,
    ] = field(default=PROFILE_TO_FIXED_SOURCE_SLOT_MAPPING, init=False)
    exact_four_fixed_source_slots: bool = field(default=True, init=False)
    repository_only: bool = field(default=True, init=False)
    symbolic_fixed_source_slot: bool = field(default=True, init=False)
    value_free: bool = field(default=True, init=False)
    fail_closed: bool = field(default=True, init=False)
    zero_authority: bool = field(default=True, init=False)
    evidence_acquisition_category_distinct: bool = field(default=True, init=False)
    source_bundle_identity_distinct: bool = field(default=True, init=False)
    protected_source_profile_identity_distinct: bool = field(default=True, init=False)
    fixed_source_slot_identity_distinct: bool = field(default=True, init=False)
    concrete_source_location_established: bool = field(default=False, init=False)
    source_path_defined: bool = field(default=False, init=False)
    source_exists: bool = field(default=False, init=False)
    historical_evidence_exists: bool = field(default=False, init=False)
    source_metadata_inspected: bool = field(default=False, init=False)
    source_metadata_safe: bool = field(default=False, init=False)
    content_acquired: bool = field(default=False, init=False)
    evidence_admitted: bool = field(default=False, init=False)
    evidence_verified: bool = field(default=False, init=False)
    authority: bool = field(default=False, init=False)
    recover_evidence_sufficient: bool = field(default=False, init=False)
    offline_acquisition_assessment: OfflineAcquisitionAssessment = field(
        default=OfflineAcquisitionAssessment.UNKNOWN, init=False
    )
    production_access_currently_justified: bool = field(default=False, init=False)
    caller_slot_selection_allowed: bool = field(default=False, init=False)
    caller_path_injection_allowed: bool = field(default=False, init=False)
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
    acquisition_authority: bool = field(default=False, init=False)
    admission_authority: bool = field(default=False, init=False)
    verification_authority: bool = field(default=False, init=False)
    authorization_authority: bool = field(default=False, init=False)
    capability_authority: bool = field(default=False, init=False)
    category_to_bundle_mapping_is_verification_requirement_scope: bool = field(
        default=CATEGORY_TO_BUNDLE_MAPPING_IS_VERIFICATION_REQUIREMENT_SCOPE,
        init=False,
    )
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


def canonical_mariadb_continuity_evidence_fixed_source_slot_contract(
) -> MariaDBContinuityEvidenceFixedSourceSlotContract:
    return MariaDBContinuityEvidenceFixedSourceSlotContract()
