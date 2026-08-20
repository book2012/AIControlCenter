import inspect
from dataclasses import FrozenInstanceError, fields
from types import MappingProxyType

import pytest

from core.secrets.mariadb_continuity_evidence_acquisition_descriptor import (
    EvidenceAcquisitionCategory,
)
from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    EvidenceReferenceIdentityClass,
    RecoverEvidenceGate,
    SemanticsChangeRequired,
)
from core.secrets.mariadb_continuity_evidence_source_binding import (
    CATEGORY_TO_BUNDLE_MAPPING,
)
from core.secrets.mariadb_continuity_evidence_source_profile import (
    BUNDLE_TO_PROTECTED_SOURCE_PROFILE_MAPPING,
    MariaDBContinuityEvidenceSourceProfileContract,
    OfflineAcquisitionAssessment,
    ProtectedExternalEvidenceSourceProfile,
    ProtectedExternalEvidenceSourceProfileIdentity,
    _canonical_profile,
    canonical_mariadb_continuity_evidence_source_profile_contract,
)


EXPECTED_MAPPING = {
    "AUTH_PLUGIN_HISTORICAL_ATTESTATION": "AUTH_PLUGIN_PROTECTED_SOURCE_PROFILE",
    "PYMYSQL_COMPATIBILITY_ATTESTATION": "PYMYSQL_PROTECTED_SOURCE_PROFILE",
    "DATA_IDENTITY_ATTESTATION": "DATA_IDENTITY_PROTECTED_SOURCE_PROFILE",
    "CONTINUITY_LINEAGE_ATTESTATION": (
        "CONTINUITY_LINEAGE_PROTECTED_SOURCE_PROFILE"
    ),
}


def test_closed_four_profile_identities_and_complete_immutable_mapping():
    assert len(ProtectedExternalEvidenceSourceProfileIdentity) == 4
    assert type(BUNDLE_TO_PROTECTED_SOURCE_PROFILE_MAPPING) is MappingProxyType
    assert set(BUNDLE_TO_PROTECTED_SOURCE_PROFILE_MAPPING) == set(
        EvidenceReferenceIdentityClass
    )
    assert set(BUNDLE_TO_PROTECTED_SOURCE_PROFILE_MAPPING.values()) == set(
        ProtectedExternalEvidenceSourceProfileIdentity
    )
    assert {
        bundle.value: profile.value
        for bundle, profile in BUNDLE_TO_PROTECTED_SOURCE_PROFILE_MAPPING.items()
    } == EXPECTED_MAPPING
    with pytest.raises(TypeError):
        BUNDLE_TO_PROTECTED_SOURCE_PROFILE_MAPPING[
            EvidenceReferenceIdentityClass.DATA_IDENTITY_ATTESTATION
        ] = ProtectedExternalEvidenceSourceProfileIdentity.DATA_IDENTITY_PROTECTED_SOURCE_PROFILE


def test_canonical_factory_is_private_single_input_and_repository_derived():
    assert tuple(inspect.signature(_canonical_profile).parameters) == (
        "bundle_identity",
    )
    with pytest.raises(TypeError):
        _canonical_profile(
            EvidenceReferenceIdentityClass.DATA_IDENTITY_ATTESTATION,
            ProtectedExternalEvidenceSourceProfileIdentity.DATA_IDENTITY_PROTECTED_SOURCE_PROFILE,
        )
    with pytest.raises(TypeError):
        _canonical_profile(
            bundle_identity=EvidenceReferenceIdentityClass.DATA_IDENTITY_ATTESTATION,
            profile_identity=(
                ProtectedExternalEvidenceSourceProfileIdentity.DATA_IDENTITY_PROTECTED_SOURCE_PROFILE
            ),
        )
    with pytest.raises(TypeError):
        _canonical_profile(
            bundle_identity=EvidenceReferenceIdentityClass.DATA_IDENTITY_ATTESTATION,
            mapping={},
        )

    contract = canonical_mariadb_continuity_evidence_source_profile_contract()
    for profile in contract.profiles:
        bundle_identity = profile.bundle_policy.identity
        assert profile.identity is BUNDLE_TO_PROTECTED_SOURCE_PROFILE_MAPPING[
            bundle_identity
        ]


def test_profiles_are_nonconstructible_frozen_total_unique_and_distinct():
    with pytest.raises(TypeError):
        ProtectedExternalEvidenceSourceProfile()
    assert all(
        item.init is False for item in fields(ProtectedExternalEvidenceSourceProfile)
    )
    contract = canonical_mariadb_continuity_evidence_source_profile_contract()
    assert len(contract.profiles) == 4
    assert len({profile.identity for profile in contract.profiles}) == 4
    assert tuple(
        profile.bundle_policy.identity for profile in contract.profiles
    ) == tuple(EvidenceReferenceIdentityClass)
    assert all(
        type(profile.identity) is ProtectedExternalEvidenceSourceProfileIdentity
        and type(profile.bundle_policy.identity) is EvidenceReferenceIdentityClass
        and profile.identity.value != profile.bundle_policy.identity.value
        for profile in contract.profiles
    )
    with pytest.raises(FrozenInstanceError):
        contract.profiles[0].identity = (
            ProtectedExternalEvidenceSourceProfileIdentity.DATA_IDENTITY_PROTECTED_SOURCE_PROFILE
        )


def test_profiles_promote_no_location_existence_metadata_or_pipeline_fact():
    contract = canonical_mariadb_continuity_evidence_source_profile_contract()
    for profile in contract.profiles:
        assert profile.profile_is_symbolic and profile.mac_control_plane_owned
        assert not any(
            (
                profile.concrete_source_location_established,
                profile.source_path_defined,
                profile.source_exists,
                profile.source_metadata_inspected,
                profile.source_metadata_safe,
                profile.content_acquired,
                profile.evidence_admitted,
                profile.evidence_verified,
                profile.authority,
            )
        )
    assert contract.descriptor_classification_distinct
    assert contract.source_bundle_identity_distinct
    assert contract.protected_source_profile_identity_distinct
    assert not any(
        (
            contract.concrete_source_location_established,
            contract.source_exists,
            contract.historical_evidence_exists,
            contract.source_metadata_safe,
            contract.content_acquired,
            contract.evidence_admitted,
            contract.evidence_verified,
            contract.authority,
        )
    )


def test_unknown_offline_assessment_and_current_production_facts_fail_closed():
    contract = canonical_mariadb_continuity_evidence_source_profile_contract()
    assert tuple(OfflineAcquisitionAssessment) == (
        OfflineAcquisitionAssessment.UNKNOWN,
    )
    assert (
        contract.offline_acquisition_assessment
        is OfflineAcquisitionAssessment.UNKNOWN
    )
    assert contract.production_access_currently_justified is False
    assert contract.production_access_allowed is False
    assert contract.historical_evidence_exists is False
    field_names = {item.name for item in fields(contract)}
    assert "offline_acquisition_possible" not in field_names
    assert "production_access_permanently_unnecessary" not in field_names


def test_contract_preserves_zero_authority_phase06_and_binding_scope():
    contract = MariaDBContinuityEvidenceSourceProfileContract()
    assert all(item.init is False for item in fields(contract))
    assert all(
        (
            contract.exact_four_profiles,
            contract.repository_only,
            contract.value_free,
            contract.fail_closed,
            contract.zero_authority,
        )
    )
    assert not any(
        (
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
            contract.rotate_authorized,
            contract.replace_authorized,
            contract.strategy_executed,
            contract.production_validation_ready,
            contract.shopping_runtime_activated,
            contract.category_to_bundle_mapping_is_verification_requirement_scope,
        )
    )
    assert contract.recover_evidence_gate is RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT
    assert contract.sm_01b_02d_06_semantics_change_required is SemanticsChangeRequired.NO
    assert len(CATEGORY_TO_BUNDLE_MAPPING) == 12
    assert set(CATEGORY_TO_BUNDLE_MAPPING) == set(EvidenceAcquisitionCategory)


def test_no_permanent_repository_history_pytest_invariant_is_introduced():
    assert not any(
        name.startswith("test_") and "git_state" in name
        for name in globals()
    )
