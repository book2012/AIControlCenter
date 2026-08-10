"""Authorization identity value objects."""

from __future__ import annotations

from dataclasses import dataclass

from .failures import InvalidAuthorizationInput


def require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidAuthorizationInput(f"{field_name} must not be empty")
    return value


@dataclass(frozen=True, slots=True)
class GovernanceIdentity:
    identity_id: str
    identity_type: str

    def __post_init__(self) -> None:
        require_text(self.identity_id, "identity_id")
        require_text(self.identity_type, "identity_type")

    def to_dict(self) -> dict[str, str]:
        return {
            "identity_id": self.identity_id,
            "identity_type": self.identity_type,
        }
