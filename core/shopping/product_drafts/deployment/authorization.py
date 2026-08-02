"""Replaceable exact-binding, deny-by-default write authorization."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

from ..values import ActorReference, require_text, require_utc


class AuthorizationDecisionValue(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


@dataclass(frozen=True, slots=True)
class WriteAuthorizationDecision:
    action: str
    actor: ActorReference
    draft_id: str
    revision_id: str
    deployment_intent_id: str
    authorization_reference: str
    evaluated_at: datetime
    policy_reference: str
    decision: AuthorizationDecisionValue

    def __post_init__(self) -> None:
        for name in ("action", "draft_id", "revision_id", "deployment_intent_id",
                     "authorization_reference", "policy_reference"):
            require_text(getattr(self, name), name)
        if not isinstance(self.actor, ActorReference):
            raise ValueError("actor must be an ActorReference")
        require_utc(self.evaluated_at, "evaluated_at")
        if not isinstance(self.decision, AuthorizationDecisionValue):
            object.__setattr__(self, "decision", AuthorizationDecisionValue(self.decision))


class CommerceWriteAuthorizationPort(Protocol):
    def authorize(self, *, action: str, actor: ActorReference, draft_id: str,
                  revision_id: str, deployment_intent_id: str,
                  authorization_reference: str,
                  evaluated_at: datetime) -> WriteAuthorizationDecision: ...


class StaticWriteAuthorizationAdapter:
    """Instance-local adapter for tests; absence of an exact ALLOW is DENY."""

    def __init__(self, decisions: tuple[WriteAuthorizationDecision, ...] = ()) -> None:
        self._decisions = tuple(decisions)

    def authorize(self, **request: object) -> WriteAuthorizationDecision:
        require_utc(request["evaluated_at"], "evaluated_at")  # type: ignore[arg-type]
        binding = tuple(request[name] for name in (
            "action", "actor", "draft_id", "revision_id", "deployment_intent_id",
            "authorization_reference", "evaluated_at"))
        for item in self._decisions:
            if (item.action, item.actor, item.draft_id, item.revision_id,
                    item.deployment_intent_id, item.authorization_reference,
                    item.evaluated_at) == binding:
                return item
        return WriteAuthorizationDecision(
            request["action"], request["actor"], request["draft_id"],  # type: ignore[arg-type]
            request["revision_id"], request["deployment_intent_id"],  # type: ignore[arg-type]
            request["authorization_reference"], request["evaluated_at"],  # type: ignore[arg-type]
            "DENY_BY_DEFAULT", AuthorizationDecisionValue.DENY,
        )
