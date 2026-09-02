from __future__ import annotations

import ast
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import core.governance.control_plane.application.wu09_image_preload_coordinator as coordinator_module
from core.governance.control_plane.application.orchestration_policy import (
    GovernanceOrchestrationDecision,
    OrchestrationDisposition,
)
from core.governance.control_plane.application.wu09_image_preload_coordinator import (
    WU09ImagePreloadCoordinator,
    WU09PreloadDisposition,
    WU09PreloadLifecycle,
    WU09_PRELOAD_ACTION_TYPE,
    WU09_PRELOAD_TARGET,
    wu09_preload_plan_digest,
)
from core.governance.control_plane.domain import (
    AuthorizationDecision,
    AuthorizationState,
    ConsumptionTransactionStatus,
    ExecutionStatus,
    GovernanceAuthorization,
    GovernanceAuthorizationConsumptionReceipt,
    GovernanceAuthorizationDecision,
    GovernanceAuthorizationRequest,
    GovernanceExecutionReceipt,
    GovernanceExecutionRequest,
    GovernanceIdentity,
    GovernanceMutationBudget,
    MutationBudgetLineItem,
    PostconditionDecision,
    consume_mutation_budget,
    transition_authorization,
)
from core.governance.control_plane.ports import AuthorizationConsumptionResult
from ops.macos.shopping.wu09_image_preload import (
    DOCKER_CONTEXT,
    EXACT_IMAGE,
    WU09ExactImagePreloadExecution,
    WU09PreloadPostconditionValidator,
    WU09PreloadPostconditions,
    WU09PreloadPreconditionObserver,
    WU09PreloadPreconditions,
    build_precondition_snapshot,
    ReadOnlyCommandResult,
    WU09ProductionReadOnlyObservation,
)
import ops.macos.shopping.wu09_image_preload_composition as composition_module
from ops.macos.shopping.wu09_image_preload_composition import (
    WU09ProductionComposition,
    WU09ProductionCompositionInput,
    compose_wu09_production_image_preload,
)


NOW = datetime(2026, 8, 27, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[1]


def good_preconditions(**changes: object) -> WU09PreloadPreconditions:
    value = WU09PreloadPreconditions(
        "Darwin", True, True, DOCKER_CONTEXT, True, False, False, True,
        True, True, True, True, False,
    )
    return replace(value, **changes)


def authorization_request(action: str = WU09_PRELOAD_ACTION_TYPE):
    return GovernanceAuthorizationRequest(
        "1.0", "request-1", "lifecycle-1",
        GovernanceIdentity(identity_id="requester", identity_type="HUMAN"),
        "WU09_PINNED_IMAGE_PRELOAD", WU09_PRELOAD_TARGET, "PRODUCTION",
        "explicit exact image preload approval", (action,), "budget-1", NOW,
    )


def lifecycle(
    *, action: str = WU09_PRELOAD_ACTION_TYPE, target: str = WU09_PRELOAD_TARGET
) -> WU09PreloadLifecycle:
    auth_request = authorization_request(action)
    expected = build_precondition_snapshot(auth_request, good_preconditions(), collected_at=NOW)
    decision = GovernanceAuthorizationDecision(
        "1.0", "decision-1", auth_request.request_id,
        GovernanceIdentity(identity_id="approver", identity_type="HUMAN"),
        AuthorizationDecision.APPROVED,
        ("EXPLICIT_APPROVAL",), NOW, NOW + timedelta(hours=1), (action,),
        "budget-1", expected.snapshot_digest,
    )
    authority = transition_authorization(
        GovernanceAuthorization(auth_request), AuthorizationState.AUTHORIZED, "APPROVED", NOW,
        decision=decision, authorization_id="authorization-1",
    ).authorization
    budget = GovernanceMutationBudget(
        "1.0", "budget-1", "authorization-1", (MutationBudgetLineItem(action, 1),)
    )
    request = GovernanceExecutionRequest(
        "1.0", "execution-1", "lifecycle-1", "authorization-1", "claim-1",
        "budget-1", action, target, wu09_preload_plan_digest(), NOW,
    )
    return WU09PreloadLifecycle(authority, budget, request, expected)


def test_governance_identities_serialize_with_explicit_wu09_bindings():
    request = authorization_request()
    snapshot = build_precondition_snapshot(request, good_preconditions(), collected_at=NOW)
    decision = lifecycle().authorization.decision

    request_payload = request.to_dict()
    assert request_payload["requester"]["identity_id"] == "requester"
    assert request_payload["requester"]["identity_type"] == "HUMAN"

    decision_payload = decision.to_dict()
    assert decision_payload["approver"]["identity_id"] == "approver"
    assert decision_payload["approver"]["identity_type"] == "HUMAN"

    snapshot_payload = snapshot.to_dict()
    assert snapshot_payload["collector_identities"][0]["identity_id"] == "MAC_MINI_M4"
    assert snapshot_payload["collector_identities"][0]["identity_type"] == "CONTROL_PLANE"
    assert snapshot_payload["target_identity"]["identity_id"] == "MAC_MINI_M4"
    assert snapshot_payload["target_identity"]["identity_type"] == "CONTROL_PLANE"


class Observer:
    def __init__(self, snapshots):
        self.snapshots = list(snapshots)
        self.count = 0

    def observe_preconditions(self, request):
        value = self.snapshots[min(self.count, len(self.snapshots) - 1)]
        self.count += 1
        return value


class Consumer:
    def __init__(self):
        self.count = 0

    def consume_once(self, command):
        self.count += 1
        consumed = transition_authorization(
            command.authorization, AuthorizationState.CONSUMED, "ATOMIC_CONSUMPTION", NOW
        ).authorization
        receipt = GovernanceAuthorizationConsumptionReceipt(
            "1.0", command.execution_request.claim_id, command.execution_request.lifecycle_id,
            command.execution_request.authorization_id, command.execution_request.mutation_budget_id,
            command.execution_request.execution_request_id, NOW,
            ConsumptionTransactionStatus.COMMITTED,
        )
        return AuthorizationConsumptionResult(
            consumed, consume_mutation_budget(command.mutation_budget), receipt,
            command.execution_request,
        )


class Execution:
    def __init__(self, status=ExecutionStatus.COMPLETED):
        self.status = status
        self.count = 0
        self.consumer = None

    def invoke_once(self, request):
        assert self.consumer is None or self.consumer.count == 1
        self.count += 1
        return GovernanceExecutionReceipt(
            "1.0", "receipt-1", request.lifecycle_id, request.execution_request_id,
            request.authorization_id, request.claim_id, request.mutation_budget_id,
            request.action_type, self.status, 1,
            int(self.status is ExecutionStatus.COMPLETED),
            int(self.status is ExecutionStatus.UNCERTAIN), NOW, NOW, "sha256:result",
            ("INVOCATION_COMPLETE",),
        )


def assembled(value: WU09PreloadLifecycle, *, snapshots=None, execution=None):
    consumer = Consumer()
    observer = Observer(snapshots or (value.expected_preconditions, value.expected_preconditions))
    execution = execution or Execution()
    execution.consumer = consumer
    validator = WU09PreloadPostconditionValidator(
        lambda: WU09PreloadPostconditions(
            DOCKER_CONTEXT, EXACT_IMAGE, True, False, False
        ), clock=lambda: NOW,
    )
    coordinator = WU09ImagePreloadCoordinator(
        authorization_consumption=consumer,
        precondition_observation=observer,
        controlled_execution=execution,
        postcondition_validation=validator,
    )
    return coordinator, consumer, observer, execution


def test_exact_action_target_and_plan_are_accepted_once_with_closeout():
    value = lifecycle()
    coordinator, consumer, observer, execution = assembled(value)
    result = coordinator.coordinate(value)
    assert result.disposition is WU09PreloadDisposition.CLOSEOUT
    assert result.postcondition_decision is PostconditionDecision.PASS
    assert (consumer.count, observer.count, execution.count) == (1, 2, 1)


@pytest.mark.parametrize(
    ("action", "target"),
    (("SHOPPING_MARIADB_LOOPBACK_IMAGE:DEPLOY", WU09_PRELOAD_TARGET),
     (WU09_PRELOAD_ACTION_TYPE, "SHOPPING_MARIADB_LOOPBACK")),
)
def test_wrong_action_or_target_rejected_before_observation_consumption_invocation(action, target):
    value = lifecycle(action=action, target=target)
    coordinator, consumer, observer, execution = assembled(value)
    result = coordinator.coordinate(value)
    assert result.reason_codes == ("PRELOAD_REQUEST_BINDING_MISMATCH",)
    assert (consumer.count, observer.count, execution.count) == (0, 0, 0)


def test_exact_execution_uses_fixed_argv_and_prohibits_shell():
    calls = []

    def runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0)

    adapter = WU09ExactImagePreloadExecution(
        runner, platform_system=lambda: "Darwin", clock=lambda: NOW
    )
    receipt = adapter.invoke_once(lifecycle().execution_request)
    assert receipt.status is ExecutionStatus.COMPLETED
    assert calls == [
        (["docker", "--context", "colima-aicontrolcenter-commerce", "pull", EXACT_IMAGE],
         {"shell": False, "check": False, "capture_output": True, "text": False})
    ]


def test_execution_public_surface_accepts_no_argv_context_image_tag_or_digest():
    signature = inspect.signature(WU09ExactImagePreloadExecution.invoke_once)
    assert tuple(signature.parameters) == ("self", "request")
    public = {
        name for name, member in inspect.getmembers(WU09ExactImagePreloadExecution, inspect.isfunction)
        if not name.startswith("_")
    }
    assert public == {"invoke_once"}
    assert DOCKER_CONTEXT == "colima-aicontrolcenter-commerce"
    assert EXACT_IMAGE == "alpine/socat@sha256:cc2ab2488d6b39cbac670d18fdca5f87ea44fe630697a09d8558afb17f3269a1"


@pytest.mark.parametrize(
    ("outcome", "expected"),
    ((SimpleNamespace(returncode=19), ExecutionStatus.FAILED),
     (SimpleNamespace(), ExecutionStatus.UNCERTAIN)),
)
def test_nonzero_or_ambiguous_completion_has_no_retry(outcome, expected):
    calls = 0

    def runner(argv, **kwargs):
        nonlocal calls
        calls += 1
        return outcome

    receipt = WU09ExactImagePreloadExecution(
        runner, platform_system=lambda: "Darwin", clock=lambda: NOW
    ).invoke_once(lifecycle().execution_request)
    assert receipt.status is expected
    assert calls == 1


def test_runner_exception_maps_to_uncertain_after_exactly_one_attempt():
    calls = 0

    def runner(argv, **kwargs):
        nonlocal calls
        calls += 1
        raise OSError("ambiguous process completion")

    receipt = WU09ExactImagePreloadExecution(
        runner, platform_system=lambda: "Darwin", clock=lambda: NOW
    ).invoke_once(lifecycle().execution_request)
    assert receipt.status is ExecutionStatus.UNCERTAIN
    assert calls == 1


def test_darwin_gate_fails_closed_without_runner_invocation():
    calls = 0

    def runner(argv, **kwargs):
        nonlocal calls
        calls += 1

    receipt = WU09ExactImagePreloadExecution(
        runner, platform_system=lambda: "Linux", clock=lambda: NOW
    ).invoke_once(lifecycle().execution_request)
    assert receipt.status is ExecutionStatus.FAILED
    assert calls == 0


@pytest.mark.parametrize(
    "change",
    (
        {"platform_system": "Linux"}, {"git_clean": False},
        {"upstream_aligned": False}, {"docker_context": "default"},
        {"docker_context_reachable": False}, {"exact_image_present": True},
        {"adapter_container_present": True}, {"host_port_free": False},
        {"network_exists": False}, {"network_internal": False},
        {"database_container_running": False}, {"database_attached_to_network": False},
        {"wu09_deployment_active": True},
    ),
)
def test_observer_validates_every_frozen_precondition_fail_closed(change):
    observer = WU09PreloadPreconditionObserver(
        lambda: good_preconditions(**change), clock=lambda: NOW
    )
    with pytest.raises(ValueError):
        observer.observe_preconditions(authorization_request())


def test_preconsumption_drift_blocks_consumption_and_invocation():
    value = lifecycle()
    drift = replace(value.expected_preconditions, snapshot_digest="sha256:drift")
    coordinator, consumer, observer, execution = assembled(value, snapshots=(drift,))
    result = coordinator.coordinate(value)
    assert result.reason_codes == ("CURRENT_PRECONDITION_DRIFT",)
    assert (consumer.count, observer.count, execution.count) == (0, 1, 0)


def test_postconsumption_drift_permanently_consumes_and_blocks_invocation():
    value = lifecycle()
    drift = replace(value.expected_preconditions, snapshot_digest="sha256:drift")
    coordinator, consumer, observer, execution = assembled(
        value, snapshots=(value.expected_preconditions, drift)
    )
    result = coordinator.coordinate(value)
    assert result.reason_codes == ("CURRENT_PRECONDITION_DRIFT",)
    assert result.authorization_consumed is True
    assert (consumer.count, observer.count, execution.count) == (1, 2, 0)


def test_allow_single_invocation_is_required_after_consumption(monkeypatch):
    real_decide = coordinator_module.decide_next_disposition
    calls = 0

    def policy(context):
        nonlocal calls
        calls += 1
        if calls == 2:
            return GovernanceOrchestrationDecision(
                OrchestrationDisposition.STOP, ("SINGLE_INVOCATION_DENIED",)
            )
        return real_decide(context)

    monkeypatch.setattr(coordinator_module, "decide_next_disposition", policy)
    value = lifecycle()
    coordinator, consumer, observer, execution = assembled(value)
    result = coordinator.coordinate(value)
    assert result.reason_codes == ("SINGLE_INVOCATION_DENIED",)
    assert (consumer.count, observer.count, execution.count) == (1, 2, 0)


def test_completed_execution_requires_postcondition_and_presence_does_not_claim_deployment():
    value = lifecycle()
    consumer = Consumer()
    execution = Execution()
    post_facts = WU09PreloadPostconditions(DOCKER_CONTEXT, EXACT_IMAGE, True, False, False)
    validator = WU09PreloadPostconditionValidator(lambda: post_facts, clock=lambda: NOW)
    coordinator = WU09ImagePreloadCoordinator(
        authorization_consumption=consumer,
        precondition_observation=Observer((value.expected_preconditions,) * 2),
        controlled_execution=execution,
        postcondition_validation=validator,
    )
    result = coordinator.coordinate(value)
    assert result.postcondition_decision is PostconditionDecision.PASS
    assert result.wu09_deployment_authorized is False
    assert result.wu10_authorized is False and result.wu11_authorized is False


def postcondition_report(facts: WU09PreloadPostconditions):
    receipt = Execution().invoke_once(lifecycle().execution_request)
    return WU09PreloadPostconditionValidator(
        lambda: facts, clock=lambda: NOW
    ).validate_postconditions(receipt)


def test_pass_evidence_records_exact_observed_facts_without_granting_authority():
    report = postcondition_report(
        WU09PreloadPostconditions(DOCKER_CONTEXT, EXACT_IMAGE, True, False, False)
    )
    expected = json.loads(report.expected_state_reference)
    observed = json.loads(report.observed_state_reference)
    assert report.decision is PostconditionDecision.PASS
    assert observed == expected
    assert observed["docker_context"] == DOCKER_CONTEXT
    assert observed["exact_image"] == EXACT_IMAGE
    assert observed["exact_image_present"] is True
    assert observed["adapter_deployed"] is False
    assert observed["unrelated_runtime_mutation_claimed"] is False
    assert "authorized" not in report.observed_state_reference.lower()


@pytest.mark.parametrize(
    ("facts", "field", "actual"),
    (
        (WU09PreloadPostconditions(DOCKER_CONTEXT, EXACT_IMAGE, False, False, False),
         "exact_image_present", False),
        (WU09PreloadPostconditions(DOCKER_CONTEXT, EXACT_IMAGE, True, True, False),
         "adapter_deployed", True),
        (WU09PreloadPostconditions(DOCKER_CONTEXT, EXACT_IMAGE, True, False, True),
         "unrelated_runtime_mutation_claimed", True),
    ),
)
def test_fail_evidence_records_actual_observed_fact(facts, field, actual):
    report = postcondition_report(facts)
    expected = json.loads(report.expected_state_reference)
    observed = json.loads(report.observed_state_reference)
    assert report.decision is PostconditionDecision.FAIL
    assert observed[field] is actual
    assert observed != expected


@pytest.mark.parametrize(
    "facts",
    (
        WU09PreloadPostconditions(DOCKER_CONTEXT, EXACT_IMAGE, False, False, False),
        WU09PreloadPostconditions(DOCKER_CONTEXT, EXACT_IMAGE, True, True, False),
        WU09PreloadPostconditions(DOCKER_CONTEXT, EXACT_IMAGE, True, False, True),
    ),
)
def test_postcondition_fails_if_image_or_non_deployment_separation_not_proven(facts):
    receipt = Execution().invoke_once(lifecycle().execution_request)
    report = WU09PreloadPostconditionValidator(
        lambda: facts, clock=lambda: NOW
    ).validate_postconditions(receipt)
    assert report.decision is PostconditionDecision.FAIL


def test_no_generic_docker_or_ubuntu_execution_surface_is_introduced():
    paths = (
        ROOT / "core/governance/control_plane/application/wu09_image_preload_coordinator.py",
        ROOT / "ops/macos/shopping/wu09_image_preload.py",
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert "UbuntuWorkerClient" not in source
    assert "compose" not in source.lower()
    tree = ast.parse(paths[1].read_text(encoding="utf-8"))
    methods = {
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    assert "execute" not in methods and "run" not in methods


def _composition_dependencies(monkeypatch, value):
    counts = {"consume": 0, "coordinate": 0, "invoke": 0, "process": 0}
    trusted = SimpleNamespace(facts=SimpleNamespace(
        authorization=value.authorization,
        mutation_budget=value.mutation_budget,
        execution_request=value.execution_request,
        expected_operator=GovernanceIdentity("operator", "MAC_LOCAL_OPERATOR_V1"),
    ))
    observed = SimpleNamespace(
        uid=501, gid=20, passwd_home="/Users/operator",
        governance_identity=trusted.facts.expected_operator,
    )
    captured = {}

    class InertConsumer:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def consume_once(self, command):
            counts["consume"] += 1
            raise AssertionError("assembly consumed authorization")

    class InertObservation:
        def __init__(self, repository_root):
            captured["observation_root"] = repository_root

        def observe_preload_preconditions(self):
            counts["process"] += 1
            raise AssertionError("assembly observed runtime")

        def observe_preload_postconditions(self):
            counts["process"] += 1
            raise AssertionError("assembly observed runtime")

    class InertExecution:
        def invoke_once(self, request):
            counts["invoke"] += 1
            raise AssertionError("assembly invoked execution")

    monkeypatch.setattr(composition_module, "intake_wu09_trusted_production_authorization", lambda raw: trusted)
    monkeypatch.setattr(composition_module, "ProductionMacOperatorObserver", lambda: object())
    monkeypatch.setattr(composition_module, "observe_operator", lambda observer: observed)
    monkeypatch.setattr(composition_module, "SQLiteAuthorizationConsumptionAdapter", InertConsumer)
    monkeypatch.setattr(composition_module, "WU09ProductionReadOnlyObservation", InertObservation)
    monkeypatch.setattr(composition_module, "WU09ExactImagePreloadExecution", InertExecution)
    return counts, captured


def test_exact_trusted_facts_compose_without_consuming_deciding_or_invoking(monkeypatch):
    value = lifecycle()
    counts, captured = _composition_dependencies(monkeypatch, value)
    request = WU09ProductionCompositionInput(b"signed", value.expected_preconditions, ROOT)
    composed = compose_wu09_production_image_preload(request)
    assert type(composed) is WU09ProductionComposition
    assert counts == {"consume": 0, "coordinate": 0, "invoke": 0, "process": 0}
    assert captured == {"observation_root": ROOT}
    assert not hasattr(composed, "coordinate") and not hasattr(composed, "invoke_once")


def test_composition_snapshot_digest_mismatch_fails_before_adapter_assembly(monkeypatch):
    value = lifecycle()
    counts, captured = _composition_dependencies(monkeypatch, value)
    mismatch = replace(value.expected_preconditions, snapshot_digest="sha256:mismatch")
    with pytest.raises(ValueError, match="not exact and complete"):
        compose_wu09_production_image_preload(
            WU09ProductionCompositionInput(b"signed", mismatch, ROOT)
        )
    assert counts == {"consume": 0, "coordinate": 0, "invoke": 0, "process": 0}
    assert captured == {}


def test_matching_digest_cannot_override_tampered_expected_snapshot(monkeypatch):
    value = lifecycle()
    counts, captured = _composition_dependencies(monkeypatch, value)
    tampered = replace(
        value.expected_preconditions,
        runtime_identity_binding=value.expected_preconditions.git_state_binding,
    )
    with pytest.raises(ValueError, match="not exact and complete"):
        compose_wu09_production_image_preload(
            WU09ProductionCompositionInput(b"signed", tampered, ROOT)
        )
    assert counts == {"consume": 0, "coordinate": 0, "invoke": 0, "process": 0}
    assert captured == {}


def test_composition_has_no_caller_controlled_execution_parameters():
    assert tuple(inspect.signature(compose_wu09_production_image_preload).parameters) == ("request",)
    assert tuple(WU09ProductionCompositionInput.__dataclass_fields__) == (
        "raw_authorization_envelope", "expected_preconditions", "repository_root"
    )
    forbidden = {"argv", "image", "digest", "context", "target"}
    assert forbidden.isdisjoint(WU09ProductionCompositionInput.__dataclass_fields__)
    with pytest.raises(TypeError):
        WU09ProductionComposition()


def test_read_only_observation_uses_only_fixed_commands_and_exact_parsing():
    calls = []
    outputs = iter((
        "", "0\t0\n", '[{"Name":"colima-aicontrolcenter-commerce"}]', "",
        "", '[{"Name":"ai-shopping-internal","Internal":true}]',
        '[{"State":{"Running":true},"NetworkSettings":{"Networks":{"ai-shopping-internal":{}}}}]',
    ))

    def runner(argv, *, cwd=None):
        calls.append((tuple(argv), cwd))
        return ReadOnlyCommandResult(0, next(outputs))

    observation = WU09ProductionReadOnlyObservation(
        ROOT, _runner=runner, _platform_system=lambda: "Darwin", _port_available=lambda: True
    ).observe_preload_preconditions()
    assert observation == good_preconditions()
    assert len(calls) == 7
    assert all("pull" not in argv and "run" not in argv and "create" not in argv for argv, _ in calls)


@pytest.mark.parametrize(
    "bad_result",
    (ReadOnlyCommandResult(1, ""), ReadOnlyCommandResult(0, "{"), ReadOnlyCommandResult(0, "[]")),
)
def test_read_only_observation_fails_closed_on_nonzero_malformed_or_missing(bad_result):
    def runner(argv, *, cwd=None):
        if argv[:3] == ("docker", "context", "inspect"):
            return bad_result
        return ReadOnlyCommandResult(0, "")

    observer = WU09ProductionReadOnlyObservation(
        ROOT, _runner=runner, _platform_system=lambda: "Darwin", _port_available=lambda: True
    )
    with pytest.raises(RuntimeError):
        observer.observe_preload_preconditions()
