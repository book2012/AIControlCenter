from dataclasses import replace

import pytest

from core.governance.control_plane.domain import (
    ApprovalRequired, AuthorizationDecision, AuthorizationState, GovernanceAuthorization,
    InvalidAuthorizationInput, InvalidAuthorizationTransition, RequestDecisionBindingMismatch,
    TerminalAuthorizationReuse, transition_authorization,
)
from .test_authorization_state_machine import T1, T2, decision, request


def test_rejection_cannot_authorize() -> None:
    with pytest.raises(ApprovalRequired):
        transition_authorization(
            GovernanceAuthorization(request()), AuthorizationState.AUTHORIZED, "bad", T1,
            decision=decision(AuthorizationDecision.REJECTED), authorization_id="authorization-1",
        )


def test_approval_cannot_reject() -> None:
    with pytest.raises(InvalidAuthorizationTransition):
        transition_authorization(
            GovernanceAuthorization(request()), AuthorizationState.REJECTED, "bad", T1,
            decision=decision(AuthorizationDecision.APPROVED), authorization_id="authorization-1",
        )


def test_mismatched_request_id_fails_without_payload_dump() -> None:
    with pytest.raises(RequestDecisionBindingMismatch) as captured:
        transition_authorization(
            GovernanceAuthorization(request()), AuthorizationState.AUTHORIZED, "bad", T1,
            decision=replace(decision(AuthorizationDecision.APPROVED), request_id="other"),
            authorization_id="authorization-1",
        )
    assert "REQUEST_DECISION_BINDING_MISMATCH" in str(captured.value)
    assert "GovernanceAuthorizationRequest(" not in str(captured.value)


def test_missing_required_binding_fails() -> None:
    with pytest.raises(InvalidAuthorizationInput):
        replace(decision(AuthorizationDecision.APPROVED), precondition_snapshot_digest=None)


def test_illegal_transition_and_terminal_reuse_are_distinct() -> None:
    with pytest.raises(InvalidAuthorizationTransition) as illegal:
        transition_authorization(
            GovernanceAuthorization(request()), AuthorizationState.CONSUMED, "bad", T1,
        )
    rejected = transition_authorization(
        GovernanceAuthorization(request()), AuthorizationState.REJECTED, "no", T1,
        decision=decision(AuthorizationDecision.REJECTED), authorization_id="authorization-1",
    ).authorization
    with pytest.raises(TerminalAuthorizationReuse) as terminal:
        transition_authorization(rejected, AuthorizationState.AUTHORIZED, "reuse", T2)
    assert "INVALID_AUTHORIZATION_TRANSITION" in str(illegal.value)
    assert "TERMINAL_AUTHORIZATION_REUSE" in str(terminal.value)
