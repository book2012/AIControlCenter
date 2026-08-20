import inspect
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from types import MappingProxyType

import pytest

from core.secrets.mariadb_continuity_authoritative_mac_base_path import (
    BASE_LOCATION_TO_AUTHORITATIVE_MAC_BASE_PATH_POLICY_MAPPING,
    AuthoritativeMacProtectedEvidenceBasePathPolicy,
    AuthoritativeMacProtectedEvidenceBasePathPolicyIdentity,
    _canonical_authoritative_mac_base_path_policy,
)
from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    RecoverEvidenceGate,
    SemanticsChangeRequired,
)
from core.secrets.mariadb_continuity_evidence_concrete_source_location import (
    ProtectedExternalEvidenceBaseLocationIdentity,
)
from core.secrets.mariadb_continuity_evidence_source_profile import (
    OfflineAcquisitionAssessment,
)


def test_exactly_one_base_identity_maps_immutably_to_one_policy_identity():
    mapping = BASE_LOCATION_TO_AUTHORITATIVE_MAC_BASE_PATH_POLICY_MAPPING
    assert type(mapping) is MappingProxyType
    assert tuple(mapping) == tuple(ProtectedExternalEvidenceBaseLocationIdentity)
    assert tuple(mapping.values()) == tuple(AuthoritativeMacProtectedEvidenceBasePathPolicyIdentity)
    assert len(mapping) == len(set(mapping.values())) == 1
    with pytest.raises(TypeError):
        mapping[next(iter(mapping))] = next(iter(mapping.values()))


def test_policy_is_canonical_nonconstructible_frozen_and_caller_unselectable():
    assert not inspect.signature(_canonical_authoritative_mac_base_path_policy).parameters
    with pytest.raises(TypeError):
        AuthoritativeMacProtectedEvidenceBasePathPolicy()
    policy = _canonical_authoritative_mac_base_path_policy()
    assert all(item.init is False for item in fields(policy))
    with pytest.raises(FrozenInstanceError):
        policy.identity = next(iter(AuthoritativeMacProtectedEvidenceBasePathPolicyIdentity))
    with pytest.raises(TypeError):
        _canonical_authoritative_mac_base_path_policy(path="caller-value")


def test_policy_defines_only_value_free_repository_facts():
    policy = _canonical_authoritative_mac_base_path_policy()
    assert policy.base_path_policy_layer_required
    assert policy.authoritative_base_path_policy_defined
    assert all((policy.frozen, policy.slotted, policy.repository_owned, policy.mac_control_plane_owned, policy.value_free, policy.fail_closed, policy.zero_authority))
    assert not any(isinstance(getattr(policy, item.name), Path) for item in fields(policy))
    assert not any(type(getattr(policy, item.name)) is str for item in fields(policy))
    assert not policy.exact_protected_evidence_suffix_established
    assert not policy.concrete_path_value_established
    assert not policy.runtime_home_resolver_available


def test_all_path_sources_factual_promotions_and_authorities_remain_closed():
    policy = _canonical_authoritative_mac_base_path_policy()
    false_facts = (
        policy.authoritative_base_location_already_exists,
        policy.source_existence_established,
        policy.historical_evidence_existence_established,
        policy.metadata_inspection_performed,
        policy.source_metadata_safe,
        policy.content_acquisition_performed,
        policy.evidence_admitted,
        policy.evidence_verified,
        policy.recover_evidence_sufficient,
        policy.production_access_currently_justified,
        policy.production_validation_ready,
        policy.shopping_runtime_activated,
        policy.caller_base_path_selection_allowed,
        policy.caller_path_injection_allowed,
        policy.caller_suffix_injection_allowed,
        policy.environment_path_authority_allowed,
        policy.home_environment_authority_allowed,
        policy.argv_path_authority_allowed,
        policy.fallback_allowed,
        policy.path_enumeration_allowed,
        policy.candidate_iteration_allowed,
        policy.filesystem_io_allowed,
        policy.authorization_authority,
        policy.capability_authority,
        policy.execution_authority,
        policy.mutation_authority,
        policy.retry_authority,
        policy.reconnect_authority,
        policy.rollback_authority,
        policy.acquisition_authority,
        policy.admission_authority,
        policy.verification_authority,
        policy.production_access_allowed,
        policy.protected_source_access_allowed,
        policy.mariadb_access_allowed,
        policy.sql_allowed,
        policy.process_allowed,
        policy.ubuntu_access_allowed,
    )
    assert not any(false_facts)
    assert policy.offline_acquisition_possible is OfflineAcquisitionAssessment.UNKNOWN
    assert policy.recover_evidence_gate is RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT
    assert policy.sm_01b_02d_06_semantics_change_required is SemanticsChangeRequired.NO
