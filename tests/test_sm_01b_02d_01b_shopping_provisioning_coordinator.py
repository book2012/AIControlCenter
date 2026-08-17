from __future__ import annotations

import ast
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import inspect
import json
from pathlib import Path

import pytest

import core.governance.control_plane.application.shopping_provisioning_coordinator as module
from core.governance.control_plane.application.orchestration_policy import (
    GovernanceOrchestrationDecision,
    OrchestrationDisposition,
)
from core.governance.control_plane.application.shopping_provisioning_coordinator import (
    CoordinatorDisposition,
    PROVISIONING_ACTIONS,
    SHOPPING_SECRET_PROVISIONING,
    ShoppingProvisioningGovernanceCoordinator,
    ShoppingProvisioningLifecycle,
    ShoppingProvisioningResult,
    provisioning_plan_digest,
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
    GovernancePostconditionReport,
    GovernancePreconditionSnapshot,
    MutationBudgetLineItem,
    PostconditionDecision,
    PreconditionBinding,
    consume_mutation_budget,
    transition_authorization,
)
from core.governance.control_plane.ports import AuthorizationConsumptionResult
from core.secrets.provisioning import Readiness, plan_for

NOW = datetime(2026, 8, 17, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[1]
COORDINATOR_PATH = (
    ROOT / "core/governance/control_plane/application/shopping_provisioning_coordinator.py"
)


def plan(readiness: Readiness, action: str = PROVISIONING_ACTIONS[0]):
    return plan_for(
        schema_version="1.0", backend_definition_id="shopping-secret-backend",
        action=action, readiness=readiness,
        missing_prerequisites=() if readiness is Readiness.READY else ("NOT_READY",),
    )


def snapshot(*, digest: str = "sha256:snapshot", snapshot_id: str = "snapshot-1"):
    identity = GovernanceIdentity("CONTROL_PLANE", "mac-mini")
    return GovernancePreconditionSnapshot(
        "1.0", snapshot_id, "lifecycle-1", "request-1", NOW,
        (identity,), identity, PreconditionBinding("git", "baseline"),
        PreconditionBinding("runtime", "not-inspected"), (), (), (),
        "sec-02-v1", digest,
    )


def authorized(action: str):
    request = GovernanceAuthorizationRequest(
        "1.0", "request-1", "lifecycle-1", GovernanceIdentity("HUMAN", "requester"),
        "SHOPPING_SECRET_PROVISIONING", SHOPPING_SECRET_PROVISIONING, "CANDIDATE",
        "explicit provisioning approval", (action,), "budget-1", NOW,
    )
    decision = GovernanceAuthorizationDecision(
        "1.0", "decision-1", "request-1", GovernanceIdentity("HUMAN", "approver"),
        AuthorizationDecision.APPROVED, ("EXPLICIT_APPROVAL",), NOW,
        NOW + timedelta(hours=1), (action,), "budget-1", "sha256:snapshot",
    )
    return transition_authorization(
        GovernanceAuthorization(request), AuthorizationState.AUTHORIZED, "APPROVED", NOW,
        decision=decision, authorization_id="authorization-1",
    ).authorization


def lifecycle(value_plan, observer=None):
    action = value_plan.action
    authority = authorized(action)
    budget = GovernanceMutationBudget(
        "1.0", "budget-1", "authorization-1", (MutationBudgetLineItem(action, 1),)
    )
    request = GovernanceExecutionRequest(
        "1.0", "execution-1", "lifecycle-1", "authorization-1", "claim-1",
        "budget-1", action, SHOPPING_SECRET_PROVISIONING,
        provisioning_plan_digest(value_plan), NOW,
    )
    return ShoppingProvisioningLifecycle(authority, budget, request, snapshot())


class Observer:
    def __init__(self, values=None):
        self.values = list(values or (snapshot(), snapshot()))
        self.count = 0

    def observe_preconditions(self, request):
        value = self.values[min(self.count, len(self.values) - 1)]
        self.count += 1
        return value


class Consumer:
    def __init__(self):
        self.count = 0

    def consume_once(self, command):
        self.count += 1
        consumed_authority = transition_authorization(
            command.authorization, AuthorizationState.CONSUMED, "ATOMIC_CONSUMPTION", NOW
        ).authorization
        receipt = GovernanceAuthorizationConsumptionReceipt(
            "1.0", command.execution_request.claim_id,
            command.execution_request.lifecycle_id, command.execution_request.authorization_id,
            command.execution_request.mutation_budget_id,
            command.execution_request.execution_request_id, NOW,
            ConsumptionTransactionStatus.COMMITTED,
        )
        return AuthorizationConsumptionResult(
            consumed_authority, consume_mutation_budget(command.mutation_budget), receipt,
            command.execution_request,
        )


class Execution:
    def __init__(self, status=ExecutionStatus.COMPLETED):
        self.status = status
        self.count = 0

    def invoke_once(self, request):
        self.count += 1
        return GovernanceExecutionReceipt(
            "1.0", "receipt-1", request.lifecycle_id, request.execution_request_id,
            request.authorization_id, request.claim_id, request.mutation_budget_id,
            request.action_type, self.status, 1,
            int(self.status is ExecutionStatus.COMPLETED),
            int(self.status is ExecutionStatus.UNCERTAIN), NOW, NOW, None,
            (f"MUTATION_{self.status.value}",),
        )


class Validator:
    def __init__(self, decision=PostconditionDecision.PASS):
        self.decision = decision
        self.count = 0

    def validate_postconditions(self, receipt):
        self.count += 1
        return GovernancePostconditionReport(
            "1.0", "report-1", receipt.lifecycle_id, receipt.receipt_id, "validator-1",
            self.decision, ("VALIDATION_COMPLETE",), "expected", "observed",
            "sha256:report", NOW,
        )


def coordinator(*, consumer=None, observer=None, executions=None, validator=None):
    consumer = consumer or Consumer()
    observer = observer or Observer()
    executions = executions or {action: Execution() for action in PROVISIONING_ACTIONS}
    validator = validator or Validator()
    value = ShoppingProvisioningGovernanceCoordinator(
        authorization_consumption=consumer,
        precondition_observation=observer,
        postcondition_validation=validator,
        sops_install=executions[PROVISIONING_ACTIONS[0]],
        age_install=executions[PROVISIONING_ACTIONS[1]],
        control_plane_identity_create=executions[PROVISIONING_ACTIONS[2]],
        control_plane_recipient_register_validate=executions[PROVISIONING_ACTIONS[3]],
        offline_recovery_recipient_register_validate=executions[PROVISIONING_ACTIONS[4]],
    )
    return value, consumer, observer, executions, validator


@pytest.mark.parametrize("readiness", [Readiness.READY, Readiness.BLOCKED, Readiness.MALFORMED])
def test_non_mutating_plans_never_consume_or_invoke(readiness):
    value, consumer, _, executions, _ = coordinator()
    result = value.coordinate(plan(readiness))
    assert consumer.count == 0
    assert sum(item.count for item in executions.values()) == 0
    assert result.invocation_count == 0
    assert result.disposition is (
        CoordinatorDisposition.CLOSEOUT if readiness is Readiness.READY
        else CoordinatorDisposition.STOP
    )


def test_missing_without_valid_authorization_path_stops_zero_zero():
    value, consumer, _, executions, _ = coordinator()
    result = value.coordinate(plan(Readiness.MISSING))
    assert result.reason_codes == ("AUTHORIZATION_PATH_INVALID",)
    assert consumer.count == 0
    assert sum(item.count for item in executions.values()) == 0


def test_post_consumption_drift_stops_consumed_once_and_invoked_zero():
    observer = Observer((snapshot(), snapshot(digest="sha256:drift", snapshot_id="snapshot-2")))
    value_plan = plan(Readiness.MISSING)
    value, consumer, _, executions, _ = coordinator(observer=observer)
    result = value.coordinate(value_plan, lifecycle(value_plan))
    assert consumer.count == 1
    assert result.authorization_consumed is True
    assert result.invocation_count == 0
    assert sum(item.count for item in executions.values()) == 0


def test_allow_single_invocation_denial_after_consumption_stops(monkeypatch):
    real_decide = module.decide_next_disposition
    calls = 0

    def deny_second(context):
        nonlocal calls
        calls += 1
        if calls == 2:
            return GovernanceOrchestrationDecision(
                OrchestrationDisposition.STOP, ("SINGLE_INVOCATION_DENIED",)
            )
        return real_decide(context)

    monkeypatch.setattr(module, "decide_next_disposition", deny_second)
    value_plan = plan(Readiness.MISSING)
    value, consumer, _, executions, _ = coordinator()
    result = value.coordinate(value_plan, lifecycle(value_plan))
    assert consumer.count == 1
    assert sum(item.count for item in executions.values()) == 0
    assert result.reason_codes == ("SINGLE_INVOCATION_DENIED",)


@pytest.mark.parametrize("action", PROVISIONING_ACTIONS)
def test_exact_five_actions_route_only_to_exact_injected_adapter(action):
    value_plan = plan(Readiness.MISSING, action)
    value, consumer, _, executions, validator = coordinator()
    result = value.coordinate(value_plan, lifecycle(value_plan))
    assert consumer.count == 1
    assert {key: item.count for key, item in executions.items()} == {
        key: int(key == action) for key in PROVISIONING_ACTIONS
    }
    assert validator.count == 1
    assert result.disposition is CoordinatorDisposition.CLOSEOUT


def test_unknown_action_fails_closed_before_consumption_and_invocation():
    value_plan = plan(Readiness.MISSING, "SHOPPING_SECRET_TOOL:UNKNOWN_ENSURE")
    value, consumer, _, executions, _ = coordinator()
    result = value.coordinate(value_plan, lifecycle(value_plan))
    assert result.reason_codes == ("ACTION_NOT_SUPPORTED",)
    assert consumer.count == 0
    assert sum(item.count for item in executions.values()) == 0


@pytest.mark.parametrize("status", [ExecutionStatus.FAILED, ExecutionStatus.UNCERTAIN])
def test_failed_or_uncertain_stops_after_exactly_one_without_retry(status):
    value_plan = plan(Readiness.MISSING)
    executions = {action: Execution() for action in PROVISIONING_ACTIONS}
    executions[value_plan.action] = Execution(status)
    value, consumer, _, _, validator = coordinator(executions=executions)
    result = value.coordinate(value_plan, lifecycle(value_plan))
    assert consumer.count == 1
    assert executions[value_plan.action].count == 1
    assert validator.count == 0
    assert result.disposition is CoordinatorDisposition.STOP
    assert result.execution_status is status


@pytest.mark.parametrize("decision", [PostconditionDecision.PASS, PostconditionDecision.FAIL])
def test_completed_validates_read_only_once_and_never_mutates_again(decision):
    value_plan = plan(Readiness.MISSING)
    validator = Validator(decision)
    value, consumer, _, executions, _ = coordinator(validator=validator)
    result = value.coordinate(value_plan, lifecycle(value_plan))
    assert consumer.count == 1
    assert executions[value_plan.action].count == 1
    assert sum(item.count for item in executions.values()) == 1
    assert validator.count == 1
    assert result.disposition is (
        CoordinatorDisposition.CLOSEOUT
        if decision is PostconditionDecision.PASS else CoordinatorDisposition.STOP
    )


def test_result_is_value_free_factual_and_grants_no_capability():
    value_plan = plan(Readiness.MISSING)
    value, _, _, _, _ = coordinator()
    result = value.coordinate(value_plan, lifecycle(value_plan))
    assert isinstance(result, ShoppingProvisioningResult)
    assert not any(
        callable(getattr(result, name, None))
        for name in ("invoke", "invoke_once", "execute", "retry", "rollback", "authorize")
    )
    rendered = json.dumps(result.to_dict()).lower()
    assert not any(token in rendered for token in (
        "age-secret-key", "private", "credential", "stdout", "stderr", "/users/"
    ))
    assert result.retry_prohibited and result.rollback_prohibited
    assert result.compensation_prohibited and result.secret_values_read is False


def test_no_generic_recovery_capability_and_clean_core_dependency_direction():
    source = COORDINATOR_PATH.read_text(encoding="utf-8")
    lower = source.lower()
    assert "ops.macos" not in lower
    assert not any(token in lower for token in (
        "subprocess", "argv", "shell", "retry(", "rollback(", "compensate("
    ))
    public = {
        name for name, member in inspect.getmembers(
            ShoppingProvisioningGovernanceCoordinator, inspect.isfunction
        ) if not name.startswith("_")
    }
    assert public == {"coordinate"}
    imports = []
    for path in (ROOT / "core").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
    assert not [name for name in imports if name == "ops" or name.startswith("ops.")]
