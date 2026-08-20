import inspect
from dataclasses import FrozenInstanceError, fields
from types import MappingProxyType

import pytest

from core.secrets.mariadb_continuity_evidence_concrete_source_location import (
    FIXED_SOURCE_SLOT_TO_CONCRETE_LOCATION_MAPPING,
    MariaDBContinuityEvidenceConcreteSourceLocationContract,
    ProtectedExternalEvidenceBaseLocationIdentity,
    ProtectedExternalEvidenceConcreteSourceLocation,
    ProtectedExternalEvidenceConcreteSourceLocationIdentity,
    _canonical_concrete_source_location,
)
from core.secrets.mariadb_continuity_evidence_fixed_source_slot import (
    ProtectedExternalEvidenceFixedSourceSlotIdentity,
)


def test_exact_four_slots_map_one_to_one_to_closed_locations():
    mapping = FIXED_SOURCE_SLOT_TO_CONCRETE_LOCATION_MAPPING
    assert type(mapping) is MappingProxyType
    assert set(mapping) == set(ProtectedExternalEvidenceFixedSourceSlotIdentity)
    assert set(mapping.values()) == set(ProtectedExternalEvidenceConcreteSourceLocationIdentity)
    assert len(mapping) == len(set(mapping.values())) == 4
    with pytest.raises(TypeError):
        mapping[next(iter(mapping))] = next(iter(mapping.values()))


def test_descriptor_is_canonical_nonconstructible_and_immutable():
    assert tuple(inspect.signature(_canonical_concrete_source_location).parameters) == ("slot_identity",)
    with pytest.raises(TypeError):
        ProtectedExternalEvidenceConcreteSourceLocation()
    contract = MariaDBContinuityEvidenceConcreteSourceLocationContract()
    assert len(contract.locations) == 4
    assert all(item.init is False for item in fields(ProtectedExternalEvidenceConcreteSourceLocation))
    with pytest.raises(FrozenInstanceError):
        contract.locations[0].identity = contract.locations[1].identity
    with pytest.raises(TypeError):
        _canonical_concrete_source_location(next(iter(ProtectedExternalEvidenceFixedSourceSlotIdentity)), path="x")


def test_closed_base_identity_does_not_invent_or_establish_a_path():
    contract = MariaDBContinuityEvidenceConcreteSourceLocationContract()
    assert tuple(ProtectedExternalEvidenceBaseLocationIdentity) == (
        ProtectedExternalEvidenceBaseLocationIdentity.PROTECTED_EXTERNAL_EVIDENCE_BASE_LOCATION,
    )
    assert all(location.closed_repository_owned_descriptor for location in contract.locations)
    assert all(location.base_identity is next(iter(ProtectedExternalEvidenceBaseLocationIdentity)) for location in contract.locations)
    assert all(location.operational_path_establishment_pending for location in contract.locations)
    assert not contract.authoritative_base_path_exists
    assert not contract.concrete_path_value_established
    assert not any(location.absolute_path_value_established for location in contract.locations)


def test_location_and_existence_facts_remain_independently_false():
    contract = MariaDBContinuityEvidenceConcreteSourceLocationContract()
    assert contract.concrete_location_descriptor_established
    assert not any((
        contract.source_exists, contract.historical_evidence_exists,
        contract.source_metadata_inspected, contract.source_metadata_safe,
        contract.content_acquired, contract.evidence_admitted,
        contract.evidence_verified, contract.recover_evidence_sufficient,
        contract.authority, contract.production_access_currently_justified,
        contract.production_validation_ready, contract.shopping_runtime_activated,
    ))


def test_caller_and_all_external_path_authority_are_closed():
    contract = MariaDBContinuityEvidenceConcreteSourceLocationContract()
    assert not any((
        contract.caller_location_selection_allowed,
        contract.caller_path_injection_allowed,
        contract.environment_path_authority_allowed,
        contract.home_environment_authority_allowed,
        contract.argv_path_authority_allowed,
        contract.fallback_path_allowed,
        contract.path_enumeration_allowed,
        contract.candidate_iteration_allowed,
        contract.io_allowed, contract.network_allowed, contract.process_allowed,
        contract.sql_allowed, contract.production_access_allowed,
        contract.ubuntu_access_allowed,
    ))
    assert all(location.fixed_source_slot.outside_git_required for location in contract.locations)
    assert all(location.fixed_source_slot.future_fd_inode_binding_required for location in contract.locations)
