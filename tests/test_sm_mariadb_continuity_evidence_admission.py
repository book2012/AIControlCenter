from dataclasses import fields

import pytest

from core.secrets.mariadb_continuity_evidence_admission import (
    ExternalEvidenceAdmissionContract,
    canonical_external_evidence_admission_contract,
)
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


def test_existing_closed_types_are_reused_exactly():
    contract = canonical_external_evidence_admission_contract()
    assert contract.evidence_requirements == tuple(EvidenceRequirementCategory)
    assert contract.admissible_reference_identity_classes == tuple(
        EvidenceReferenceIdentityClass
    )
    assert contract.data_identity_categories == tuple(DataIdentityCategory)
    assert contract.continuity_evidence_categories == tuple(
        ContinuityEvidenceCategory
    )
    assert type(contract.reference_verification_result) is VerificationState


def test_caller_cannot_inject_any_fact_or_reference_value():
    contract = ExternalEvidenceAdmissionContract()
    for item in fields(contract):
        assert item.init is False
        with pytest.raises(TypeError):
            ExternalEvidenceAdmissionContract(**{item.name: True})
        with pytest.raises((AttributeError, TypeError)):
            setattr(contract, item.name, True)


def test_admission_verification_and_downstream_facts_are_independent():
    contract = canonical_external_evidence_admission_contract()
    assert contract.reference_presented is False
    assert contract.reference_admitted is False
    assert contract.reference_verification_required is True
    assert contract.reference_verification_result is VerificationState.UNAVAILABLE
    assert contract.reference_local_verified is False
    assert all(
        fact is False
        for fact in (
            contract.authoritative_evidence_exists,
            contract.provenance_valid,
            contract.integrity_binding_valid,
            contract.timestamp_binding_valid,
            contract.issuer_valid,
            contract.account_binding_valid,
            contract.expected_database_binding_valid,
            contract.expected_account_binding_valid,
            contract.required_grants_binding_valid,
            contract.baseline_binding_valid,
            contract.compatible,
            contract.five_category_data_identity_complete,
            contract.three_category_continuity_lineage_complete,
            contract.recover_evidence_sufficient,
            contract.production_validation_ready,
        )
    )


def test_all_historical_evidence_requirements_are_closed_and_independent():
    contract = canonical_external_evidence_admission_contract()
    assert contract.evidence_requirements == tuple(EvidenceRequirementCategory)
    assert contract.admissible_reference_identity_classes == tuple(
        EvidenceReferenceIdentityClass
    )
    assert all(
        requirement is True
        for requirement in (
            contract.repository_defined_identity_required,
            contract.independent_historical_source_required,
            contract.provenance_verification_required,
            contract.immutable_integrity_binding_verification_required,
            contract.timestamp_binding_verification_required,
            contract.trusted_issuer_verification_required,
            contract.account_binding_verification_required,
            contract.expected_database_binding_verification_required,
            contract.expected_account_binding_verification_required,
            contract.required_grants_binding_verification_required,
            contract.baseline_binding_verification_required,
            contract.pymysql_1_2_0_compatibility_proof_required,
        )
    )
    assert contract.data_identity_categories == tuple(DataIdentityCategory)
    assert contract.continuity_evidence_categories == tuple(
        ContinuityEvidenceCategory
    )


def test_canonical_contract_preserves_frozen_fail_closed_outcomes():
    contract = canonical_external_evidence_admission_contract()
    assert contract.auth_plugin_authoritative_evidence is EvidenceAvailability.UNAVAILABLE
    assert contract.pymysql_compatibility_evidence is EvidenceAvailability.UNAVAILABLE
    assert contract.recover_evidence_gate is RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT
    assert contract.sm_01b_02d_06_semantics_change_required is SemanticsChangeRequired.NO
    assert contract.rotate_authorized is False
    assert contract.replace_authorized is False
    assert contract.strategy_executed is False
    assert contract.shopping_runtime_activated is False


def test_contract_is_repository_only_value_free_and_contains_no_value_fields():
    contract = canonical_external_evidence_admission_contract()
    assert contract.repository_only is True
    assert contract.value_free is True
    assert contract.fail_closed is True
    assert contract.caller_positive_fact_injection_allowed is False
    assert contract.arbitrary_reference_string_allowed is False
    assert contract.actual_evidence_values_accepted is False
    assert contract.credential_values_accepted is False
    prohibited = {
        "path", "url", "reference", "identifier", "hash", "digest", "credential",
        "secret", "sql", "host", "port", "dsn", "username", "database_name",
        "runtime_identifier",
    }
    names = {item.name for item in fields(contract)}
    assert names.isdisjoint(prohibited)
    assert not any(type(getattr(contract, name)) is str for name in names)
