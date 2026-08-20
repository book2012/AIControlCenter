import inspect
from dataclasses import FrozenInstanceError, fields

import pytest

from core.secrets.mariadb_continuity_authoritative_mac_protected_evidence_suffix import (
    EXACT_PROTECTED_EVIDENCE_SUFFIX,
    AuthoritativeMacProtectedEvidenceSuffixPolicy,
    AuthoritativeMacProtectedEvidenceSuffixPolicyIdentity,
    canonical_authoritative_mac_protected_evidence_suffix_policy,
)
from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    RecoverEvidenceGate,
    SemanticsChangeRequired,
)
from core.secrets.mariadb_continuity_evidence_source_profile import (
    OfflineAcquisitionAssessment,
)


def test_exact_identity_and_repository_owned_relative_suffix_are_closed():
    policy = canonical_authoritative_mac_protected_evidence_suffix_policy()
    assert tuple(AuthoritativeMacProtectedEvidenceSuffixPolicyIdentity) == (
        AuthoritativeMacProtectedEvidenceSuffixPolicyIdentity.AUTHORITATIVE_MAC_PROTECTED_EVIDENCE_SUFFIX_POLICY,
    )
    assert policy.identity.value == "AUTHORITATIVE_MAC_PROTECTED_EVIDENCE_SUFFIX_POLICY"
    assert EXACT_PROTECTED_EVIDENCE_SUFFIX == (
        "Library/Application Support/AIControlCenter/"
        "protected-external-evidence/mariadb-continuity"
    )
    assert policy.suffix == EXACT_PROTECTED_EVIDENCE_SUFFIX
    assert not policy.suffix.startswith("/")
    assert policy.suffix_is_relative_to_trusted_account_home
    assert policy.exact_suffix_policy_layer_required
    assert policy.exact_suffix_policy_evidence_established_by_architecture_decision
    assert policy.exact_suffix_value_established


def test_policy_is_zero_argument_nonconstructible_frozen_and_caller_unselectable():
    factory = canonical_authoritative_mac_protected_evidence_suffix_policy
    assert not inspect.signature(factory).parameters
    with pytest.raises(TypeError):
        AuthoritativeMacProtectedEvidenceSuffixPolicy()
    policy = factory()
    assert all(item.init is False for item in fields(policy))
    with pytest.raises(FrozenInstanceError):
        policy.suffix = "caller-value"
    with pytest.raises(TypeError):
        factory(suffix="caller-value")
    assert not any((policy.caller_suffix_selection_allowed, policy.caller_base_path_selection_allowed, policy.caller_home_selection_allowed, policy.caller_absolute_path_selection_allowed, policy.caller_concrete_path_selection_allowed))


def test_no_runtime_resolution_path_or_filesystem_factual_promotion():
    policy = canonical_authoritative_mac_protected_evidence_suffix_policy()
    assert not any((policy.absolute_path_established, policy.concrete_path_value_established, policy.runtime_home_resolver_available, policy.authoritative_base_location_already_exists, policy.source_existence_established, policy.historical_evidence_existence_established, policy.metadata_inspection_performed, policy.source_metadata_safe, policy.content_acquisition_performed, policy.evidence_admitted, policy.evidence_verified, policy.recover_evidence_sufficient, policy.filesystem_io_allowed))
    assert policy.offline_acquisition_possible is OfflineAcquisitionAssessment.UNKNOWN
    assert policy.recover_evidence_gate is RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT


def test_zero_authority_architecture_and_downstream_separation_are_preserved():
    policy = canonical_authoritative_mac_protected_evidence_suffix_policy()
    assert all((policy.repository_owned, policy.mac_control_plane_owned, policy.zero_authority, policy.fail_closed))
    assert not any((policy.authorization_authority, policy.capability_authority, policy.execution_authority, policy.mutation_authority, policy.retry_authority, policy.reconnect_authority, policy.rollback_authority, policy.acquisition_authority, policy.admission_authority, policy.verification_authority, policy.production_access_allowed, policy.protected_source_access_allowed, policy.ubuntu_access_allowed, policy.governance_core_coupled, policy.sec_02_coupled, policy.controlled_execution_port_coupled, policy.legacy_caller_path_observer_reachable, policy.production_access_currently_justified, policy.production_validation_ready, policy.shopping_runtime_activated))
    assert policy.sm_01b_02d_06_semantics_change_required is SemanticsChangeRequired.NO
