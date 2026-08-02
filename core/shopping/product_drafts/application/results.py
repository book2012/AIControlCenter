"""Immutable application results and safe JSON-compatible projections."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Mapping

from ..models import ApprovalDecision, ProductDraftRevision, ValidationResult
from ..serialization import to_json_compatible


class ReadOnlyProjection(dict[str, object]):
    """A JSON-serializable dictionary that rejects mutation."""

    def _immutable(self, *args: object, **kwargs: object) -> None:
        raise TypeError("projection is read-only")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable
    __ior__ = _immutable


@dataclass(frozen=True, slots=True)
class ApplicationResult:
    operation: str
    draft_id: str
    revision_id: str
    outcome: str
    authorization_reference: str
    audit_reference: str
    correlation_id: str
    completed_at: datetime
    idempotent_replay: bool = False
    validation: ValidationResult | None = None
    review_decision: ApprovalDecision | None = None
    revision: ProductDraftRevision | None = None

    def as_replay(self) -> "ApplicationResult":
        return replace(self, idempotent_replay=True)

    def projection(self) -> Mapping[str, object]:
        data = {
            "operation": self.operation,
            "draft_id": self.draft_id,
            "revision_id": self.revision_id,
            "outcome": self.outcome,
            "validation_status": self.validation.status.value if self.validation else None,
            "review_decision": self.review_decision.decision.value if self.review_decision else None,
            "authorization_reference": self.authorization_reference,
            "audit_reference": self.audit_reference,
            "idempotent_replay": self.idempotent_replay,
            "correlation_id": self.correlation_id,
            "completed_at": to_json_compatible(self.completed_at),
        }
        return ReadOnlyProjection(data)
