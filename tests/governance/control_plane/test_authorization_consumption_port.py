"""Contracts for the generic SEC-02 authorization-consumption boundary."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timedelta, timezone
import inspect

import pytest

from core.governance.control_plane.domain import (
    AuthorizationDecision,
    AuthorizationState,
    ConsumptionTransactionStatus,
    GovernanceAuthorization,
    GovernanceAuthorizationConsumptionReceipt,
    GovernanceAuthorizationDecision,
    GovernanceAuthorizationRequest,
    GovernanceExecutionRequest,
    GovernanceIdentity,
    GovernanceMutationBudget,
    MutationBudgetLineItem,
    MutationBudgetStatus,
    consume_mutation_budget,
    transition_authorization,
)
from core.governance.control_plane.ports import (
    AuthorizationConsumptionCommand,
    AuthorizationConsumptionPort,
    AuthorizationConsumptionResult,
)

NOW = datetime(2026, 8, 17, tzinfo=timezone.utc)


def authorized() -> GovernanceAuthorization:
    request = GovernanceAuthorizationRequest(
        "1.0.0", "request-1", "lifecycle-1", GovernanceIdentity("human", "approver-1"),
        "CONTROLLED_CHANGE", "target-1", "managed", "approved change",
        ("SERVICE_RESTART",), "budget-1", NOW,
    )
    decision = GovernanceAuthorizationDecision(
        "1.0.0", "decision-1", "request-1", GovernanceIdentity("human", "approver-2"),
        AuthorizationDecision.APPROVED, ("POLICY_SATISFIED",), NOW,
        NOW + timedelta(hours=1), ("SERVICE_RESTART",), "budget-1", "sha256:snapshot",
    )
    return transition_authorization(
        GovernanceAuthorization(request), AuthorizationState.AUTHORIZED,
        "APPROVED", NOW, decision=decision, authorization_id="authorization-1",
    ).authorization


def budget(*, consumed: bool = False, action: str = "SERVICE_RESTART", allowed: int = 2) -> GovernanceMutationBudget:
    value = GovernanceMutationBudget(
        "1.0.0", "budget-1", "authorization-1",
        (MutationBudgetLineItem(action, allowed),),
    )
    return consume_mutation_budget(value) if consumed else value


def request(**changes: object) -> GovernanceExecutionRequest:
    value = GovernanceExecutionRequest(
        "1.0.0", "execution-1", "lifecycle-1", "authorization-1", "claim-1",
        "budget-1", "SERVICE_RESTART", "target-1", "sha256:plan", NOW,
    )
    return replace(value, **changes)


def consumed_authorization() -> GovernanceAuthorization:
    return transition_authorization(
        authorized(), AuthorizationState.CONSUMED, "ATOMIC_CONSUMPTION", NOW,
    ).authorization


def receipt(**changes: object) -> GovernanceAuthorizationConsumptionReceipt:
    value = GovernanceAuthorizationConsumptionReceipt(
        "1.0.0", "claim-1", "lifecycle-1", "authorization-1", "budget-1",
        "execution-1", NOW, ConsumptionTransactionStatus.COMMITTED,
    )
    return replace(value, **changes)


def result(**changes: object) -> AuthorizationConsumptionResult:
    values = {
        "authorization": consumed_authorization(),
        "mutation_budget": budget(consumed=True),
        "consumption_receipt": receipt(),
        "execution_request": request(),
    }
    values.update(changes)
    return AuthorizationConsumptionResult(**values)  # type: ignore[arg-type]


def test_descriptors_are_frozen_slots_and_construction_performs_no_mutation() -> None:
    authorization, mutation_budget, execution_request = authorized(), budget(), request()
    command = AuthorizationConsumptionCommand(authorization, mutation_budget, execution_request)
    assert tuple(item.name for item in fields(command)) == (
        "authorization", "mutation_budget", "execution_request",
    )
    with pytest.raises(FrozenInstanceError):
        command.authorization = authorization  # type: ignore[misc]
    assert command.authorization is authorization
    assert command.mutation_budget is mutation_budget
    assert command.execution_request is execution_request
    value = result()
    assert tuple(item.name for item in fields(value)) == (
        "authorization", "mutation_budget", "consumption_receipt", "execution_request",
    )
    with pytest.raises(FrozenInstanceError):
        value.mutation_budget = mutation_budget  # type: ignore[misc]


def test_port_has_exact_single_consumption_api_and_annotations() -> None:
    methods = tuple(
        name for name, member in vars(AuthorizationConsumptionPort).items()
        if callable(member) and not name.startswith("_")
    )
    assert methods == ("consume_once",)
    assert inspect.get_annotations(
        AuthorizationConsumptionPort.consume_once, eval_str=True
    ) == {
        "command": AuthorizationConsumptionCommand,
        "return": AuthorizationConsumptionResult,
    }
    assert getattr(AuthorizationConsumptionPort, "_is_protocol", False)
    assert inspect.getsource(AuthorizationConsumptionPort.consume_once).strip().endswith("...")


def test_authorized_available_command_succeeds() -> None:
    AuthorizationConsumptionCommand(authorized(), budget(), request())


def test_command_rejects_target_mismatch() -> None:
    with pytest.raises(ValueError):
        AuthorizationConsumptionCommand(
            authorized(), budget(), request(target="target-2")
        )


def test_result_rejects_target_mismatch() -> None:
    with pytest.raises(ValueError):
        result(execution_request=request(target="target-2"))


def test_action_present_in_budget_but_outside_authorization_scope_is_rejected() -> None:
    execution_request = request(action_type="SERVICE_STOP")
    with pytest.raises(ValueError):
        AuthorizationConsumptionCommand(
            authorized(), budget(action="SERVICE_STOP"), execution_request
        )
    with pytest.raises(ValueError):
        result(
            mutation_budget=budget(consumed=True, action="SERVICE_STOP"),
            execution_request=execution_request,
        )


def test_action_inside_authorization_scope_is_accepted() -> None:
    AuthorizationConsumptionCommand(authorized(), budget(), request())
    result()


@pytest.mark.parametrize("boundary", ["command", "result"])
def test_authorization_request_mutation_budget_binding_mismatch_is_rejected(
    boundary: str,
) -> None:
    authorization = authorized() if boundary == "command" else consumed_authorization()
    object.__setattr__(
        authorization.request, "requested_mutation_budget_id", "budget-other"
    )
    with pytest.raises(ValueError):
        if boundary == "command":
            AuthorizationConsumptionCommand(authorization, budget(), request())
        else:
            result(authorization=authorization)


@pytest.mark.parametrize("state", [
    AuthorizationState.REQUESTED, AuthorizationState.STALE,
    AuthorizationState.CONSUMED, AuthorizationState.REJECTED,
])
def test_command_rejects_every_non_authorized_state(state: AuthorizationState) -> None:
    value = authorized()
    object.__setattr__(value, "state", state)
    with pytest.raises(ValueError):
        AuthorizationConsumptionCommand(value, budget(), request())


@pytest.mark.parametrize("status", [
    MutationBudgetStatus.CONSUMED, MutationBudgetStatus.EXHAUSTED, MutationBudgetStatus.VIOLATED,
])
def test_command_rejects_non_available_budget(status: MutationBudgetStatus) -> None:
    value = budget()
    object.__setattr__(value, "status", status)
    with pytest.raises(ValueError):
        AuthorizationConsumptionCommand(authorized(), value, request())


@pytest.mark.parametrize("kind", [
    "budget_authorization", "request_lifecycle", "request_authorization", "request_budget",
])
def test_command_rejects_all_binding_mismatches(kind: str) -> None:
    mutation_budget, execution_request = budget(), request()
    if kind == "budget_authorization":
        object.__setattr__(mutation_budget, "authorization_id", "other")
    else:
        field = {"request_lifecycle": "lifecycle_id", "request_authorization": "authorization_id", "request_budget": "mutation_budget_id"}[kind]
        object.__setattr__(execution_request, field, "other")
    with pytest.raises(ValueError):
        AuthorizationConsumptionCommand(authorized(), mutation_budget, execution_request)


def test_command_rejects_absent_action_nonavailable_line_and_preexisting_invocation() -> None:
    with pytest.raises(ValueError):
        AuthorizationConsumptionCommand(authorized(), budget(action="SERVICE_STOP"), request())
    value = budget()
    object.__setattr__(value.line_items[0], "status", MutationBudgetStatus.CONSUMED)
    with pytest.raises(ValueError):
        AuthorizationConsumptionCommand(authorized(), value, request())
    value = budget()
    object.__setattr__(value.line_items[0], "actual_invocation_count", 1)
    with pytest.raises(ValueError):
        AuthorizationConsumptionCommand(authorized(), value, request())


def test_consumed_result_with_committed_exact_bindings_succeeds() -> None:
    result()


def test_result_requires_consumed_authorization_and_exact_consumed_budget() -> None:
    with pytest.raises(ValueError):
        result(authorization=authorized())
    for status in (MutationBudgetStatus.AVAILABLE, MutationBudgetStatus.EXHAUSTED):
        value = budget(consumed=True)
        object.__setattr__(value, "status", status)
        with pytest.raises(ValueError):
            result(mutation_budget=value)
    value = budget(consumed=True)
    object.__setattr__(value.line_items[0], "status", MutationBudgetStatus.EXHAUSTED)
    with pytest.raises(ValueError):
        result(mutation_budget=value)


@pytest.mark.parametrize("kind", [
    "budget_authorization", "receipt_lifecycle", "receipt_authorization", "receipt_budget",
    "receipt_request", "receipt_claim", "request_lifecycle", "request_authorization",
    "request_budget", "request_action",
])
def test_result_rejects_every_receipt_request_and_budget_binding_mismatch(kind: str) -> None:
    values: dict[str, object] = {}
    if kind == "budget_authorization":
        value = budget(consumed=True); object.__setattr__(value, "authorization_id", "other"); values["mutation_budget"] = value
    elif kind.startswith("receipt_"):
        field = {"receipt_lifecycle": "lifecycle_id", "receipt_authorization": "authorization_id", "receipt_budget": "mutation_budget_id", "receipt_request": "execution_request_id", "receipt_claim": "claim_id"}[kind]
        value = receipt(); object.__setattr__(value, field, "other"); values["consumption_receipt"] = value
    else:
        field = {"request_lifecycle": "lifecycle_id", "request_authorization": "authorization_id", "request_budget": "mutation_budget_id", "request_action": "action_type"}[kind]
        value = request(); object.__setattr__(value, field, "SERVICE_STOP" if kind == "request_action" else "other"); values["execution_request"] = value
    with pytest.raises(ValueError):
        result(**values)


def test_result_requires_committed_receipt_and_zero_invocation_accounting() -> None:
    value = receipt()
    object.__setattr__(value, "transaction_status", "PENDING")
    with pytest.raises(ValueError):
        result(consumption_receipt=value)
    value = budget(consumed=True)
    object.__setattr__(value.line_items[0], "actual_invocation_count", 1)
    with pytest.raises(ValueError):
        result(mutation_budget=value)


@pytest.mark.parametrize("field_name", [
    "authorization", "mutation_budget", "execution_request",
])
def test_command_requires_exact_typed_values(field_name: str) -> None:
    values = {"authorization": authorized(), "mutation_budget": budget(), "execution_request": request()}
    values[field_name] = object()
    with pytest.raises(ValueError):
        AuthorizationConsumptionCommand(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("field_name", [
    "authorization", "mutation_budget", "consumption_receipt", "execution_request",
])
def test_result_requires_exact_typed_values(field_name: str) -> None:
    values = {
        "authorization": consumed_authorization(),
        "mutation_budget": budget(consumed=True),
        "consumption_receipt": receipt(),
        "execution_request": request(),
    }
    values[field_name] = object()
    with pytest.raises(ValueError):
        AuthorizationConsumptionResult(**values)  # type: ignore[arg-type]


def test_generic_core_dependency_direction_and_no_forbidden_capability() -> None:
    module = inspect.getmodule(AuthorizationConsumptionCommand)
    assert module is not None
    source = inspect.getsource(module)
    tree = ast.parse(source)
    imports = tuple(
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    )
    assert all(name in {"__future__", "dataclasses", "typing", "domain"} or name.endswith("domain") for name in imports)
    prohibited = (
        "shopping", "sops", "provider", "subprocess", "filesystem", "network", "environment",
        "shell", "argv", "secret", "credential", "stdout", "stderr",
        "retry", "rollback", "compensation", "replay authority", "invoke_once(", "execute(",
    )
    lowered = source.lower()
    assert not any(marker in lowered for marker in prohibited)
    for descriptor in (AuthorizationConsumptionCommand, AuthorizationConsumptionResult):
        names = tuple(item.name.lower() for item in fields(descriptor))
        assert not any(marker in name for name in names for marker in prohibited)


def test_result_is_evidence_and_grants_no_execution_authority() -> None:
    value = result()
    for forbidden in (
        "invoke", "execute", "authorize", "allow_single_invocation", "retry", "rollback", "compensate",
    ):
        assert not hasattr(value, forbidden)
