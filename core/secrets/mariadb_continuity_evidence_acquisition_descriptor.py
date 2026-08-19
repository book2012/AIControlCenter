"""Repository-owned classifications for future historical evidence acquisition."""

from dataclasses import dataclass, field
from enum import Enum

from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    EvidenceAvailability,
    RecoverEvidenceGate,
    SemanticsChangeRequired,
)
from core.secrets.mariadb_continuity_evidence_reference_manifest import (
    VerificationState,
)
from core.secrets.mariadb_continuity_sources import (
    ContinuityEvidenceCategory,
    DataIdentityCategory,
)


class EvidenceAcquisitionCategory(str, Enum):
    """Closed identities for independently classified acquisition requirements."""

    AUTH_PLUGIN_AUTHORITATIVE_EVIDENCE = "AUTH_PLUGIN_AUTHORITATIVE_EVIDENCE"
    PYMYSQL_1_2_0_COMPATIBILITY_EVIDENCE = "PYMYSQL_1_2_0_COMPATIBILITY_EVIDENCE"
    EXPECTED_DATABASE_IDENTITY = "EXPECTED_DATABASE_IDENTITY"
    EXPECTED_ACCOUNT_IDENTITY = "EXPECTED_ACCOUNT_IDENTITY"
    REQUIRED_GRANTS = "REQUIRED_GRANTS"
    FIVE_CATEGORY_DATA_IDENTITY = "FIVE_CATEGORY_DATA_IDENTITY"
    THREE_CATEGORY_CONTINUITY_LINEAGE = "THREE_CATEGORY_CONTINUITY_LINEAGE"
    TIMESTAMP_EVIDENCE = "TIMESTAMP_EVIDENCE"
    IMMUTABLE_INTEGRITY_BINDING = "IMMUTABLE_INTEGRITY_BINDING"
    TRUSTED_ISSUER = "TRUSTED_ISSUER"
    ACCOUNT_BINDING = "ACCOUNT_BINDING"
    BASELINE_BINDING = "BASELINE_BINDING"


@dataclass(frozen=True, slots=True)
class EvidenceAcquisitionDescriptor:
    """Value-free classification; it is neither a source nor evidence."""

    category: EvidenceAcquisitionCategory
    repository_defined_identity_selection_required: bool = field(
        default=True, init=False
    )
    independently_pre_existing_source_required: bool = field(default=True, init=False)
    mac_control_plane_owned: bool = field(default=True, init=False)
    metadata_only_sufficient: bool = field(default=False, init=False)
    content_required: bool = field(default=True, init=False)
    secret_bearing_content_permitted: bool = field(default=False, init=False)
    production_access_required: bool = field(default=False, init=False)
    future_human_authorization_required: bool = field(default=True, init=False)
    future_one_shot_acquisition_required: bool = field(default=True, init=False)
    external_immutable_artifact_required: bool = field(default=True, init=False)
    repository_only_verification_sufficient: bool = field(default=False, init=False)
    acquisition_grants_authority: bool = field(default=False, init=False)
    current_availability: EvidenceAvailability = field(
        default=EvidenceAvailability.UNAVAILABLE, init=False
    )


def _canonical_descriptors() -> tuple[EvidenceAcquisitionDescriptor, ...]:
    return tuple(EvidenceAcquisitionDescriptor(category) for category in EvidenceAcquisitionCategory)


@dataclass(frozen=True, slots=True)
class MariaDBContinuityEvidenceAcquisitionContract:
    """Canonical closed acquisition descriptor set and downstream separations."""

    descriptors: tuple[EvidenceAcquisitionDescriptor, ...] = field(
        default_factory=_canonical_descriptors, init=False
    )
    data_identity_categories: tuple[DataIdentityCategory, ...] = field(
        default_factory=lambda: tuple(DataIdentityCategory), init=False
    )
    continuity_evidence_categories: tuple[ContinuityEvidenceCategory, ...] = field(
        default_factory=lambda: tuple(ContinuityEvidenceCategory), init=False
    )
    verification_state: VerificationState = field(
        default=VerificationState.UNAVAILABLE, init=False
    )
    auth_plugin_authoritative_evidence: EvidenceAvailability = field(
        default=EvidenceAvailability.UNAVAILABLE, init=False
    )
    pymysql_compatibility_evidence: EvidenceAvailability = field(
        default=EvidenceAvailability.UNAVAILABLE, init=False
    )
    five_category_data_identity_complete: bool = field(default=False, init=False)
    three_category_continuity_lineage_complete: bool = field(default=False, init=False)
    source_exists: bool = field(default=False, init=False)
    evidence_exists: bool = field(default=False, init=False)
    content_acquired: bool = field(default=False, init=False)
    evidence_admitted: bool = field(default=False, init=False)
    verification_succeeded: bool = field(default=False, init=False)
    authoritative_evidence_exists: bool = field(default=False, init=False)
    recover_evidence_sufficient: bool = field(default=False, init=False)
    recover_evidence_gate: RecoverEvidenceGate = field(
        default=RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT, init=False
    )
    production_validation_ready: bool = field(default=False, init=False)
    shopping_runtime_activated: bool = field(default=False, init=False)
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
    io_allowed: bool = field(default=False, init=False)
    network_allowed: bool = field(default=False, init=False)
    sql_allowed: bool = field(default=False, init=False)
    production_access_allowed: bool = field(default=False, init=False)
    runtime_mutation_allowed: bool = field(default=False, init=False)
    caller_positive_fact_injection_allowed: bool = field(default=False, init=False)
    caller_source_path_allowed: bool = field(default=False, init=False)
    arbitrary_reference_string_allowed: bool = field(default=False, init=False)
    external_evidence_values_accepted: bool = field(default=False, init=False)
    verification_authority: bool = field(default=False, init=False)
    admission_authority: bool = field(default=False, init=False)
    acquisition_authority: bool = field(default=False, init=False)


def canonical_mariadb_continuity_evidence_acquisition_contract(
) -> MariaDBContinuityEvidenceAcquisitionContract:
    return MariaDBContinuityEvidenceAcquisitionContract()
