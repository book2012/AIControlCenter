"""Replaceable, side-effect-free application ports and in-memory test adapters."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

from ..serialization import sha256_digest
from ..values import ActorReference, require_text, require_utc


class AuthorizationDecisionValue(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    action: str
    actor: ActorReference
    draft_id: str
    revision_id: str
    authorization_reference: str
    decision: AuthorizationDecisionValue
    evaluated_at: datetime
    policy_reference: str

    def __post_init__(self) -> None:
        for name in ("action", "draft_id", "revision_id", "authorization_reference", "policy_reference"):
            require_text(getattr(self, name), name)
        if not isinstance(self.actor, ActorReference):
            raise ValueError("actor must be an ActorReference")
        if not isinstance(self.decision, AuthorizationDecisionValue):
            object.__setattr__(self, "decision", AuthorizationDecisionValue(self.decision))
        require_utc(self.evaluated_at, "evaluated_at")


class AuthorizationPort(Protocol):
    def authorize(self, *, action: str, actor: ActorReference, draft_id: str,
                  revision_id: str, authorization_reference: str,
                  evaluated_at: datetime) -> AuthorizationDecision: ...


class StaticAuthorizationAdapter:
    """Exact-match, deny-by-default adapter intended for tests."""

    def __init__(self, decisions: tuple[AuthorizationDecision, ...] = ()) -> None:
        self._decisions = tuple(decisions)

    def authorize(self, *, action: str, actor: ActorReference, draft_id: str,
                  revision_id: str, authorization_reference: str,
                  evaluated_at: datetime) -> AuthorizationDecision:
        require_utc(evaluated_at, "evaluated_at")
        for item in self._decisions:
            if (item.action, item.actor, item.draft_id, item.revision_id,
                    item.authorization_reference, item.evaluated_at) == (
                    action, actor, draft_id, revision_id,
                    authorization_reference, evaluated_at):
                return item
        return AuthorizationDecision(
            action, actor, draft_id, revision_id, authorization_reference,
            AuthorizationDecisionValue.DENY, evaluated_at, "DENY_BY_DEFAULT",
        )


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    event_type: str
    draft_id: str
    revision_id: str
    actor: ActorReference
    correlation_id: str
    authorization_reference: str
    audit_reference: str
    outcome: str
    occurred_at: datetime
    payload_digest: str

    def __post_init__(self) -> None:
        for name in ("event_id", "event_type", "draft_id", "revision_id",
                     "correlation_id", "authorization_reference", "audit_reference",
                     "outcome", "payload_digest"):
            require_text(getattr(self, name), name)
        if not isinstance(self.actor, ActorReference):
            raise ValueError("actor must be an ActorReference")
        require_utc(self.occurred_at, "occurred_at")

    @classmethod
    def create(cls, *, event_type: str, draft_id: str, revision_id: str,
               actor: ActorReference, correlation_id: str,
               authorization_reference: str, audit_reference: str,
               outcome: str, occurred_at: datetime, payload: object) -> "AuditEvent":
        payload_digest = sha256_digest(payload)
        event_id = sha256_digest({
            "event_type": event_type, "draft_id": draft_id,
            "revision_id": revision_id, "actor": actor,
            "correlation_id": correlation_id,
            "authorization_reference": authorization_reference,
            "audit_reference": audit_reference, "outcome": outcome,
            "occurred_at": occurred_at, "payload_digest": payload_digest,
        })
        return cls(event_id, event_type, draft_id, revision_id, actor,
                   correlation_id, authorization_reference, audit_reference,
                   outcome, occurred_at, payload_digest)


class AuditEventPort(Protocol):
    def record(self, event: AuditEvent) -> None: ...


class InMemoryAuditAdapter:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        if not isinstance(event, AuditEvent):
            raise TypeError("event must be an AuditEvent")
        self._events.append(event)

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)
