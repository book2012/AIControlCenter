from dataclasses import fields

import pytest

from core.secrets.mariadb_continuity_evidence_acquisition_descriptor import (
    EvidenceAcquisitionCategory,
    EvidenceAcquisitionDescriptor,
    MariaDBContinuityEvidenceAcquisitionContract,
    canonical_mariadb_continuity_evidence_acquisition_contract,
)
from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    EvidenceAvailability,
    RecoverEvidenceGate,
    SemanticsChangeRequired,
)
from core.secrets.mariadb_continuity_evidence_reference_manifest import VerificationState
from core.secrets.mariadb_continuity_sources import (
    ContinuityEvidenceCategory,
    DataIdentityCategory,
)


EXPECTED_CATEGORIES = (
    "AUTH_PLUGIN_AUTHORITATIVE_EVIDENCE",
    "PYMYSQL_1_2_0_COMPATIBILITY_EVIDENCE",
    "EXPECTED_DATABASE_IDENTITY",
    "EXPECTED_ACCOUNT_IDENTITY",
    "REQUIRED_GRANTS",
    "FIVE_CATEGORY_DATA_IDENTITY",
    "THREE_CATEGORY_CONTINUITY_LINEAGE",
    "TIMESTAMP_EVIDENCE",
    "IMMUTABLE_INTEGRITY_BINDING",
    "TRUSTED_ISSUER",
    "ACCOUNT_BINDING",
    "BASELINE_BINDING",
)


def test_exact_closed_twelve_category_coverage_and_direct_type_reuse():
    contract = canonical_mariadb_continuity_evidence_acquisition_contract()
    assert tuple(item.value for item in EvidenceAcquisitionCategory) == EXPECTED_CATEGORIES
    assert tuple(item.category for item in contract.descriptors) == tuple(
        EvidenceAcquisitionCategory
    )
    assert len(contract.descriptors) == 12
    assert len(set(contract.descriptors)) == 12
    assert contract.data_identity_categories == tuple(DataIdentityCategory)
    assert contract.continuity_evidence_categories == tuple(ContinuityEvidenceCategory)
    assert type(contract.verification_state) is VerificationState
    assert type(contract.auth_plugin_authoritative_evidence) is EvidenceAvailability
    assert type(contract.recover_evidence_gate) is RecoverEvidenceGate


def test_each_descriptor_is_closed_value_free_and_fail_closed():
    contract = canonical_mariadb_continuity_evidence_acquisition_contract()
    for descriptor in contract.descriptors:
        assert descriptor.repository_defined_identity_selection_required is True
        assert descriptor.independently_pre_existing_source_required is True
        assert descriptor.mac_control_plane_owned is True
        assert descriptor.metadata_only_sufficient is False
        assert descriptor.content_required is True
        assert descriptor.secret_bearing_content_permitted is False
        assert descriptor.production_access_required is False
        assert descriptor.future_human_authorization_required is True
        assert descriptor.future_one_shot_acquisition_required is True
        assert descriptor.external_immutable_artifact_required is True
        assert descriptor.repository_only_verification_sufficient is False
        assert descriptor.acquisition_grants_authority is False
        assert descriptor.current_availability is EvidenceAvailability.UNAVAILABLE
        for item in fields(descriptor):
            if item.name != "category":
                assert item.init is False
                with pytest.raises(TypeError):
                    EvidenceAcquisitionDescriptor(
                        EvidenceAcquisitionCategory.AUTH_PLUGIN_AUTHORITATIVE_EVIDENCE,
                        **{item.name: True},
                    )


def test_contract_rejects_caller_facts_paths_references_and_values():
    contract = MariaDBContinuityEvidenceAcquisitionContract()
    for item in fields(contract):
        assert item.init is False
        with pytest.raises(TypeError):
            MariaDBContinuityEvidenceAcquisitionContract(**{item.name: True})
        with pytest.raises((AttributeError, TypeError)):
            setattr(contract, item.name, True)
    prohibited = {
        "path", "source_path", "reference", "identifier", "artifact", "contents",
        "credential", "credential_hash", "hash", "digest", "signature", "timestamp",
        "issuer_identifier", "historical_account_identifier", "external_evidence_value",
    }
    names = {item.name for item in fields(contract)} | {
        item.name for item in fields(EvidenceAcquisitionDescriptor)
    }
    assert names.isdisjoint(prohibited)
    assert not any(type(getattr(contract, item.name)) is str for item in fields(contract))


def test_all_existence_verification_recover_and_readiness_facts_are_separate():
    contract = canonical_mariadb_continuity_evidence_acquisition_contract()
    assert contract.verification_state is VerificationState.UNAVAILABLE
    assert contract.auth_plugin_authoritative_evidence is EvidenceAvailability.UNAVAILABLE
    assert contract.pymysql_compatibility_evidence is EvidenceAvailability.UNAVAILABLE
    assert all(
        fact is False
        for fact in (
            contract.source_exists,
            contract.evidence_exists,
            contract.content_acquired,
            contract.evidence_admitted,
            contract.verification_succeeded,
            contract.authoritative_evidence_exists,
            contract.five_category_data_identity_complete,
            contract.three_category_continuity_lineage_complete,
            contract.recover_evidence_sufficient,
            contract.production_validation_ready,
            contract.shopping_runtime_activated,
        )
    )
    assert contract.recover_evidence_gate is RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT


def test_repository_only_zero_authority_and_phase_06_are_unchanged():
    contract = canonical_mariadb_continuity_evidence_acquisition_contract()
    assert contract.repository_only is True
    assert contract.value_free is True
    assert contract.fail_closed is True
    assert contract.zero_authority is True
    assert contract.sm_01b_02d_06_semantics_change_required is SemanticsChangeRequired.NO
    assert all(
        fact is False
        for fact in (
            contract.io_allowed,
            contract.network_allowed,
            contract.sql_allowed,
            contract.production_access_allowed,
            contract.runtime_mutation_allowed,
            contract.caller_positive_fact_injection_allowed,
            contract.caller_source_path_allowed,
            contract.arbitrary_reference_string_allowed,
            contract.external_evidence_values_accepted,
            contract.verification_authority,
            contract.admission_authority,
            contract.acquisition_authority,
            contract.rotate_authorized,
            contract.replace_authorized,
            contract.strategy_executed,
        )
    )
