import json
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from core.governance.control_plane.domain import (
    AuthorizationBindingMismatch, AuthorizationDecision, AuthorizationState,
    GovernanceAuthorization, GovernanceAuthorizationDecision, GovernanceAuthorizationReceipt,
    GovernanceAuthorizationRequest, GovernanceIdentity, InvalidAuthorizationInput,
    RequestDecisionBindingMismatch, transition_authorization,
)

NOW = datetime(2026, 8, 10, tzinfo=timezone.utc)
LATER = datetime(2026, 8, 11, tzinfo=timezone.utc)


def models():
    req = GovernanceAuthorizationRequest(
        "1", "request-1", "lifecycle-1", GovernanceIdentity("requester-1", "HUMAN"),
        "WRITE", "target-1", "production", "reason", ("one", "two"), "budget-1", NOW,
    )
    dec = GovernanceAuthorizationDecision(
        "1", "decision-1", "request-1", GovernanceIdentity("approver-1", "HUMAN"),
        AuthorizationDecision.APPROVED, ("APPROVED",), NOW, LATER, ("one",),
        "budget-1", "sha256:snapshot",
    )
    return req, dec


@pytest.mark.parametrize("value", ["", " ", "\t"])
def test_non_empty_identity_validation(value: str) -> None:
    with pytest.raises(InvalidAuthorizationInput):
        GovernanceIdentity(value, "HUMAN")


def test_request_decision_binding() -> None:
    req, dec = models()
    with pytest.raises(RequestDecisionBindingMismatch):
        transition_authorization(
            GovernanceAuthorization(req), AuthorizationState.AUTHORIZED, "approve", NOW,
            decision=replace(dec, request_id="other"), authorization_id="authorization-1",
        )


@pytest.mark.parametrize(
    "change",
    [
        {"lifecycle_id": "other"},
        {"approved_scope": ("one", "outside")},
        {"mutation_budget_id": "other"},
        {"precondition_snapshot_digest": "sha256:other"},
    ],
)
def test_receipt_preserves_exact_bindings(change: dict[str, object]) -> None:
    req, dec = models()
    receipt = GovernanceAuthorizationReceipt(
        "1", "authorization-1", "request-1", "decision-1", "lifecycle-1",
        AuthorizationState.AUTHORIZED, ("one",), "budget-1", "sha256:snapshot", NOW, LATER,
    )
    with pytest.raises(AuthorizationBindingMismatch):
        GovernanceAuthorization(
            req, AuthorizationState.AUTHORIZED, "authorization-1", dec, replace(receipt, **change),
        )


def test_scope_may_narrow_but_never_widen() -> None:
    req, dec = models()
    result = transition_authorization(
        GovernanceAuthorization(req), AuthorizationState.AUTHORIZED, "approve", NOW,
        decision=dec, authorization_id="authorization-1",
    )
    assert result.authorization.receipt.approved_scope == ("one",)  # type: ignore[union-attr]


def test_projection_is_deterministic_and_json_safe() -> None:
    req, dec = models()
    result = transition_authorization(
        GovernanceAuthorization(req), AuthorizationState.AUTHORIZED, "approve", NOW,
        decision=dec, authorization_id="authorization-1",
    )
    first = result.authorization.to_dict()
    assert first == result.authorization.to_dict()
    assert json.loads(json.dumps(first)) == first
    assert first["state"] == "AUTHORIZED"
    assert first["receipt"]["approved_scope"] == ["one"]
