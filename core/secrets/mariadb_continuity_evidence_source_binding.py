"""Closed symbolic source-bundle binding for future evidence acquisition."""

from dataclasses import dataclass, field, fields
from types import MappingProxyType
from typing import Mapping

from core.secrets.mariadb_continuity_evidence_acquisition_descriptor import (
    EvidenceAcquisitionCategory,
)
from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    EvidenceAvailability,
    EvidenceReferenceIdentityClass,
    RecoverEvidenceGate,
    SemanticsChangeRequired,
)


CATEGORY_TO_BUNDLE_MAPPING: Mapping[
    EvidenceAcquisitionCategory, EvidenceReferenceIdentityClass
] = MappingProxyType({
    EvidenceAcquisitionCategory.AUTH_PLUGIN_AUTHORITATIVE_EVIDENCE:
        EvidenceReferenceIdentityClass.AUTH_PLUGIN_HISTORICAL_ATTESTATION,
    EvidenceAcquisitionCategory.ACCOUNT_BINDING:
        EvidenceReferenceIdentityClass.AUTH_PLUGIN_HISTORICAL_ATTESTATION,
    EvidenceAcquisitionCategory.PYMYSQL_1_2_0_COMPATIBILITY_EVIDENCE:
        EvidenceReferenceIdentityClass.PYMYSQL_COMPATIBILITY_ATTESTATION,
    EvidenceAcquisitionCategory.EXPECTED_DATABASE_IDENTITY:
        EvidenceReferenceIdentityClass.DATA_IDENTITY_ATTESTATION,
    EvidenceAcquisitionCategory.EXPECTED_ACCOUNT_IDENTITY:
        EvidenceReferenceIdentityClass.DATA_IDENTITY_ATTESTATION,
    EvidenceAcquisitionCategory.REQUIRED_GRANTS:
        EvidenceReferenceIdentityClass.DATA_IDENTITY_ATTESTATION,
    EvidenceAcquisitionCategory.FIVE_CATEGORY_DATA_IDENTITY:
        EvidenceReferenceIdentityClass.DATA_IDENTITY_ATTESTATION,
    EvidenceAcquisitionCategory.BASELINE_BINDING:
        EvidenceReferenceIdentityClass.DATA_IDENTITY_ATTESTATION,
    EvidenceAcquisitionCategory.THREE_CATEGORY_CONTINUITY_LINEAGE:
        EvidenceReferenceIdentityClass.CONTINUITY_LINEAGE_ATTESTATION,
    EvidenceAcquisitionCategory.TIMESTAMP_EVIDENCE:
        EvidenceReferenceIdentityClass.CONTINUITY_LINEAGE_ATTESTATION,
    EvidenceAcquisitionCategory.IMMUTABLE_INTEGRITY_BINDING:
        EvidenceReferenceIdentityClass.CONTINUITY_LINEAGE_ATTESTATION,
    EvidenceAcquisitionCategory.TRUSTED_ISSUER:
        EvidenceReferenceIdentityClass.CONTINUITY_LINEAGE_ATTESTATION,
})
CATEGORY_TO_BUNDLE_MAPPING_IS_VERIFICATION_REQUIREMENT_SCOPE = False


@dataclass(frozen=True, slots=True, init=False)
class ProtectedSourceBundlePolicy:
    """Value-free requirements for one future protected source slot."""

    identity: EvidenceReferenceIdentityClass = field(init=False)
    categories: tuple[EvidenceAcquisitionCategory, ...] = field(init=False)
    mac_control_plane_owned: bool = field(default=True, init=False)
    fixed_protected_source_slot_required: bool = field(default=True, init=False)
    outside_git_required: bool = field(default=True, init=False)
    protected_parent_exact_0700_required: bool = field(default=True, init=False)
    regular_non_symlink_leaf_required: bool = field(default=True, init=False)
    leaf_permissions_no_broader_than_0600_required: bool = field(
        default=True, init=False
    )
    explicit_trusted_uid_gid_required: bool = field(default=True, init=False)
    future_fd_inode_binding_required: bool = field(default=True, init=False)
    fallback_allowed: bool = field(default=False, init=False)
    enumeration_allowed: bool = field(default=False, init=False)
    candidate_iteration_allowed: bool = field(default=False, init=False)
    environment_home_authority_allowed: bool = field(default=False, init=False)
    argv_transport_allowed: bool = field(default=False, init=False)
    json_value_transport_allowed: bool = field(default=False, init=False)
    evidence_secret_logging_allowed: bool = field(default=False, init=False)
    evidence_secret_hashing_allowed: bool = field(default=False, init=False)
    future_human_authorization_required: bool = field(default=True, init=False)
    future_one_shot_acquisition_required: bool = field(default=True, init=False)
    maximum_acquisitions_per_future_authorization: int = field(default=1, init=False)

    def __init__(self) -> None:
        raise TypeError(
            "ProtectedSourceBundlePolicy is constructed only by canonical "
            "repository policy"
        )


def _canonical_bundle(
    identity: EvidenceReferenceIdentityClass,
) -> ProtectedSourceBundlePolicy:
    categories = tuple(
        category
        for category in EvidenceAcquisitionCategory
        if CATEGORY_TO_BUNDLE_MAPPING[category] is identity
    )
    bundle = object.__new__(ProtectedSourceBundlePolicy)
    object.__setattr__(bundle, "identity", identity)
    object.__setattr__(bundle, "categories", categories)
    for policy_field in fields(ProtectedSourceBundlePolicy):
        if policy_field.name not in {"identity", "categories"}:
            object.__setattr__(bundle, policy_field.name, policy_field.default)
    return bundle


def _canonical_bundles() -> tuple[ProtectedSourceBundlePolicy, ...]:
    return tuple(
        _canonical_bundle(identity)
        for identity in EvidenceReferenceIdentityClass
    )


@dataclass(frozen=True, slots=True)
class MariaDBContinuityEvidenceSourceBindingContract:
    """Repository-defined binding; never a locator, acquisition, or admission."""

    bundles: tuple[ProtectedSourceBundlePolicy, ...] = field(
        default_factory=_canonical_bundles, init=False
    )
    category_to_bundle_mapping: Mapping[
        EvidenceAcquisitionCategory, EvidenceReferenceIdentityClass
    ] = field(default=CATEGORY_TO_BUNDLE_MAPPING, init=False)
    descriptor_classification_distinct: bool = field(default=True, init=False)
    symbolic_source_bundle_identity_distinct: bool = field(default=True, init=False)
    concrete_source_location_established: bool = field(default=False, init=False)
    source_exists: bool = field(default=False, init=False)
    source_metadata_safe: bool = field(default=False, init=False)
    content_acquired: bool = field(default=False, init=False)
    evidence_exists: bool = field(default=False, init=False)
    evidence_admitted: bool = field(default=False, init=False)
    evidence_verified: bool = field(default=False, init=False)
    authoritative_evidence_exists: bool = field(default=False, init=False)
    provenance_valid: bool = field(default=False, init=False)
    integrity_valid: bool = field(default=False, init=False)
    timestamp_valid: bool = field(default=False, init=False)
    issuer_valid: bool = field(default=False, init=False)
    account_baseline_valid: bool = field(default=False, init=False)
    identity_complete: bool = field(default=False, init=False)
    lineage_complete: bool = field(default=False, init=False)
    recover_evidence_sufficient: bool = field(default=False, init=False)
    production_validation_ready: bool = field(default=False, init=False)
    shopping_runtime_activated: bool = field(default=False, init=False)
    auth_plugin_authoritative_evidence: EvidenceAvailability = field(
        default=EvidenceAvailability.UNAVAILABLE, init=False
    )
    pymysql_compatibility_evidence: EvidenceAvailability = field(
        default=EvidenceAvailability.UNAVAILABLE, init=False
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
    repository_only: bool = field(default=True, init=False)
    value_free: bool = field(default=True, init=False)
    fail_closed: bool = field(default=True, init=False)
    zero_authority: bool = field(default=True, init=False)
    caller_selection_allowed: bool = field(default=False, init=False)
    io_allowed: bool = field(default=False, init=False)
    network_allowed: bool = field(default=False, init=False)
    sql_allowed: bool = field(default=False, init=False)
    process_allowed: bool = field(default=False, init=False)
    production_access_allowed: bool = field(default=False, init=False)
    runtime_mutation_allowed: bool = field(default=False, init=False)
    ubuntu_access_allowed: bool = field(default=False, init=False)
    acquisition_authority: bool = field(default=False, init=False)
    admission_authority: bool = field(default=False, init=False)
    verification_authority: bool = field(default=False, init=False)
    authorization_authority: bool = field(default=False, init=False)
    capability_authority: bool = field(default=False, init=False)


def canonical_mariadb_continuity_evidence_source_binding_contract(
) -> MariaDBContinuityEvidenceSourceBindingContract:
    return MariaDBContinuityEvidenceSourceBindingContract()
