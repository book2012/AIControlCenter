from dataclasses import FrozenInstanceError

import pytest

from core.secrets.mariadb_continuity_concrete_protected_evidence_path import ConcreteProtectedEvidencePath
from core.secrets.mariadb_continuity_evidence_fixed_source_slot import ProtectedExternalEvidenceFixedSourceSlotIdentity as Slot
from core.secrets.mariadb_continuity_protected_evidence_acquisition_authorization import ProtectedEvidenceAcquisitionAuthorization, ProtectedEvidenceAcquisitionRequest, acquisition_request, issue_acquisition_authorization, validate_acquisition_request
from core.secrets.mariadb_continuity_protected_evidence_leaf_locator import compose_concrete_protected_evidence_leaf_path


def request(identity="request-1", slot=Slot.AUTH_PLUGIN_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT):
    parent = object.__new__(ConcreteProtectedEvidencePath)
    object.__setattr__(parent, "concrete_path", "/synthetic/protected")
    return acquisition_request(identity, compose_concrete_protected_evidence_leaf_path(parent, slot))


def test_exact_binding_one_attempt_and_no_positive_injection():
    req = request()
    auth = issue_acquisition_authorization("authorization-1", req)
    assert auth.maximum_acquisition_attempts == 1
    assert auth.human_authorization_evidence_supplied is False
    assert auth.authorization_authority is False
    assert all(getattr(auth, name) == getattr(req, name) for name in ("acquisition_request_id", "fixed_source_slot_identity", "concrete_source_location_identity", "leaf_basename", "concrete_leaf_path"))
    with pytest.raises(TypeError):
        ProtectedEvidenceAcquisitionRequest()
    with pytest.raises(TypeError):
        ProtectedEvidenceAcquisitionAuthorization()
    with pytest.raises(FrozenInstanceError):
        auth.maximum_acquisition_attempts = 2


def test_four_sources_require_four_fresh_authorizations():
    authorizations = [issue_acquisition_authorization(f"authorization-{n}", request(f"request-{n}", slot)) for n, slot in enumerate(Slot)]
    assert len({value.authorization_id for value in authorizations}) == 4
    assert len({value.acquisition_request_id for value in authorizations}) == 4
    assert len({value.fixed_source_slot_identity for value in authorizations}) == 4
    assert not any(hasattr(authorizations[0], name) for name in ("execution_authority", "mutation_authority", "retry_authority"))


def test_tampered_request_fails_revalidation():
    req = request()
    object.__setattr__(req, "leaf_basename", "caller")
    with pytest.raises(ValueError):
        validate_acquisition_request(req)
