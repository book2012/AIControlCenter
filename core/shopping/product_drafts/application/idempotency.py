"""Instance-scoped deterministic application idempotency."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from ..values import require_text

T = TypeVar("T")


class IdempotencyKeyReuseConflict(ValueError):
    """An existing key was presented with a different canonical command."""


@dataclass(frozen=True, slots=True)
class IdempotencyRecord(Generic[T]):
    command_digest: str
    result: T


class InMemoryIdempotencyStore(Generic[T]):
    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord[T]] = {}

    def lookup(self, key: str, command_digest: str) -> T | None:
        require_text(key, "idempotency_key")
        record = self._records.get(key)
        if record is None:
            return None
        if record.command_digest != command_digest:
            raise IdempotencyKeyReuseConflict("idempotency key is already bound to a different command")
        return record.result

    def bind(self, key: str, command_digest: str, result: T) -> None:
        existing = self.lookup(key, command_digest)
        if existing is None:
            self._records[key] = IdempotencyRecord(command_digest, result)
