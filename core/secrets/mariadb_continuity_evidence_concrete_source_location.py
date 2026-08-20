"""Closed location descriptors for protected external evidence source slots."""

from dataclasses import dataclass, field, fields
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    RecoverEvidenceGate,
    SemanticsChangeRequired,
)
from core.secrets.mariadb_continuity_evidence_fixed_source_slot import (
    PROFILE_TO_FIXED_SOURCE_SLOT_MAPPING,
    ProtectedExternalEvidenceFixedSourceSlot,
    ProtectedExternalEvidenceFixedSourceSlotIdentity,
    _canonical_fixed_source_slot,
)
from core.secrets.mariadb_continuity_evidence_source_profile import (
    OfflineAcquisitionAssessment,
)


class ProtectedExternalEvidenceBaseLocationIdentity(str, Enum):
    """Repository-owned base identity; no filesystem path is established."""

    PROTECTED_EXTERNAL_EVIDENCE_BASE_LOCATION = (
        "PROTECTED_EXTERNAL_EVIDENCE_BASE_LOCATION"
    )


class ProtectedExternalEvidenceConcreteSourceLocationIdentity(str, Enum):
    """Closed leaf-location identities; never caller-selectable paths."""

    AUTH_PLUGIN_PROTECTED_EVIDENCE_LOCATION = (
        "AUTH_PLUGIN_PROTECTED_EVIDENCE_LOCATION"
    )
    PYMYSQL_PROTECTED_EVIDENCE_LOCATION = "PYMYSQL_PROTECTED_EVIDENCE_LOCATION"
    DATA_IDENTITY_PROTECTED_EVIDENCE_LOCATION = (
        "DATA_IDENTITY_PROTECTED_EVIDENCE_LOCATION"
    )
    CONTINUITY_LINEAGE_PROTECTED_EVIDENCE_LOCATION = (
        "CONTINUITY_LINEAGE_PROTECTED_EVIDENCE_LOCATION"
    )


FIXED_SOURCE_SLOT_TO_CONCRETE_LOCATION_MAPPING: Mapping[
    ProtectedExternalEvidenceFixedSourceSlotIdentity,
    ProtectedExternalEvidenceConcreteSourceLocationIdentity,
] = MappingProxyType({
    ProtectedExternalEvidenceFixedSourceSlotIdentity.AUTH_PLUGIN_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT:
        ProtectedExternalEvidenceConcreteSourceLocationIdentity.AUTH_PLUGIN_PROTECTED_EVIDENCE_LOCATION,
    ProtectedExternalEvidenceFixedSourceSlotIdentity.PYMYSQL_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT:
        ProtectedExternalEvidenceConcreteSourceLocationIdentity.PYMYSQL_PROTECTED_EVIDENCE_LOCATION,
    ProtectedExternalEvidenceFixedSourceSlotIdentity.DATA_IDENTITY_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT:
        ProtectedExternalEvidenceConcreteSourceLocationIdentity.DATA_IDENTITY_PROTECTED_EVIDENCE_LOCATION,
    ProtectedExternalEvidenceFixedSourceSlotIdentity.CONTINUITY_LINEAGE_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT:
        ProtectedExternalEvidenceConcreteSourceLocationIdentity.CONTINUITY_LINEAGE_PROTECTED_EVIDENCE_LOCATION,
})


@dataclass(frozen=True, slots=True, init=False)
class ProtectedExternalEvidenceConcreteSourceLocation:
    """One closed symbolic location, without a filesystem path or existence fact."""

    fixed_source_slot: ProtectedExternalEvidenceFixedSourceSlot = field(init=False)
    identity: ProtectedExternalEvidenceConcreteSourceLocationIdentity = field(init=False)
    base_identity: ProtectedExternalEvidenceBaseLocationIdentity = field(init=False)
    closed_repository_owned_descriptor: bool = field(default=True, init=False)
    absolute_path_value_established: bool = field(default=False, init=False)
    operational_path_establishment_pending: bool = field(default=True, init=False)
    source_exists: bool = field(default=False, init=False)

    def __init__(self) -> None:
        raise TypeError(
            "ProtectedExternalEvidenceConcreteSourceLocation is constructed only "
            "by canonical repository policy"
        )


def _canonical_concrete_source_location(
    slot_identity: ProtectedExternalEvidenceFixedSourceSlotIdentity,
) -> ProtectedExternalEvidenceConcreteSourceLocation:
    location = object.__new__(ProtectedExternalEvidenceConcreteSourceLocation)
    profile_identity = next(
        profile
        for profile, slot in PROFILE_TO_FIXED_SOURCE_SLOT_MAPPING.items()
        if slot is slot_identity
    )
    object.__setattr__(location, "fixed_source_slot", _canonical_fixed_source_slot(profile_identity))
    object.__setattr__(
        location, "identity", FIXED_SOURCE_SLOT_TO_CONCRETE_LOCATION_MAPPING[slot_identity]
    )
    object.__setattr__(
        location,
        "base_identity",
        ProtectedExternalEvidenceBaseLocationIdentity.PROTECTED_EXTERNAL_EVIDENCE_BASE_LOCATION,
    )
    for location_field in fields(ProtectedExternalEvidenceConcreteSourceLocation):
        if location_field.name not in {"fixed_source_slot", "identity", "base_identity"}:
            object.__setattr__(location, location_field.name, location_field.default)
    return location


def _canonical_concrete_source_locations(
) -> tuple[ProtectedExternalEvidenceConcreteSourceLocation, ...]:
    return tuple(
        _canonical_concrete_source_location(slot_identity)
        for slot_identity in ProtectedExternalEvidenceFixedSourceSlotIdentity
    )


@dataclass(frozen=True, slots=True)
class MariaDBContinuityEvidenceConcreteSourceLocationContract:
    locations: tuple[ProtectedExternalEvidenceConcreteSourceLocation, ...] = field(
        default_factory=_canonical_concrete_source_locations, init=False
    )
    slot_to_location_mapping: Mapping[
        ProtectedExternalEvidenceFixedSourceSlotIdentity,
        ProtectedExternalEvidenceConcreteSourceLocationIdentity,
    ] = field(default=FIXED_SOURCE_SLOT_TO_CONCRETE_LOCATION_MAPPING, init=False)
    exact_four_locations: bool = field(default=True, init=False)
    one_to_one_immutable_mapping: bool = field(default=True, init=False)
    repository_owned: bool = field(default=True, init=False)
    fail_closed: bool = field(default=True, init=False)
    zero_authority: bool = field(default=True, init=False)
    concrete_location_descriptor_established: bool = field(default=True, init=False)
    authoritative_base_path_exists: bool = field(default=False, init=False)
    concrete_path_value_established: bool = field(default=False, init=False)
    source_exists: bool = field(default=False, init=False)
    historical_evidence_exists: bool = field(default=False, init=False)
    source_metadata_inspected: bool = field(default=False, init=False)
    source_metadata_safe: bool = field(default=False, init=False)
    content_acquired: bool = field(default=False, init=False)
    evidence_admitted: bool = field(default=False, init=False)
    evidence_verified: bool = field(default=False, init=False)
    recover_evidence_sufficient: bool = field(default=False, init=False)
    authority: bool = field(default=False, init=False)
    caller_location_selection_allowed: bool = field(default=False, init=False)
    caller_path_injection_allowed: bool = field(default=False, init=False)
    environment_path_authority_allowed: bool = field(default=False, init=False)
    home_environment_authority_allowed: bool = field(default=False, init=False)
    argv_path_authority_allowed: bool = field(default=False, init=False)
    fallback_path_allowed: bool = field(default=False, init=False)
    path_enumeration_allowed: bool = field(default=False, init=False)
    candidate_iteration_allowed: bool = field(default=False, init=False)
    io_allowed: bool = field(default=False, init=False)
    network_allowed: bool = field(default=False, init=False)
    process_allowed: bool = field(default=False, init=False)
    sql_allowed: bool = field(default=False, init=False)
    production_access_allowed: bool = field(default=False, init=False)
    ubuntu_access_allowed: bool = field(default=False, init=False)
    offline_acquisition_assessment: OfflineAcquisitionAssessment = field(
        default=OfflineAcquisitionAssessment.UNKNOWN, init=False
    )
    production_access_currently_justified: bool = field(default=False, init=False)
    recover_evidence_gate: RecoverEvidenceGate = field(
        default=RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT, init=False
    )
    sm_01b_02d_06_semantics_change_required: SemanticsChangeRequired = field(
        default=SemanticsChangeRequired.NO, init=False
    )
    production_validation_ready: bool = field(default=False, init=False)
    shopping_runtime_activated: bool = field(default=False, init=False)


def canonical_mariadb_continuity_evidence_concrete_source_location_contract(
) -> MariaDBContinuityEvidenceConcreteSourceLocationContract:
    return MariaDBContinuityEvidenceConcreteSourceLocationContract()
