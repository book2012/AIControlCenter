import ast
import inspect
import json
from dataclasses import replace

import pytest

from core.governance.control_plane import application
from core.governance.control_plane.application import OrchestrationDisposition, decide_next_disposition
from core.governance.control_plane.application import orchestration_policy
from core.governance.control_plane.domain import (
    AuthorizationState, ExecutionStatus, GovernanceMutationBudget, MutationBudgetLineItem,
    MutationBudgetStatus, PostconditionDecision,
)
from tests.governance.control_plane.test_orchestration_policy import (
    authorization, consumed_context, execution, postcondition,
)


@pytest.mark.parametrize("status", [ExecutionStatus.FAILED, ExecutionStatus.UNCERTAIN])
def test_remaining_count_after_failed_or_uncertain_is_accounting_only(status: ExecutionStatus) -> None:
    remaining = GovernanceMutationBudget(
        "1.0.0", "budget-1", "authorization-1",
        (MutationBudgetLineItem("SERVICE_RESTART", 2, 1, uncertain_count=int(status is ExecutionStatus.UNCERTAIN), status=MutationBudgetStatus.CONSUMED),),
        MutationBudgetStatus.CONSUMED,
    )
    assert remaining.remaining_count == 1
    assert decide_next_disposition(consumed_context(
        mutation_budget=remaining, execution_receipt=execution(status),
    )).disposition is OrchestrationDisposition.STOP


def test_repeated_same_action_is_not_permitted_from_remaining_count() -> None:
    remaining = GovernanceMutationBudget(
        "1.0.0", "budget-1", "authorization-1",
        (MutationBudgetLineItem("SERVICE_RESTART", 2, 1, status=MutationBudgetStatus.CONSUMED),),
        MutationBudgetStatus.CONSUMED,
    )
    decision = decide_next_disposition(consumed_context(mutation_budget=remaining))
    assert decision.disposition is OrchestrationDisposition.STOP
    assert decision.reason_codes == ("ACTION_ALREADY_ATTEMPTED",)


def test_consumed_authorization_and_pass_never_grant_another_execution() -> None:
    context = consumed_context(execution_receipt=execution(), postcondition_report=postcondition(PostconditionDecision.PASS))
    decision = decide_next_disposition(context)
    assert context.authorization.state is AuthorizationState.CONSUMED
    assert decision.disposition is OrchestrationDisposition.ALLOW_CLOSEOUT
    assert decision.disposition is not OrchestrationDisposition.ALLOW_SINGLE_INVOCATION


@pytest.mark.parametrize("forbidden", [
    "retry", "can_retry", "retry_allowed", "retry_execution", "automatic_retry",
    "rollback", "can_rollback", "rollback_allowed", "compensate", "automatic_rollback",
])
def test_no_retry_rollback_or_compensation_api_exists(forbidden: str) -> None:
    assert not hasattr(application, forbidden)
    assert not hasattr(orchestration_policy, forbidden)


def test_policy_has_no_attempt_loops_ports_adapters_or_external_access() -> None:
    source = inspect.getsource(orchestration_policy)
    tree = ast.parse(source)
    assert not any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree))
    forbidden_imports = {"pathlib", "subprocess", "sqlite3", "socket", "requests", "urllib", "os"}
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imports.isdisjoint(forbidden_imports)
    lowered = source.lower()
    for marker in ("..ports", "..adapters", "getenv", "environ", "current_time", "sleep(", "git ", "secret"):
        assert marker not in lowered


@pytest.mark.parametrize("context", [
    consumed_context(),
    consumed_context(execution_receipt=execution(ExecutionStatus.FAILED)),
    consumed_context(execution_receipt=execution(ExecutionStatus.UNCERTAIN)),
    consumed_context(execution_receipt=execution(), postcondition_report=postcondition(PostconditionDecision.PASS)),
])
def test_retry_and_rollback_are_prohibited_for_every_decision(context) -> None:
    decision = decide_next_disposition(context)
    assert decision.retry_prohibited is True
    assert decision.rollback_prohibited is True
    assert json.loads(json.dumps(decision.to_dict())) == decision.to_dict()
