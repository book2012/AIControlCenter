import inspect
from dataclasses import FrozenInstanceError, fields
from types import MappingProxyType

import pytest

from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    RecoverEvidenceGate,
    SemanticsChangeRequired,
)
from core.secrets.mariadb_continuity_evidence_fixed_source_slot import (
    PROFILE_TO_FIXED_SOURCE_SLOT_MAPPING,
    MariaDBContinuityEvidenceFixedSourceSlotContract,
    ProtectedExternalEvidenceFixedSourceSlot,
    ProtectedExternalEvidenceFixedSourceSlotIdentity,
    _canonical_fixed_source_slot,
    canonical_mariadb_continuity_evidence_fixed_source_slot_contract,
)
from core.secrets.mariadb_continuity_evidence_source_profile import (
    OfflineAcquisitionAssessment,
    ProtectedExternalEvidenceSourceProfileIdentity,
)


EXPECTED_MAPPING = {
    "AUTH_PLUGIN_PROTECTED_SOURCE_PROFILE":
        "AUTH_PLUGIN_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT",
    "PYMYSQL_PROTECTED_SOURCE_PROFILE":
        "PYMYSQL_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT",
    "DATA_IDENTITY_PROTECTED_SOURCE_PROFILE":
        "DATA_IDENTITY_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT",
    "CONTINUITY_LINEAGE_PROTECTED_SOURCE_PROFILE":
        "CONTINUITY_LINEAGE_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT",
}


def test_exact_four_slot_identities_and_total_unique_immutable_mapping():
    assert len(ProtectedExternalEvidenceFixedSourceSlotIdentity) == 4
    assert type(PROFILE_TO_FIXED_SOURCE_SLOT_MAPPING) is MappingProxyType
    assert set(PROFILE_TO_FIXED_SOURCE_SLOT_MAPPING) == set(
        ProtectedExternalEvidenceSourceProfileIdentity
    )
    assert set(PROFILE_TO_FIXED_SOURCE_SLOT_MAPPING.values()) == set(
        ProtectedExternalEvidenceFixedSourceSlotIdentity
    )
    assert len(set(PROFILE_TO_FIXED_SOURCE_SLOT_MAPPING.values())) == 4
    assert {
        profile.value: slot.value
        for profile, slot in PROFILE_TO_FIXED_SOURCE_SLOT_MAPPING.items()
    } == EXPECTED_MAPPING
    with pytest.raises(TypeError):
        PROFILE_TO_FIXED_SOURCE_SLOT_MAPPING[
            ProtectedExternalEvidenceSourceProfileIdentity.DATA_IDENTITY_PROTECTED_SOURCE_PROFILE
        ] = ProtectedExternalEvidenceFixedSourceSlotIdentity.DATA_IDENTITY_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT


def test_private_factory_accepts_only_repository_owned_existing_profile_identity():
    assert tuple(inspect.signature(_canonical_fixed_source_slot).parameters) == (
        "profile_identity",
    )
    profile = (
        ProtectedExternalEvidenceSourceProfileIdentity.DATA_IDENTITY_PROTECTED_SOURCE_PROFILE
    )
    slot = _canonical_fixed_source_slot(profile)
    assert type(slot.profile_identity) is ProtectedExternalEvidenceSourceProfileIdentity
    assert slot.identity is PROFILE_TO_FIXED_SOURCE_SLOT_MAPPING[profile]
    with pytest.raises(TypeError):
        _canonical_fixed_source_slot(profile, slot.identity)
    with pytest.raises(TypeError):
        _canonical_fixed_source_slot(profile_identity=profile, mapping={})
    with pytest.raises(TypeError):
        _canonical_fixed_source_slot(profile_identity=profile, path="source")


def test_slots_are_nonconstructible_frozen_and_have_no_caller_positive_facts():
    with pytest.raises(TypeError):
        ProtectedExternalEvidenceFixedSourceSlot()
    for item in fields(ProtectedExternalEvidenceFixedSourceSlot):
        assert item.init is False
        with pytest.raises(TypeError):
            ProtectedExternalEvidenceFixedSourceSlot(**{item.name: True})
    contract = canonical_mariadb_continuity_evidence_fixed_source_slot_contract()
    assert len(contract.slots) == 4
    assert len({slot.identity for slot in contract.slots}) == 4
    with pytest.raises(FrozenInstanceError):
        contract.slots[0].identity = contract.slots[1].identity


def test_all_future_protection_requirements_are_closed_and_fail_closed():
    contract = canonical_mariadb_continuity_evidence_fixed_source_slot_contract()
    for slot in contract.slots:
        assert all((
            slot.mac_control_plane_owned,
            slot.outside_git_required,
            slot.protected_parent_exact_0700_required,
            slot.regular_non_symlink_leaf_required,
            slot.leaf_permissions_no_broader_than_0600_required,
            slot.explicit_trusted_uid_gid_required,
            slot.future_fd_inode_binding_required,
            slot.future_human_authorization_required,
            slot.future_one_shot_acquisition_required,
        ))
        assert slot.maximum_acquisitions_per_future_authorization == 1
        assert not any((
            slot.fallback_allowed,
            slot.enumeration_allowed,
            slot.candidate_iteration_allowed,
            slot.environment_home_authority_allowed,
            slot.argv_transport_allowed,
            slot.json_value_transport_allowed,
            slot.evidence_secret_logging_allowed,
            slot.evidence_secret_hashing_allowed,
        ))


def test_slot_contract_preserves_identity_path_and_all_factual_separations():
    contract = canonical_mariadb_continuity_evidence_fixed_source_slot_contract()
    assert all((
        contract.evidence_acquisition_category_distinct,
        contract.source_bundle_identity_distinct,
        contract.protected_source_profile_identity_distinct,
        contract.fixed_source_slot_identity_distinct,
    ))
    assert not any((
        contract.concrete_source_location_established,
        contract.source_path_defined,
        contract.source_exists,
        contract.historical_evidence_exists,
        contract.source_metadata_inspected,
        contract.source_metadata_safe,
        contract.content_acquired,
        contract.evidence_admitted,
        contract.evidence_verified,
        contract.authority,
        contract.recover_evidence_sufficient,
    ))
    field_names = {item.name for item in fields(contract)}
    assert "source_path" not in field_names
    assert "locator" not in field_names
    assert "offline_acquisition_possible" not in field_names


def test_unknown_offline_production_unjustified_and_zero_authority():
    contract = MariaDBContinuityEvidenceFixedSourceSlotContract()
    assert tuple(OfflineAcquisitionAssessment) == (OfflineAcquisitionAssessment.UNKNOWN,)
    assert contract.offline_acquisition_assessment is OfflineAcquisitionAssessment.UNKNOWN
    assert contract.production_access_currently_justified is False
    assert not any((
        contract.caller_slot_selection_allowed,
        contract.caller_path_injection_allowed,
        contract.io_allowed,
        contract.metadata_inspection_allowed,
        contract.source_resolution_allowed,
        contract.content_acquisition_allowed,
        contract.admission_allowed,
        contract.verification_allowed,
        contract.network_allowed,
        contract.process_allowed,
        contract.sql_allowed,
        contract.production_access_allowed,
        contract.runtime_mutation_allowed,
        contract.ubuntu_access_allowed,
        contract.acquisition_authority,
        contract.admission_authority,
        contract.verification_authority,
        contract.authorization_authority,
        contract.capability_authority,
    ))


def test_phase06_and_verification_scope_are_preserved_without_authorization():
    contract = canonical_mariadb_continuity_evidence_fixed_source_slot_contract()
    assert all(item.init is False for item in fields(contract))
    assert all((
        contract.exact_four_fixed_source_slots,
        contract.repository_only,
        contract.symbolic_fixed_source_slot,
        contract.value_free,
        contract.fail_closed,
        contract.zero_authority,
    ))
    assert contract.category_to_bundle_mapping_is_verification_requirement_scope is False
    assert contract.recover_evidence_gate is RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT
    assert contract.sm_01b_02d_06_semantics_change_required is SemanticsChangeRequired.NO
    assert not any((
        contract.rotate_authorized,
        contract.replace_authorized,
        contract.strategy_executed,
        contract.production_validation_ready,
        contract.shopping_runtime_activated,
    ))


def test_no_permanent_repository_history_pytest_invariant_is_introduced():
    assert not any(
        name.startswith("test_") and "git_state" in name for name in globals()
    )
