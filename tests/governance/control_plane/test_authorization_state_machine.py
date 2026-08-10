from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from core.governance.control_plane.domain import (
    AuthorizationDecision,
    AuthorizationState,
    GovernanceAuthorization,
    GovernanceAuthorizationDecision,
    GovernanceAuthorizationRequest,
    GovernanceIdentity,
    InvalidAuthorizationTransition,
    TerminalAuthorizationReuse,
    transition_authorization,
)

T0 = datetime(2026, 8, 10, 1, tzinfo=timezone.utc)
T1 = datetime(2026, 8, 10, 2, tzinfo=timezone.utc)
T2 = datetime(2026, 8, 10, 3, tzinfo=timezone.utc)


def request() -> GovernanceAuthorizationRequest:
    return GovernanceAuthorizationRequest(
        "1.0.0", "request-1", "lifecycle-1", GovernanceIdentity("user-1", "HUMAN"),
        "DEPLOY", "service-1", "production", "controlled change",
        ("deploy:service-1",), "budget-1", T0,
    )


def decision(value: AuthorizationDecision) -> GovernanceAuthorizationDecision:
    approved = value is AuthorizationDecision.APPROVED
    return GovernanceAuthorizationDecision(
        "1.0.0", "decision-1", "request-1", GovernanceIdentity("approver-1", "HUMAN"),
        value, ("POLICY_REVIEWED",), T0, T2 if approved else None,
        ("deploy:service-1",) if approved else None, "budget-1" if approved else None,
        "sha256:snapshot" if approved else None,
    )


def authorized():
    return transition_authorization(
        GovernanceAuthorization(request()), AuthorizationState.AUTHORIZED, "approved", T1,
        decision=decision(AuthorizationDecision.APPROVED), authorization_id="authorization-1",
    )


def test_all_four_allowed_transitions() -> None:
    approved = authorized()
    rejected = transition_authorization(
        GovernanceAuthorization(request()), AuthorizationState.REJECTED, "rejected", T1,
        decision=decision(AuthorizationDecision.REJECTED), authorization_id="authorization-2",
    )
    stale = transition_authorization(
        approved.authorization, AuthorizationState.STALE, "AUTHORIZATION_EXPIRED", T2,
        precondition_comparison_digest="sha256:comparison",
    )
    consumed = transition_authorization(
        approved.authorization, AuthorizationState.CONSUMED, "claim consumed", T2,
        audit_event_id="audit-1",
    )
    assert [
        rejected.authorization.state,
        stale.authorization.state,
        consumed.authorization.state,
    ] == [
        AuthorizationState.REJECTED,
        AuthorizationState.STALE,
        AuthorizationState.CONSUMED,
    ]
    assert approved.state_record.transitioned_at == T1
    assert consumed.authorization.receipt is not None
    assert "success" not in consumed.authorization.receipt.to_dict()


@pytest.mark.parametrize(
    "start,next_state",
    [
        (AuthorizationState.REQUESTED, AuthorizationState.CONSUMED),
        (AuthorizationState.REQUESTED, AuthorizationState.STALE),
        (AuthorizationState.AUTHORIZED, AuthorizationState.REJECTED),
        (AuthorizationState.AUTHORIZED, AuthorizationState.AUTHORIZED),
    ],
)
def test_forbidden_transition_classes(
    start: AuthorizationState,
    next_state: AuthorizationState,
) -> None:
    current = (
        GovernanceAuthorization(request())
        if start is AuthorizationState.REQUESTED
        else authorized().authorization
    )
    with pytest.raises(InvalidAuthorizationTransition):
        transition_authorization(current, next_state, "forbidden", T2)


@pytest.mark.parametrize("terminal", [AuthorizationState.STALE, AuthorizationState.CONSUMED])
def test_receipt_terminal_states_cannot_transition(terminal: AuthorizationState) -> None:
    current = transition_authorization(
        authorized().authorization,
        terminal,
        "terminal",
        T2,
    ).authorization
    with pytest.raises(TerminalAuthorizationReuse):
        transition_authorization(current, AuthorizationState.CONSUMED, "reuse", T2)


def test_rejected_terminal_state_cannot_transition() -> None:
    current = transition_authorization(
        GovernanceAuthorization(request()), AuthorizationState.REJECTED, "no", T1,
        decision=decision(AuthorizationDecision.REJECTED), authorization_id="authorization-2",
    ).authorization
    with pytest.raises(TerminalAuthorizationReuse):
        transition_authorization(current, AuthorizationState.AUTHORIZED, "reuse", T2)


def test_transition_does_not_mutate_input() -> None:
    original = authorized().authorization
    transitioned = transition_authorization(original, AuthorizationState.CONSUMED, "claim", T2)
    assert original.state is AuthorizationState.AUTHORIZED
    assert transitioned.authorization is not original
    with pytest.raises(FrozenInstanceError):
        original.state = AuthorizationState.CONSUMED  # type: ignore[misc]
