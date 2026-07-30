from __future__ import annotations

from dataclasses import replace

import pytest

from core.deployment.controlled_activation_validation import (
    ControlledActivationInvariant,
    ControlledActivationReadinessDecision,
    ControlledActivationValidationConfig,
    ControlledActivationValidationError,
    ControlledActivationValidator,
)


def _validate(config: ControlledActivationValidationConfig | None = None):
    return ControlledActivationValidator().validate(
        config or ControlledActivationValidationConfig()
    )


def test_complete_valid_m3_state_is_accepted_and_bound_exactly():
    result, report = _validate()
    assert result.decision is (
        ControlledActivationReadinessDecision
        .READY_FOR_SEPARATELY_AUTHORIZED_CONTROLLED_ACTIVATION
    )
    assert report.task == "M3-A4C"
    assert report.branch == "feature/deployment-package"
    assert report.commit == "0f23abdf362965c09db5f4f35483cbff47853643"
    assert report.bootstrap_evidence_status == "VALID"
    assert report.recovery_validation_status == "VALID"
    assert report.audit_health == report.replay_health == "HEALTHY"
    assert report.audit_event_count == report.replay_event_count == 0
    assert report.consumed_permit_status == "CONSUMED_SINGLE_USE"
    assert report.single_claim_status == "EXACTLY_ONE_ATOMIC_CLAIM"
    assert report.managed_filesystem_readiness == "READY"


def test_closeout_report_is_deterministic_canonical_json():
    first = _validate()[1]
    second = _validate()[1]
    assert first == second
    assert first.canonical_json() == second.canonical_json()
    assert first.canonical_json().endswith("}")
    assert first.report_digest.startswith("sha256:")


def test_control_plane_mac_and_ubuntu_invariants_are_explicit():
    result, report = _validate()
    assert set(result.invariants) == set(ControlledActivationInvariant)
    assert ControlledActivationInvariant.CONTROL_PLANE_OWNERSHIP in result.invariants
    assert ControlledActivationInvariant.MAC_BRAIN_ROLE in result.invariants
    assert ControlledActivationInvariant.UBUNTU_EXCLUSION in result.invariants
    assert report.ubuntu_participation is False


def test_future_activation_contract_is_requirement_only_and_default_deny():
    contract = _validate()[1].future_activation_contract
    required = {
        name: value for name, value in contract.__dict__.items()
        if name.endswith("_required")
    } if hasattr(contract, "__dict__") else {
        name: getattr(contract, name)
        for name in contract.__dataclass_fields__
        if name.endswith("_required")
    }
    assert required and all(required.values())
    assert contract.capabilities_default_false is True
    assert contract.ubuntu_participation is False
    assert contract.production_authorized is False


@pytest.mark.parametrize(("field", "value", "code"), [
    ("branch", "main", "BRANCH_MISMATCH"),
    ("commit", "0" * 40, "COMMIT_MISMATCH"),
    ("bootstrap_commit", "0" * 40, "BOOTSTRAP_COMMIT_MISMATCH"),
    ("control_plane_owner", "external", "CONTROL_PLANE_OWNER_INVALID"),
    ("governance_owner", "n8n", "GOVERNANCE_OWNER_INVALID"),
    ("authorization_owner", "Ubuntu", "AUTHORIZATION_OWNER_INVALID"),
    ("permit_owner", "external", "PERMIT_OWNER_INVALID"),
    ("claim_owner", "external", "CLAIM_OWNER_INVALID"),
    ("evidence_owner", "external", "EVIDENCE_OWNER_INVALID"),
    ("deployment_controller", "n8n", "EXTERNAL_DEPLOYMENT_CONTROL"),
    ("host_role", "LINUX_HOST", "MAC_CONTROL_PLANE_ROLE_INVALID"),
    ("wordpress_business_logic_present", True, "WORDPRESS_LOGIC_PROHIBITED"),
    ("woocommerce_business_logic_present", True, "WOOCOMMERCE_LOGIC_PROHIBITED"),
    ("n8n_control_present", True, "N8N_CONTROL_PROHIBITED"),
    ("external_component_control_present", True, "EXTERNAL_DEPLOYMENT_CONTROL"),
    ("ubuntu_participation", True, "UBUNTU_PARTICIPATION_PROHIBITED"),
    ("ubuntu_authorization_scope", True, "UBUNTU_AUTHORIZATION_SCOPE_PROHIBITED"),
    ("ubuntu_state_ownership", True, "UBUNTU_STATE_OWNERSHIP_PROHIBITED"),
    ("linux_live_host", True, "LINUX_LIVE_HOST_PROHIBITED"),
    ("root_operator", True, "ROOT_OPERATOR_PROHIBITED"),
    ("environment_only_activation", True, "ENVIRONMENT_ONLY_ACTIVATION_PROHIBITED"),
    ("authorization_present", False, "AUTHORIZATION_MISSING"),
    ("authorization_valid", False, "AUTHORIZATION_INVALID"),
    ("authorization_expired", True, "AUTHORIZATION_EXPIRED"),
    ("permit_present", False, "PERMIT_MISSING"),
    ("permit_expired", True, "PERMIT_EXPIRED"),
    ("permit_consumed", False, "PERMIT_UNCONSUMED"),
    ("permit_reused", True, "PERMIT_REUSED"),
    ("claim_present", False, "CLAIM_MISSING"),
    ("claim_count", 0, "EXACTLY_ONE_CLAIM_REQUIRED"),
    ("claim_count", 2, "EXACTLY_ONE_CLAIM_REQUIRED"),
    ("evidence_chain_valid", False, "EVIDENCE_CHAIN_INVALID"),
    ("bootstrap_evidence_present", False, "BOOTSTRAP_EVIDENCE_MISSING"),
    ("bootstrap_evidence_valid", False, "BOOTSTRAP_EVIDENCE_INVALID"),
    ("recovery_report_present", False, "M3_A4B3_REPORT_MISSING"),
    ("recovery_report_valid", False, "M3_A4B3_REPORT_INVALID"),
    ("recovery_validation_passed", False, "RECOVERY_VALIDATION_FAILED"),
    ("audit_status", "UNHEALTHY", "AUDIT_UNHEALTHY"),
    ("audit_event_count", 1, "AUDIT_EVENT_COUNT_INVALID"),
    ("replay_status", "UNHEALTHY", "REPLAY_UNHEALTHY"),
    ("replay_event_count", 1, "REPLAY_EVENT_COUNT_INVALID"),
    ("managed_filesystem_ready", False, "MANAGED_FILESYSTEM_NOT_READY"),
    ("operational_root_safe", False, "OPERATIONAL_ROOT_UNSAFE"),
    ("operational_root_arbitrary", True, "ARBITRARY_OPERATIONAL_ROOT"),
    ("writers_authorized", True, "WRITERS_AUTHORIZATION_PROHIBITED"),
    ("monitoring_authorized", True, "MONITORING_AUTHORIZATION_PROHIBITED"),
    ("external_dispatch_authorized", True, "DISPATCH_AUTHORIZATION_PROHIBITED"),
    ("production_authorized", True, "PRODUCTION_AUTHORIZATION_PROHIBITED"),
    ("writers_active", True, "WRITERS_ACTIVE"),
    ("monitoring_active", True, "MONITORING_ACTIVE"),
    ("dispatch_active", True, "DISPATCH_ACTIVE"),
    ("validation_runner_write_requested", True, "VALIDATION_RUNNER_WRITE_PROHIBITED"),
    ("live_test_adapter_supplied", True, "LIVE_TEST_ADAPTER_PROHIBITED"),
    ("api_write_route_requested", True, "API_WRITE_ROUTE_PROHIBITED"),
])
def test_every_required_default_deny_scenario(field, value, code):
    config = replace(ControlledActivationValidationConfig(), **{field: value})
    with pytest.raises(ControlledActivationValidationError) as caught:
        _validate(config)
    assert caught.value.code == code


def test_validation_has_no_real_activation_side_effects():
    config = ControlledActivationValidationConfig()
    before = config
    _, report = _validate(config)
    assert config == before
    assert report.writers_active is False
    assert report.monitoring_active is False
    assert report.dispatch_active is False
    assert report.production_authorization is False
    assert report.future_authorization_required is True
    assert report.blockers == ()
    assert report.risks == ("427_EXISTING_DEPRECATION_WARNINGS",)
