import json
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone

import pytest

from core.governance.control_plane.domain import (
    ConsumptionTransactionStatus, ExecutionStatus,
    GovernanceAuthorizationConsumptionReceipt, GovernanceExecutionReceipt,
    GovernanceExecutionRequest, GovernancePostconditionReport,
    InvalidReceiptCounts, PostconditionDecision,
)

NOW = datetime(2026, 8, 10, tzinfo=timezone.utc)


def execution_request() -> GovernanceExecutionRequest:
    return GovernanceExecutionRequest(
        "1.0.0", "execution-1", "lifecycle-1", "authorization-1", "claim-1",
        "budget-1", "SERVICE_RESTART", "service-1", "sha256:plan", NOW,
    )


def execution_receipt(status: ExecutionStatus = ExecutionStatus.COMPLETED) -> GovernanceExecutionReceipt:
    return GovernanceExecutionReceipt(
        "1.0.0", "receipt-1", "lifecycle-1", "execution-1", "authorization-1",
        "claim-1", "budget-1", "SERVICE_RESTART", status, 1,
        1 if status is ExecutionStatus.COMPLETED else 0,
        1 if status is ExecutionStatus.UNCERTAIN else 0,
        NOW, NOW, "sha256:result", ("FACT_RECORDED",),
    )


def test_consumption_receipt_is_immutable_and_does_not_imply_success() -> None:
    value = GovernanceAuthorizationConsumptionReceipt(
        "1.0.0", "claim-1", "lifecycle-1", "authorization-1", "budget-1",
        "execution-1", NOW, ConsumptionTransactionStatus.COMMITTED, 7, "sha256:replay",
    )
    with pytest.raises(FrozenInstanceError):
        value.claim_id = "other"  # type: ignore[misc]
    assert not hasattr(value, "success")
    assert not hasattr(value, "adapter_invoked")
    assert not hasattr(value, "retry_allowed")


def test_execution_request_grants_and_executes_nothing() -> None:
    value = execution_request()
    for forbidden in ("authorized", "grant_authorization", "consume", "execute"):
        assert not hasattr(value, forbidden)


@pytest.mark.parametrize("status", list(ExecutionStatus))
def test_execution_receipt_has_stable_statuses(status: ExecutionStatus) -> None:
    assert execution_receipt(status).to_dict()["status"] == status.value


@pytest.mark.parametrize("changes", [
    {"actual_invocation_count": -1},
    {"actual_invocation_count": 1, "completed_count": 2},
    {"actual_invocation_count": 1, "uncertain_count": 2},
    {"actual_invocation_count": 1, "completed_count": 1, "uncertain_count": 1},
])
def test_execution_receipt_count_invariants(changes: dict[str, int]) -> None:
    with pytest.raises(InvalidReceiptCounts):
        replace(execution_receipt(), **changes)


def test_projection_is_deterministic_json_safe_and_input_unchanged() -> None:
    value = execution_receipt()
    before = value.to_dict()
    assert before == value.to_dict()
    assert json.loads(json.dumps(before)) == before
    assert value.to_dict() == before


@pytest.mark.parametrize("decision", list(PostconditionDecision))
def test_postcondition_pass_fail_grant_no_authority(decision: PostconditionDecision) -> None:
    value = GovernancePostconditionReport(
        "1.0.0", "report-1", "lifecycle-1", "receipt-1", "validator-1",
        decision, ("VALIDATION_COMPLETE",), "expected:1", "observed:1",
        "sha256:report", NOW,
    )
    assert value.to_dict()["decision"] == decision.value
    for forbidden in ("authorized", "retry_allowed", "rollback_allowed"):
        assert not hasattr(value, forbidden)
