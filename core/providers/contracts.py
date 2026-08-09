"""Vendor-neutral AI provider contracts owned by AIControlCenter."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable


JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


class ProviderIdentity(str, Enum):
    OPENAI = "openai"
    CLAUDE = "claude"
    OLLAMA = "ollama"
    FAKE = "fake"

    @classmethod
    def normalize(cls, value: "ProviderIdentity | str") -> str:
        normalized = value.value if isinstance(value, cls) else str(value).strip().lower()
        if not normalized:
            raise ValueError("provider identity must not be empty")
        return normalized


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class ProviderMessage:
    role: MessageRole | str
    content: str

    def __post_init__(self) -> None:
        role = self.role if isinstance(self.role, MessageRole) else MessageRole(self.role)
        if not self.content:
            raise ValueError("message content must not be empty")
        object.__setattr__(self, "role", role)

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role.value, "content": self.content}


@dataclass(frozen=True)
class TimeoutPolicy:
    seconds: float = 30.0

    def __post_init__(self) -> None:
        if self.seconds <= 0:
            raise ValueError("timeout seconds must be positive")

    def to_dict(self) -> dict[str, float]:
        return {"seconds": self.seconds}


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least one")

    def to_dict(self) -> dict[str, int]:
        return {"max_attempts": self.max_attempts}


def _json_safe_mapping(value: Mapping[str, JsonValue]) -> Mapping[str, JsonValue]:
    result: dict[str, JsonValue] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("metadata keys must be strings")
        if any(marker in key.lower() for marker in ("key", "secret", "token", "authorization", "credential")):
            raise ValueError("secret-bearing metadata keys are prohibited")
        result[key] = item
    return MappingProxyType(result)


@dataclass(frozen=True)
class ProviderRequest:
    provider: ProviderIdentity | str
    model: str
    messages: tuple[ProviderMessage, ...]
    instructions: str | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)
    timeout: TimeoutPolicy = field(default_factory=TimeoutPolicy)
    retry: RetryPolicy = field(default_factory=RetryPolicy)

    def __post_init__(self) -> None:
        if not self.model:
            raise ValueError("model must not be empty")
        if not self.messages:
            raise ValueError("at least one message is required")
        object.__setattr__(self, "provider", ProviderIdentity.normalize(self.provider))
        object.__setattr__(self, "messages", tuple(self.messages))
        object.__setattr__(self, "metadata", _json_safe_mapping(self.metadata))

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "provider": self.provider,
            "model": self.model,
            "messages": [message.to_dict() for message in self.messages],
            "instructions": self.instructions,
            "metadata": dict(self.metadata),
            "timeout": self.timeout.to_dict(),
            "retry": self.retry.to_dict(),
        }


@dataclass(frozen=True)
class ProviderUsage:
    input_units: int | None = None
    output_units: int | None = None
    total_units: int | None = None

    def to_dict(self) -> dict[str, int | None]:
        return {
            "input_units": self.input_units,
            "output_units": self.output_units,
            "total_units": self.total_units,
        }


@dataclass(frozen=True)
class ProviderResponse:
    provider: ProviderIdentity | str
    model: str
    content: str
    status: str = "completed"
    finish_reason: str | None = None
    provider_request_id: str | None = None
    usage: ProviderUsage | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", ProviderIdentity.normalize(self.provider))
        object.__setattr__(self, "metadata", _json_safe_mapping(self.metadata))

    def audit_metadata(self) -> dict[str, JsonValue]:
        return {
            "provider": self.provider,
            "model": self.model,
            "outcome": "success",
            "provider_request_id": self.provider_request_id,
            **dict(self.metadata),
        }

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "provider": self.provider,
            "model": self.model,
            "content": self.content,
            "status": self.status,
            "finish_reason": self.finish_reason,
            "provider_request_id": self.provider_request_id,
            "usage": self.usage.to_dict() if self.usage else None,
            "metadata": dict(self.metadata),
        }


@runtime_checkable
class ProviderAdapter(Protocol):
    @property
    def provider(self) -> str:
        ...

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        ...
