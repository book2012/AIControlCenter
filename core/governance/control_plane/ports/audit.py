"""Typed governance audit persistence boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from ..domain import GovernanceIdentity


@dataclass(frozen=True, slots=True)
class GovernanceAuditEventRecord:
    """Immutable Python projection compatible with GovernanceAuditEvent v1."""

    schema_version: str
    event_id: str
    sequence: int
    event_type: str
    lifecycle_id: str
    actor: GovernanceIdentity
    authorization_id: str | None
    evidence_digests: tuple[str, ...]
    previous_hash: str | None
    event_hash: str
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class AuditPersistenceReceipt:
    event_id: str
    sequence: int
    event_hash: str
    persisted: bool


@dataclass(frozen=True, slots=True)
class GovernanceAuditQuery:
    """Bounded, read-only lifecycle query for already-persisted records."""

    lifecycle_id: str
    after_sequence: int
    limit: int


@dataclass(frozen=True, slots=True)
class GovernanceAuditQueryResult:
    records: tuple[GovernanceAuditEventRecord, ...]
    query_digest: str


class GovernanceAuditPort(Protocol):
    """Persist governance-decided facts; this boundary decides no policy."""

    def persist_audit_event(
        self, event: GovernanceAuditEventRecord
    ) -> AuditPersistenceReceipt: ...

    def query_audit_events(
        self, query: GovernanceAuditQuery
    ) -> GovernanceAuditQueryResult: ...


__all__ = (
    "AuditPersistenceReceipt", "GovernanceAuditEventRecord", "GovernanceAuditPort",
    "GovernanceAuditQuery", "GovernanceAuditQueryResult",
)
