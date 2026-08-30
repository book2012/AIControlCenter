from dataclasses import FrozenInstanceError, fields
import inspect

import pytest

from core.governance.control_plane.trust.governance_privileged_helper import (
    FixedPrivilegedHelperProtocol, NativeReadiness, PeerSigningPolicy,
    PrivilegedHelperOperation, SMAppServicePackageContract,
)


def test_xpc_protocol_has_exactly_two_zero_argument_semantic_operations():
    public = [name for name in FixedPrivilegedHelperProtocol.__dict__ if not name.startswith("_")]
    assert public == [
        "provision_pre_bootstrap_remediation_journal",
        "restrict_governance_directory_mode_0755_to_0700",
    ]
    for name in public:
        method = getattr(FixedPrivilegedHelperProtocol, name)
        assert list(inspect.signature(method).parameters) == ["self"]
    assert len(PrivilegedHelperOperation) == 2


def test_helper_contract_has_no_generic_mutation_or_caller_selected_fields():
    forbidden = {
        "path", "target", "mode", "uid", "gid", "owner", "group", "command",
        "argv", "environment", "shell", "executable", "recursive", "retry",
        "rollback", "operation",
    }
    for model in (PeerSigningPolicy, SMAppServicePackageContract):
        assert forbidden.isdisjoint(field.name for field in fields(model))


def test_peer_signing_requirements_are_mandatory_and_fail_closed():
    assert PeerSigningPolicy(None, None).readiness is NativeReadiness.NOT_READY
    assert PeerSigningPolicy("client", None).readiness is NativeReadiness.NOT_READY
    policy = PeerSigningPolicy("client requirement", "helper requirement")
    assert policy.evaluate(client_matches=False, helper_matches=True) is NativeReadiness.NOT_READY
    assert policy.evaluate(client_matches=True, helper_matches=False) is NativeReadiness.NOT_READY
    assert policy.evaluate(client_matches=True, helper_matches=True) is NativeReadiness.NOT_READY


def test_package_contract_is_macos_13_bundled_daemon_but_not_operational():
    contract = SMAppServicePackageContract()
    assert contract.minimum_macos_major == 13
    assert contract.bundled_launch_daemon is True
    assert contract.registration_permitted is False
    assert contract.readiness is NativeReadiness.NOT_READY


def test_models_are_immutable_and_external_form_is_unrepresentable():
    policy = PeerSigningPolicy(None, None)
    with pytest.raises(FrozenInstanceError):
        policy.client_requirement = "forged"
    forbidden = {"external_form", "authorization_external_form", "bytes", "data", "token"}
    for model in (PeerSigningPolicy, SMAppServicePackageContract):
        assert forbidden.isdisjoint(field.name for field in fields(model))
