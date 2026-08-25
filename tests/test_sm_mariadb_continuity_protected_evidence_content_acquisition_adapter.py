from pathlib import Path
import copy
import inspect
import os
import pickle
from threading import Lock

import pytest

from core.secrets.mariadb_continuity_concrete_protected_evidence_path import ConcreteProtectedEvidencePath
from core.secrets.mariadb_continuity_evidence_fixed_source_slot import ProtectedExternalEvidenceFixedSourceSlotIdentity as Slot
from core.secrets.mariadb_continuity_protected_evidence_acquisition_authorization import ProtectedEvidenceAcquisitionInvocationCapability, ProtectedEvidenceAcquisitionInvocationCapabilityState, ProtectedEvidenceAcquisitionRequest, ProtectedEvidenceHumanAuthorizationEvidence, ProtectedEvidenceHumanAuthorizationValidation, acquisition_request, issue_acquisition_authorization
from core.secrets.mariadb_continuity_protected_evidence_content_acquisition import ProtectedEvidenceContentAcquisitionError, ProtectedEvidenceContentAcquisitionErrorCode as Code
from core.secrets.mariadb_continuity_protected_evidence_leaf_locator import compose_concrete_protected_evidence_leaf_path
from core.secrets.mariadb_continuity_trusted_ownership_expectation import TrustedOwnershipExpectation
from ops.macos.shopping.mariadb_continuity_protected_evidence_acquisition_authorization_sqlite_path_policy import ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity
from ops.macos.shopping.mariadb_continuity_protected_evidence_content_acquisition_adapter import MAXIMUM_BOUNDED_READ_BYTES, MAXIMUM_SUCCESS_CONTENT_BYTES, PRODUCTION_ACQUISITION_AVAILABLE, MacProtectedEvidenceContentAcquisitionMechanism, MariaDBContinuityProtectedEvidenceContentAcquisitionAdapter, _leaf_mode_accepted

REPOSITORY = Path(__file__).resolve().parents[1]


def setup_values(tmp_path):
    parent = object.__new__(ConcreteProtectedEvidencePath)
    object.__setattr__(parent, "concrete_path", str(tmp_path / "unopened-protected"))
    request = acquisition_request(
        "request",
        compose_concrete_protected_evidence_leaf_path(
            parent, Slot.AUTH_PLUGIN_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT),
    )
    identity = ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity(
        tmp_path.stat().st_uid, tmp_path.stat().st_gid)
    binding = issue_acquisition_authorization("repository-binding", request)
    human_evidence = object.__new__(ProtectedEvidenceHumanAuthorizationEvidence)
    object.__setattr__(human_evidence, "authorization_id", binding.authorization_id)
    object.__setattr__(human_evidence, "acquisition_request_id", binding.acquisition_request_id)
    validation = object.__new__(ProtectedEvidenceHumanAuthorizationValidation)
    object.__setattr__(validation, "authorization_id", binding.authorization_id)
    object.__setattr__(validation, "acquisition_request_id", binding.acquisition_request_id)
    object.__setattr__(validation, "production_authority", False)
    assert validation.production_authority is False

    capability_request = object.__new__(ProtectedEvidenceAcquisitionRequest)
    for name in (
        "acquisition_request_id", "fixed_source_slot_identity",
        "concrete_source_location_identity", "leaf_basename",
        "concrete_parent_path", "concrete_leaf_path",
        "_repository_composed_concrete_leaf_path",
    ):
        object.__setattr__(capability_request, name, getattr(request, name))
    capability = object.__new__(ProtectedEvidenceAcquisitionInvocationCapability)
    object.__setattr__(capability, "_request", capability_request)
    object.__setattr__(
        capability, "_state",
        ProtectedEvidenceAcquisitionInvocationCapabilityState.AVAILABLE)
    object.__setattr__(capability, "_lock", Lock())
    trusted = object.__new__(TrustedOwnershipExpectation)
    object.__setattr__(trusted, "expected_uid", identity.uid)
    object.__setattr__(trusted, "expected_gid", identity.gid)
    return request, capability, trusted


def forbid_filesystem_io(monkeypatch):
    for name in ("open", "stat", "fstat", "read"):
        monkeypatch.setattr(
            os, name,
            lambda *args, _name=name, **kwargs: pytest.fail(
                f"os.{_name} occurred"),
        )


def test_capability_is_opaque_process_local_and_not_reconstructible(tmp_path):
    _, capability, _ = setup_values(tmp_path)
    with pytest.raises(TypeError):
        ProtectedEvidenceAcquisitionInvocationCapability()
    with pytest.raises(TypeError):
        copy.copy(capability)
    with pytest.raises(TypeError):
        copy.deepcopy(capability)
    with pytest.raises(TypeError):
        pickle.dumps(capability)
    with pytest.raises(TypeError):
        hash(capability)


def test_accepted_modes_are_exactly_0000_0200_0400_0600():
    assert [mode for mode in range(0o1000) if _leaf_mode_accepted(mode)] == [
        0o000, 0o200, 0o400, 0o600]


def test_content_size_policy_constants_remain_exact():
    assert MAXIMUM_SUCCESS_CONTENT_BYTES == 1_048_576
    assert MAXIMUM_BOUNDED_READ_BYTES == MAXIMUM_SUCCESS_CONTENT_BYTES + 1


@pytest.mark.parametrize(
    "boundary",
    [MacProtectedEvidenceContentAcquisitionMechanism,
     MariaDBContinuityProtectedEvidenceContentAcquisitionAdapter],
)
def test_forged_capability_cannot_unlock_filesystem_io(
        tmp_path, monkeypatch, boundary):
    request, capability, identity = setup_values(tmp_path)
    forbid_filesystem_io(monkeypatch)
    with pytest.raises(
            ProtectedEvidenceContentAcquisitionError,
            match=Code.INVALID_REQUEST.value):
        boundary().acquire(request, capability, identity)
    assert capability._state is (
        ProtectedEvidenceAcquisitionInvocationCapabilityState.AVAILABLE)


def test_caller_values_cannot_select_filesystem_access(tmp_path, monkeypatch):
    request, capability, identity = setup_values(tmp_path)
    object.__setattr__(request, "concrete_parent_path", "/tmp/attacker")
    object.__setattr__(request, "concrete_leaf_path", "/tmp/attacker/auth-plugin.evidence")
    object.__setattr__(
        request, "_repository_composed_concrete_leaf_path",
        "/tmp/attacker/auth-plugin.evidence")
    forged_identity = object.__new__(TrustedOwnershipExpectation)
    object.__setattr__(forged_identity, "expected_uid", identity.expected_uid)
    object.__setattr__(forged_identity, "expected_gid", identity.expected_gid)
    forbid_filesystem_io(monkeypatch)
    with pytest.raises(
            ProtectedEvidenceContentAcquisitionError,
            match=Code.INVALID_REQUEST.value):
        MacProtectedEvidenceContentAcquisitionMechanism().acquire(
            request, capability, forged_identity)


def test_production_acquisition_composition_unavailable_pre_io(
        tmp_path, monkeypatch):
    request, capability, identity = setup_values(tmp_path)
    forbid_filesystem_io(monkeypatch)
    with pytest.raises(
            ProtectedEvidenceContentAcquisitionError,
            match=Code.INVALID_REQUEST.value):
        MariaDBContinuityProtectedEvidenceContentAcquisitionAdapter().acquire(
            request, capability, identity)
    assert PRODUCTION_ACQUISITION_AVAILABLE is False


def test_production_adapter_exposes_no_caller_selectable_synthetic_trust():
    signature = inspect.signature(
        MariaDBContinuityProtectedEvidenceContentAcquisitionAdapter)
    assert "_synthetic_parent_path" not in signature.parameters
    assert "_synthetic_uid" not in signature.parameters
    assert "_synthetic_gid" not in signature.parameters
    assert not hasattr(
        MariaDBContinuityProtectedEvidenceContentAcquisitionAdapter,
        "for_isolated_test",
    )
