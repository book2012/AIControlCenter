"""Repository-only admission boundary for external evidence references."""

from dataclasses import dataclass, field

from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    EvidenceAvailability,
    EvidenceReferenceIdentityClass,
    RecoverEvidenceGate,
    SemanticsChangeRequired,
)
from core.secrets.mariadb_continuity_evidence_reference_manifest import (
    EvidenceRequirementCategory,
    VerificationState,
)
from core.secrets.mariadb_continuity_sources import (
    ContinuityEvidenceCategory,
    DataIdentityCategory,
)


@dataclass(frozen=True, slots=True)
class ExternalEvidenceAdmissionContract:
    """Closed admission requirements and independent fail-closed facts."""

    evidence_requirements: tuple[EvidenceRequirementCategory, ...] = field(
        default=tuple(EvidenceRequirementCategory), init=False
    )
    admissible_reference_identity_classes: tuple[
        EvidenceReferenceIdentityClass, ...
    ] = field(default=tuple(EvidenceReferenceIdentityClass), init=False)
    data_identity_categories: tuple[DataIdentityCategory, ...] = field(
        default=tuple(DataIdentityCategory), init=False
    )
    continuity_evidence_categories: tuple[ContinuityEvidenceCategory, ...] = field(
        default=tuple(ContinuityEvidenceCategory), init=False
    )

    repository_defined_identity_required: bool = field(default=True, init=False)
    independent_historical_source_required: bool = field(default=True, init=False)
    provenance_verification_required: bool = field(default=True, init=False)
    immutable_integrity_binding_verification_required: bool = field(
        default=True, init=False
    )
    timestamp_binding_verification_required: bool = field(default=True, init=False)
    trusted_issuer_verification_required: bool = field(default=True, init=False)
    account_binding_verification_required: bool = field(default=True, init=False)
    expected_database_binding_verification_required: bool = field(
        default=True, init=False
    )
    expected_account_binding_verification_required: bool = field(
        default=True, init=False
    )
    required_grants_binding_verification_required: bool = field(
        default=True, init=False
    )
    baseline_binding_verification_required: bool = field(default=True, init=False)
    pymysql_1_2_0_compatibility_proof_required: bool = field(
        default=True, init=False
    )

    reference_presented: bool = field(default=False, init=False)
    reference_admitted: bool = field(default=False, init=False)
    reference_verification_required: bool = field(default=True, init=False)
    reference_verification_result: VerificationState = field(
        default=VerificationState.UNAVAILABLE, init=False
    )
    reference_local_verified: bool = field(default=False, init=False)
    authoritative_evidence_exists: bool = field(default=False, init=False)
    provenance_valid: bool = field(default=False, init=False)
    integrity_binding_valid: bool = field(default=False, init=False)
    timestamp_binding_valid: bool = field(default=False, init=False)
    issuer_valid: bool = field(default=False, init=False)
    account_binding_valid: bool = field(default=False, init=False)
    expected_database_binding_valid: bool = field(default=False, init=False)
    expected_account_binding_valid: bool = field(default=False, init=False)
    required_grants_binding_valid: bool = field(default=False, init=False)
    baseline_binding_valid: bool = field(default=False, init=False)
    compatible: bool = field(default=False, init=False)
    five_category_data_identity_complete: bool = field(default=False, init=False)
    three_category_continuity_lineage_complete: bool = field(default=False, init=False)
    recover_evidence_sufficient: bool = field(default=False, init=False)
    production_validation_ready: bool = field(default=False, init=False)

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

    repository_only: bool = field(default=True, init=False)
    value_free: bool = field(default=True, init=False)
    fail_closed: bool = field(default=True, init=False)
    caller_positive_fact_injection_allowed: bool = field(default=False, init=False)
    arbitrary_reference_string_allowed: bool = field(default=False, init=False)
    actual_evidence_values_accepted: bool = field(default=False, init=False)
    credential_values_accepted: bool = field(default=False, init=False)
    io_allowed: bool = field(default=False, init=False)
    network_allowed: bool = field(default=False, init=False)
    sql_allowed: bool = field(default=False, init=False)
    production_access_allowed: bool = field(default=False, init=False)
    runtime_mutation_allowed: bool = field(default=False, init=False)
    authorization_authority: bool = field(default=False, init=False)
    capability_authority: bool = field(default=False, init=False)
    execution_authority: bool = field(default=False, init=False)
    mutation_authority: bool = field(default=False, init=False)
    retry_authority: bool = field(default=False, init=False)
    reconnect_authority: bool = field(default=False, init=False)
    rollback_authority: bool = field(default=False, init=False)
    rotate_authorized: bool = field(default=False, init=False)
    replace_authorized: bool = field(default=False, init=False)
    strategy_executed: bool = field(default=False, init=False)
    shopping_runtime_activated: bool = field(default=False, init=False)


def canonical_external_evidence_admission_contract(
) -> ExternalEvidenceAdmissionContract:
    return ExternalEvidenceAdmissionContract()
