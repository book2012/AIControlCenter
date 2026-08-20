import inspect
from dataclasses import FrozenInstanceError, fields
from types import MappingProxyType

import pytest

from core.secrets.mariadb_continuity_evidence_acquisition_descriptor import (
    EvidenceAcquisitionCategory,
)
from core.secrets.mariadb_continuity_evidence_admission import (
    canonical_external_evidence_admission_contract,
)
from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    EvidenceAvailability,
    EvidenceReferenceIdentityClass,
    RecoverEvidenceGate,
    SemanticsChangeRequired,
)
from core.secrets.mariadb_continuity_evidence_source_binding import (
    CATEGORY_TO_BUNDLE_MAPPING,
    CATEGORY_TO_BUNDLE_MAPPING_IS_VERIFICATION_REQUIREMENT_SCOPE,
    MariaDBContinuityEvidenceSourceBindingContract,
    ProtectedSourceBundlePolicy,
    _canonical_bundle,
    canonical_mariadb_continuity_evidence_source_binding_contract,
)


EXPECTED_MAPPING = {
    "AUTH_PLUGIN_AUTHORITATIVE_EVIDENCE": "AUTH_PLUGIN_HISTORICAL_ATTESTATION",
    "ACCOUNT_BINDING": "AUTH_PLUGIN_HISTORICAL_ATTESTATION",
    "PYMYSQL_1_2_0_COMPATIBILITY_EVIDENCE": "PYMYSQL_COMPATIBILITY_ATTESTATION",
    "EXPECTED_DATABASE_IDENTITY": "DATA_IDENTITY_ATTESTATION",
    "EXPECTED_ACCOUNT_IDENTITY": "DATA_IDENTITY_ATTESTATION",
    "REQUIRED_GRANTS": "DATA_IDENTITY_ATTESTATION",
    "FIVE_CATEGORY_DATA_IDENTITY": "DATA_IDENTITY_ATTESTATION",
    "BASELINE_BINDING": "DATA_IDENTITY_ATTESTATION",
    "THREE_CATEGORY_CONTINUITY_LINEAGE": "CONTINUITY_LINEAGE_ATTESTATION",
    "TIMESTAMP_EVIDENCE": "CONTINUITY_LINEAGE_ATTESTATION",
    "IMMUTABLE_INTEGRITY_BINDING": "CONTINUITY_LINEAGE_ATTESTATION",
    "TRUSTED_ISSUER": "CONTINUITY_LINEAGE_ATTESTATION",
}


def test_repository_owned_factory_hardening_invariants():
    contract = canonical_mariadb_continuity_evidence_source_binding_contract()

    with pytest.raises(TypeError):
        ProtectedSourceBundlePolicy()
    assert all(item.init is False for item in fields(ProtectedSourceBundlePolicy))
    with pytest.raises(FrozenInstanceError):
        contract.bundles[0].categories = ()

    assert type(CATEGORY_TO_BUNDLE_MAPPING) is MappingProxyType
    assert tuple(inspect.signature(_canonical_bundle).parameters) == ("identity",)
    assert tuple(bundle.identity for bundle in contract.bundles) == tuple(
        EvidenceReferenceIdentityClass
    )
    assert len(contract.bundles) == 4

    mapped_categories = tuple(CATEGORY_TO_BUNDLE_MAPPING)
    assert len(mapped_categories) == len(set(mapped_categories)) == 12
    assert set(mapped_categories) == set(EvidenceAcquisitionCategory)
    for bundle in contract.bundles:
        assert bundle.categories == tuple(
            category
            for category in EvidenceAcquisitionCategory
            if CATEGORY_TO_BUNDLE_MAPPING[category] is bundle.identity
        )

    assert "subprocess" not in globals()
    assert not any(
        name.startswith("test_") and "git_state" in name
        for name in globals()
    )


def test_closed_immutable_four_bundle_total_mapping_and_direct_type_reuse():
    contract = canonical_mariadb_continuity_evidence_source_binding_contract()
    assert type(CATEGORY_TO_BUNDLE_MAPPING) is MappingProxyType
    assert len(contract.bundles) == 4
    assert tuple(bundle.identity for bundle in contract.bundles) == tuple(
        EvidenceReferenceIdentityClass
    )
    assert set(contract.category_to_bundle_mapping) == set(EvidenceAcquisitionCategory)
    assert len(contract.category_to_bundle_mapping) == 12
    assert {
        category.value: identity.value
        for category, identity in contract.category_to_bundle_mapping.items()
    } == EXPECTED_MAPPING
    categories = tuple(category for bundle in contract.bundles for category in bundle.categories)
    assert len(categories) == len(set(categories)) == 12
    assert set(categories) == set(EvidenceAcquisitionCategory)
    assert all(type(category) is EvidenceAcquisitionCategory for category in categories)
    assert all(
        type(bundle.identity) is EvidenceReferenceIdentityClass
        for bundle in contract.bundles
    )
    with pytest.raises(TypeError):
        CATEGORY_TO_BUNDLE_MAPPING[
            EvidenceAcquisitionCategory.ACCOUNT_BINDING
        ] = EvidenceReferenceIdentityClass.DATA_IDENTITY_ATTESTATION


def test_each_bundle_has_fixed_protected_future_policy_without_fallback():
    contract = canonical_mariadb_continuity_evidence_source_binding_contract()
    for bundle in contract.bundles:
        assert all(
            (
                bundle.mac_control_plane_owned,
                bundle.fixed_protected_source_slot_required,
                bundle.outside_git_required,
                bundle.protected_parent_exact_0700_required,
                bundle.regular_non_symlink_leaf_required,
                bundle.leaf_permissions_no_broader_than_0600_required,
                bundle.explicit_trusted_uid_gid_required,
                bundle.future_fd_inode_binding_required,
                bundle.future_human_authorization_required,
                bundle.future_one_shot_acquisition_required,
            )
        )
        assert bundle.maximum_acquisitions_per_future_authorization == 1
        assert not any(
            (
                bundle.fallback_allowed,
                bundle.enumeration_allowed,
                bundle.candidate_iteration_allowed,
                bundle.environment_home_authority_allowed,
                bundle.argv_transport_allowed,
                bundle.json_value_transport_allowed,
                bundle.evidence_secret_logging_allowed,
                bundle.evidence_secret_hashing_allowed,
            )
        )


def test_mapping_does_not_establish_location_existence_or_pipeline_results():
    contract = canonical_mariadb_continuity_evidence_source_binding_contract()
    assert contract.descriptor_classification_distinct is True
    assert contract.symbolic_source_bundle_identity_distinct is True
    false_facts = (
        contract.concrete_source_location_established,
        contract.source_exists,
        contract.source_metadata_safe,
        contract.content_acquired,
        contract.evidence_exists,
        contract.evidence_admitted,
        contract.evidence_verified,
        contract.authoritative_evidence_exists,
        contract.provenance_valid,
        contract.integrity_valid,
        contract.timestamp_valid,
        contract.issuer_valid,
        contract.account_baseline_valid,
        contract.identity_complete,
        contract.lineage_complete,
        contract.recover_evidence_sufficient,
        contract.production_validation_ready,
        contract.shopping_runtime_activated,
    )
    assert not any(false_facts)
    assert contract.auth_plugin_authoritative_evidence is EvidenceAvailability.UNAVAILABLE
    assert contract.pymysql_compatibility_evidence is EvidenceAvailability.UNAVAILABLE


def test_category_mapping_is_not_admission_verification_requirement_scope():
    admission = canonical_external_evidence_admission_contract()
    assert CATEGORY_TO_BUNDLE_MAPPING_IS_VERIFICATION_REQUIREMENT_SCOPE is False
    assert all(
        (
            admission.provenance_verification_required,
            admission.immutable_integrity_binding_verification_required,
            admission.timestamp_binding_verification_required,
            admission.trusted_issuer_verification_required,
            admission.account_binding_verification_required,
            admission.expected_database_binding_verification_required,
            admission.expected_account_binding_verification_required,
            admission.required_grants_binding_verification_required,
            admission.baseline_binding_verification_required,
            admission.pymysql_1_2_0_compatibility_proof_required,
            admission.reference_verification_required,
        )
    )


def test_contract_is_non_caller_selectable_value_free_and_zero_authority():
    contract = MariaDBContinuityEvidenceSourceBindingContract()
    for item in fields(contract):
        assert item.init is False
        with pytest.raises(TypeError):
            MariaDBContinuityEvidenceSourceBindingContract(**{item.name: True})
    assert all(item.init is False for item in fields(ProtectedSourceBundlePolicy))
    with pytest.raises(TypeError):
        ProtectedSourceBundlePolicy()
    with pytest.raises(TypeError):
        ProtectedSourceBundlePolicy(
            identity=EvidenceReferenceIdentityClass.DATA_IDENTITY_ATTESTATION,
            categories=(EvidenceAcquisitionCategory.ACCOUNT_BINDING,),
        )
    canonical_bundle = contract.bundles[0]
    with pytest.raises(FrozenInstanceError):
        canonical_bundle.identity = EvidenceReferenceIdentityClass.DATA_IDENTITY_ATTESTATION
    with pytest.raises(FrozenInstanceError):
        canonical_bundle.categories = (EvidenceAcquisitionCategory.ACCOUNT_BINDING,)
    names = {item.name.lower() for item in fields(contract)} | {
        item.name.lower() for item in fields(ProtectedSourceBundlePolicy)
    }
    prohibited = {
        "path", "source_path", "home", "environment_variable", "argv",
        "reference", "evidence_value", "credential_value", "credential_hash",
        "sql", "host", "port", "dsn", "url", "database_connection",
    }
    assert names.isdisjoint(prohibited)
    assert contract.repository_only and contract.value_free and contract.fail_closed
    assert contract.zero_authority
    assert not any(
        (
            contract.caller_selection_allowed,
            contract.io_allowed,
            contract.network_allowed,
            contract.sql_allowed,
            contract.process_allowed,
            contract.production_access_allowed,
            contract.runtime_mutation_allowed,
            contract.ubuntu_access_allowed,
            contract.acquisition_authority,
            contract.admission_authority,
            contract.verification_authority,
            contract.authorization_authority,
            contract.capability_authority,
        )
    )
    assert contract.recover_evidence_gate is RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT
    assert contract.sm_01b_02d_06_semantics_change_required is SemanticsChangeRequired.NO
    assert contract.rotate_authorized is False
    assert contract.replace_authorized is False
    assert contract.strategy_executed is False
