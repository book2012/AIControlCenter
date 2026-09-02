from __future__ import annotations

from copy import deepcopy
import hashlib
import inspect

import pytest

import core.governance.control_plane.application.wu09_authorization_intake as intake_module
from core.governance.control_plane.application.wu09_authorization_intake import (
    WU09AuthorizationIntakeError,
    intake_wu09_trusted_production_authorization,
)
from core.governance.control_plane.application.wu09_image_preload_coordinator import (
    WU09_PRELOAD_ACTION_TYPE,
    WU09_PRELOAD_TARGET,
    wu09_preload_plan_digest,
)
from core.governance.control_plane.domain.identity import GovernanceIdentity
from core.governance.control_plane.trust.canonical import canonicalize
from core.governance.control_plane.trust.intake import _intake_trusted_authorization
from core.governance.control_plane.trust.models import VerificationError
from core.governance.control_plane.trust.operator_identity import ObservedMacOperator
from tests.governance.control_plane.trust.fixtures.factory import NOW, material


class Observer:
    def observe(self):
        return ObservedMacOperator(
            501,
            20,
            "operator",
            "/Users/operator",
            GovernanceIdentity("operator", "MAC_LOCAL_OPERATOR_V1"),
        )


def exact_protected():
    _, protected, registry, encode = material()
    value = deepcopy(protected)
    request = value["authorization_request"]
    decision = value["authorization_decision"]
    receipt = value["authorization_receipt"]
    line = value["mutation_budget"]["line_items"][0]
    execution = value["execution_intent"]
    request.update(
        operation_type=WU09_PRELOAD_ACTION_TYPE,
        target=WU09_PRELOAD_TARGET,
        environment="PRODUCTION",
        requested_scope=[WU09_PRELOAD_ACTION_TYPE],
    )
    decision["approved_scope"] = [WU09_PRELOAD_ACTION_TYPE]
    receipt["approved_scope"] = [WU09_PRELOAD_ACTION_TYPE]
    line["action_type"] = WU09_PRELOAD_ACTION_TYPE
    execution.update(
        action_type=WU09_PRELOAD_ACTION_TYPE,
        target=WU09_PRELOAD_TARGET,
        plan_digest=wu09_preload_plan_digest(),
    )
    value.update(
        action_type=WU09_PRELOAD_ACTION_TYPE,
        target=WU09_PRELOAD_TARGET,
        plan_digest=wu09_preload_plan_digest(),
        approved_scope=[WU09_PRELOAD_ACTION_TYPE],
    )
    return value, registry, encode


def trusted_facts(protected=None):
    exact, registry, encode = exact_protected()
    raw, registry_raw = encode(protected or exact, registry)
    return _intake_trusted_authorization(
        raw,
        registry_reader=lambda: registry_raw,
        clock=lambda: NOW,
        operator_observer=Observer(),
    )


def invoke_with(protected, monkeypatch):
    facts = trusted_facts(protected)
    monkeypatch.setattr(intake_module, "intake_trusted_authorization", lambda raw: facts)
    return intake_wu09_trusted_production_authorization(b"signed-envelope")


def test_valid_exact_trusted_intake_is_validation_only(monkeypatch):
    result = invoke_with(exact_protected()[0], monkeypatch)
    assert result.purpose == WU09_PRELOAD_ACTION_TYPE
    assert result.action_type == WU09_PRELOAD_ACTION_TYPE
    assert result.target == WU09_PRELOAD_TARGET
    assert result.allowed_invocation_count == 1
    assert not any(
        (
            result.execution_authorized,
            result.retry_authorized,
            result.rollback_authorized,
            result.ubuntu_authorized,
        )
    )
    assert not hasattr(result, "consume_once") and not hasattr(result, "invoke_once")


def test_public_intake_accepts_only_raw_envelope():
    assert tuple(inspect.signature(intake_wu09_trusted_production_authorization).parameters) == (
        "raw_envelope",
    )


def test_unknown_or_untrusted_issuer_rejected_by_sec02(monkeypatch):
    def reject(_raw):
        raise VerificationError("unknown key")

    monkeypatch.setattr(intake_module, "intake_trusted_authorization", reject)
    with pytest.raises(VerificationError, match="unknown key"):
        intake_wu09_trusted_production_authorization(b"untrusted")


def test_non_human_registry_issuer_rejected_by_sec02():
    protected, registry, encode = exact_protected()
    registry = deepcopy(registry)
    registry["issuers"][0]["issuer_type"] = "INFRASTRUCTURE_WORKER"
    body = {key: value for key, value in registry.items() if key != "registry_digest"}
    registry["registry_digest"] = "sha256:" + hashlib.sha256(canonicalize(body)).hexdigest()
    raw, registry_raw = encode(protected, registry)
    with pytest.raises(VerificationError, match="trusted human authority"):
        _intake_trusted_authorization(
            raw,
            registry_reader=lambda: registry_raw,
            clock=lambda: NOW,
            operator_observer=Observer(),
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (lambda p: p["authorization_request"].update(environment="STAGING"), "environment"),
        (
            lambda p: (
                p["authorization_request"].update(target="SHOPPING_RUNTIME"),
                p["execution_intent"].update(target="SHOPPING_RUNTIME"),
                p.update(target="SHOPPING_RUNTIME"),
            ),
            "target",
        ),
    ),
)
def test_wrong_environment_or_target_rejected(mutation, message, monkeypatch):
    protected = exact_protected()[0]
    mutation(protected)
    with pytest.raises(WU09AuthorizationIntakeError, match=message):
        invoke_with(protected, monkeypatch)


def test_wrong_purpose_and_action_rejected(monkeypatch):
    protected = exact_protected()[0]
    protected["authorization_request"]["operation_type"] = "SHOPPING_RUNTIME:DEPLOY"
    protected["authorization_request"]["requested_scope"] = ["SHOPPING_RUNTIME:DEPLOY"]
    protected["authorization_decision"]["approved_scope"] = ["SHOPPING_RUNTIME:DEPLOY"]
    protected["authorization_receipt"]["approved_scope"] = ["SHOPPING_RUNTIME:DEPLOY"]
    protected["mutation_budget"]["line_items"][0]["action_type"] = "SHOPPING_RUNTIME:DEPLOY"
    protected["execution_intent"]["action_type"] = "SHOPPING_RUNTIME:DEPLOY"
    protected["action_type"] = "SHOPPING_RUNTIME:DEPLOY"
    protected["approved_scope"] = ["SHOPPING_RUNTIME:DEPLOY"]
    with pytest.raises(WU09AuthorizationIntakeError):
        invoke_with(protected, monkeypatch)


def test_scope_widening_rejected_by_sec02_before_wu09_return(monkeypatch):
    protected = exact_protected()[0]
    widened = [WU09_PRELOAD_ACTION_TYPE, "SHOPPING_RUNTIME:DEPLOY"]
    protected["authorization_request"]["requested_scope"] = widened
    protected["authorization_decision"]["approved_scope"] = widened
    protected["authorization_receipt"]["approved_scope"] = widened
    protected["approved_scope"] = widened
    with pytest.raises((WU09AuthorizationIntakeError, ValueError)):
        invoke_with(protected, monkeypatch)


def test_wrong_artifact_identity_rejected(monkeypatch):
    protected = exact_protected()[0]
    protected["execution_intent"]["plan_digest"] = "sha256:wrong-image"
    protected["plan_digest"] = "sha256:wrong-image"
    with pytest.raises(WU09AuthorizationIntakeError, match="execution intent"):
        invoke_with(protected, monkeypatch)


def test_mutation_budget_widening_rejected_by_generic_intake():
    protected = exact_protected()[0]
    line = protected["mutation_budget"]["line_items"][0]
    line.update(allowed_count=2, remaining_count=2)
    protected["mutation_budget"]["remaining_count"] = 2
    protected["allowed_invocation_count"] = 2
    with pytest.raises(ValueError):
        trusted_facts(protected)


def test_reused_or_consumed_authority_rejected_by_generic_intake():
    protected = exact_protected()[0]
    protected["authorization_receipt"]["state"] = "CONSUMED"
    with pytest.raises(ValueError):
        trusted_facts(protected)


def test_no_execution_retry_rollback_ubuntu_or_secret_surface():
    source = inspect.getsource(intake_module).lower()
    assert "controlledexecutionport" not in source
    assert "consume_once" not in source and "invoke_once" not in source
    assert "docker" not in source and "secret" not in source
