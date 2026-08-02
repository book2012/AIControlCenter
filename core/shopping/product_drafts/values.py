"""Immutable primitives and validation shared by ProductDraft contracts."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re

SCHEMA_VERSION = "1.0.0"
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")


def require_digest(value: str, field: str = "digest") -> None:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise ValueError(f"{field} must be a lowercase sha256 digest")


def require_utc(value: datetime, field: str) -> None:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() != timezone.utc.utcoffset(value)
    ):
        raise ValueError(f"{field} must be timezone-aware UTC")


class ActorType(str, Enum):
    HUMAN = "HUMAN"
    SERVICE = "SERVICE"


@dataclass(frozen=True, slots=True)
class ActorReference:
    actor_id: str
    actor_type: ActorType

    def __post_init__(self) -> None:
        require_text(self.actor_id, "actor_id")
        if not isinstance(self.actor_type, ActorType):
            object.__setattr__(self, "actor_type", ActorType(self.actor_type))


@dataclass(frozen=True, slots=True)
class Reference:
    id: str
    label: str | None = None

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        if self.label is not None and not isinstance(self.label, str):
            raise ValueError("label must be a string or null")
