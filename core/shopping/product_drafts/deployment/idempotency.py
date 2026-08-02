"""Instance-local successful-write idempotency."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from ..values import require_digest, require_text

T = TypeVar("T")


class IdempotencyConflict(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class IdempotencyRecord(Generic[T]):
    plan_digest: str
    result: T


class InMemoryWriteIdempotencyStore(Generic[T]):
    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord[T]] = {}

    def lookup(self, key: str, plan_digest: str) -> T | None:
        require_text(key, "idempotency_key"); require_digest(plan_digest, "plan_digest")
        record = self._records.get(key)
        if record is None:
            return None
        if record.plan_digest != plan_digest:
            raise IdempotencyConflict("idempotency key is bound to a different plan")
        return record.result

    def bind(self, key: str, plan_digest: str, result: T) -> None:
        if self.lookup(key, plan_digest) is None:
            self._records[key] = IdempotencyRecord(plan_digest, result)
