from dataclasses import fields

import pytest

from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    EvidenceAvailability,
    EvidenceReferenceIdentityClass,
    ExternalEvidenceAttestationReferenceContract,
    RecoverEvidenceGate,
    SemanticsChangeRequired,
    canonical_external_evidence_attestation_reference_contract,
)
from core.secrets.mariadb_continuity_evidence_reference_manifest import (
    EvidenceRequirementCategory,
    VerificationState,
    verified_external_reference_semantics,
)
from core.secrets.mariadb_continuity_sources import (
    ContinuityEvidenceCategory,
    DataIdentityCategory,
)


def test_exact_existing_enum_types_are_reused_without_duplication():
    contract = canonical_external_evidence_attestation_reference_contract()
    assert contract.evidence_requirements == tuple(EvidenceRequirementCategory)
    assert all(type(item) is EvidenceRequirementCategory for item in contract.evidence_requirements)
    assert type(contract.reference_verification_state) is VerificationState
    assert contract.data_identity_categories == tuple(DataIdentityCategory)
    assert all(type(item) is DataIdentityCategory for item in contract.data_identity_categories)
    assert contract.continuity_evidence_categories == tuple(ContinuityEvidenceCategory)
    assert all(type(item) is ContinuityEvidenceCategory for item in contract.continuity_evidence_categories)


def test_all_fields_are_immutable_and_caller_positive_fact_injection_is_closed():
    contract = ExternalEvidenceAttestationReferenceContract()
    for item in fields(contract):
        assert item.init is False
        with pytest.raises(TypeError):
            ExternalEvidenceAttestationReferenceContract(**{item.name: True})
        with pytest.raises((AttributeError, TypeError)):
            setattr(contract, item.name, True)


def test_canonical_reference_requires_verification_and_remains_fail_closed():
    contract = canonical_external_evidence_attestation_reference_contract()
    assert contract.reference_verification_state is VerificationState.VERIFICATION_REQUIRED
    independent_negative_facts = (
        contract.evidence_exists,
        contract.provenance_valid,
        contract.integrity_binding_satisfied,
        contract.account_baseline_binding_satisfied,
        contract.authority,
        contract.compatible,
        contract.reference_local_ready,
        contract.five_category_data_identity_complete,
        contract.three_category_continuity_lineage_complete,
        contract.recover_evidence_sufficient,
        contract.production_validation_ready,
    )
    assert all(value is False for value in independent_negative_facts)
    assert contract.auth_plugin_authoritative_evidence is EvidenceAvailability.UNAVAILABLE
    assert contract.pymysql_compatibility_evidence is EvidenceAvailability.UNAVAILABLE
    assert contract.recover_evidence_gate is RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT
    assert contract.rotate_authorized is False
    assert contract.replace_authorized is False
    assert contract.strategy_executed is False
    assert contract.shopping_runtime_activated is False


def test_verified_external_reference_remains_reference_local_with_zero_promotion():
    semantics = verified_external_reference_semantics()
    assert semantics.verification_state is VerificationState.VERIFIED_EXTERNAL_REFERENCE
    assert semantics.evidence_exists_authoritatively is False
    assert semantics.provenance_valid is False
    assert semantics.canonical_available is False
    assert semantics.compatible is False
    assert semantics.reference_readiness_established is False
    assert semantics.recover_evidence_sufficient is False
    assert semantics.authority is False


def test_requirements_do_not_claim_satisfaction_and_contract_is_value_free():
    contract = canonical_external_evidence_attestation_reference_contract()
    requirements = (
        contract.independent_historical_source_required,
        contract.provenance_required,
        contract.immutable_integrity_binding_required,
        contract.timestamp_binding_required,
        contract.trusted_issuer_binding_required,
        contract.account_binding_required,
        contract.baseline_binding_required,
    )
    assert all(requirement is True for requirement in requirements)
    assert contract.actual_evidence_values_accepted is False
    assert contract.caller_positive_fact_injection_allowed is False
    assert contract.arbitrary_reference_string_allowed is False
    assert contract.value_free is True
    assert contract.sm_01b_02d_06_semantics_change_required is SemanticsChangeRequired.NO


def test_reference_identity_is_closed_and_no_value_bearing_fields_exist():
    contract = canonical_external_evidence_attestation_reference_contract()
    assert contract.reference_identity_classes == tuple(EvidenceReferenceIdentityClass)
    assert all(type(item) is EvidenceReferenceIdentityClass for item in contract.reference_identity_classes)
    prohibited_names = {
        "path", "url", "reference_identifier", "hash", "digest", "plugin_name",
        "database_name", "account_name", "runtime_identifier", "credential",
        "credential_hash", "secret", "secret_value", "sql", "runtime_dump", "port",
    }
    names = {item.name for item in fields(contract)}
    assert names.isdisjoint(prohibited_names)
    assert not any(type(getattr(contract, name)) is str for name in names)
