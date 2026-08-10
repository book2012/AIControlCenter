from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from core.governance.control_plane.domain import (
    AuthorizationDecision,
    AuthorizationSnapshotBindingMismatch,
    AuthorizationState,
    GovernanceAuthorization,
    GovernanceAuthorizationDecision,
    GovernanceAuthorizationRequest,
    GovernanceIdentity,
    InvalidStaleEvaluationState,
    PreconditionComparisonStatus,
    TerminalAuthorizationReuse,
    evaluate_authorization_expiry,
    evaluate_authorization_preconditions,
    transition_authorization,
)
from .test_precondition_snapshot import snapshot

T0 = datetime(2026, 8, 10, 1, tzinfo=timezone.utc)
T1 = datetime(2026, 8, 10, 2, tzinfo=timezone.utc)
EXPIRY = datetime(2026, 8, 10, 3, tzinfo=timezone.utc)
T4 = datetime(2026, 8, 10, 4, tzinfo=timezone.utc)


def requested() -> GovernanceAuthorization:
    request = GovernanceAuthorizationRequest(
        "1.0.0", "request-1", "lifecycle-1", GovernanceIdentity("requester", "HUMAN"),
        "DEPLOY", "target-1", "production", "controlled change", ("deploy",),
        "budget-1", T0,
    )
    return GovernanceAuthorization(request)


def authorized() -> GovernanceAuthorization:
    decision = GovernanceAuthorizationDecision(
        "1.0.0", "decision-1", "request-1", GovernanceIdentity("approver", "HUMAN"),
        AuthorizationDecision.APPROVED, ("APPROVED",), T0, EXPIRY, ("deploy",),
        "budget-1", "sha256:snapshot",
    )
    return transition_authorization(
        requested(), AuthorizationState.AUTHORIZED, "approved", T1,
        decision=decision, authorization_id="authorization-1",
    ).authorization


def rejected() -> GovernanceAuthorization:
    decision = GovernanceAuthorizationDecision(
        "1.0.0", "decision-rejected", "request-1", GovernanceIdentity("approver", "HUMAN"),
        AuthorizationDecision.REJECTED, ("REJECTED",), T0, None, None, None, None,
    )
    return transition_authorization(
        requested(), AuthorizationState.REJECTED, "rejected", T1,
        decision=decision, authorization_id="authorization-rejected",
    ).authorization


def test_authorized_match_remains_same_authorization_without_record() -> None:
    current = authorized()
    observed = replace(snapshot(), snapshot_id="recollected", collected_at=T4)
    result = evaluate_authorization_preconditions(current, snapshot(), observed, T4)
    assert result.comparison.status is PreconditionComparisonStatus.MATCH
    assert result.authorization is current
    assert result.authorization.state is AuthorizationState.AUTHORIZED
    assert result.state_record is None
    assert result.authorization.receipt is not None
    assert result.authorization.receipt.issued_at == T1
    assert result.authorization.receipt.precondition_snapshot_digest == "sha256:snapshot"


def test_authorized_drift_becomes_terminal_stale_without_consumption() -> None:
    current = authorized()
    result = evaluate_authorization_preconditions(
        current, snapshot(), snapshot(policy_version="policy-2"), T4,
        comparison_digest="sha256:comparison",
    )
    assert current.state is AuthorizationState.AUTHORIZED
    assert result.authorization.state is AuthorizationState.STALE
    assert result.state_record is not None
    assert result.state_record.current_state is AuthorizationState.STALE
    assert result.state_record.transition_reason.startswith("PRECONDITION_DRIFT:")
    assert result.state_record.precondition_comparison_digest == "sha256:comparison"
    assert result.authorization.receipt is not None
    assert result.authorization.receipt.precondition_snapshot_digest == "sha256:snapshot"
    with pytest.raises(TerminalAuthorizationReuse):
        transition_authorization(result.authorization, AuthorizationState.AUTHORIZED, "reuse", T4)


def test_authorization_snapshot_binding_mismatch_fails_without_payload_dump() -> None:
    expected = snapshot(snapshot_digest="secret-like-payload-must-not-appear")
    with pytest.raises(AuthorizationSnapshotBindingMismatch) as captured:
        evaluate_authorization_preconditions(authorized(), expected, expected, T4)
    message = str(captured.value)
    assert "AUTHORIZATION_SNAPSHOT_BINDING_MISMATCH" in message
    assert "secret-like-payload-must-not-appear" not in message
    assert "GovernancePreconditionSnapshot(" not in message


def test_expiry_uses_caller_time_and_exact_boundary_is_inclusive() -> None:
    current = authorized()
    assert evaluate_authorization_expiry(current, EXPIRY - timedelta(microseconds=1)) is None
    assert evaluate_authorization_expiry(current, EXPIRY) is None
    result = evaluate_authorization_expiry(current, EXPIRY + timedelta(microseconds=1))
    assert result is not None
    assert result.authorization.state is AuthorizationState.STALE
    assert result.state_record.transition_reason == "AUTHORIZATION_EXPIRED"
    assert current.state is AuthorizationState.AUTHORIZED


@pytest.mark.parametrize(
    "invalid",
    [
        pytest.param(requested, id="requested"),
        pytest.param(lambda: transition_authorization(authorized(), AuthorizationState.CONSUMED, "consumed", T4).authorization, id="consumed"),
        pytest.param(rejected, id="rejected"),
        pytest.param(lambda: evaluate_authorization_expiry(authorized(), T4).authorization, id="stale"),
    ],
)
def test_non_authorized_states_cannot_gain_authority_from_preconditions(invalid) -> None:
    current = invalid()
    with pytest.raises(InvalidStaleEvaluationState):
        evaluate_authorization_preconditions(current, snapshot(), snapshot(), T4)
    assert current.state is not AuthorizationState.AUTHORIZED


@pytest.mark.parametrize("current", [requested, rejected])
def test_non_authorized_states_cannot_gain_authority_from_expiry(current) -> None:
    value = current()
    with pytest.raises(InvalidStaleEvaluationState):
        evaluate_authorization_expiry(value, T4)
    assert value.state is not AuthorizationState.AUTHORIZED
