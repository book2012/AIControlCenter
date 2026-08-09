"""Normalized, audit-safe provider failures."""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping

from core.providers.contracts import JsonValue, ProviderIdentity


class ProviderErrorCode(str, Enum):
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    CREDENTIAL_MISSING = "credential_missing"
    INVALID_REQUEST = "invalid_request"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    UPSTREAM_ERROR = "upstream_error"
    INTERNAL_ADAPTER_ERROR = "internal_adapter_error"
    DUPLICATE_PROVIDER = "duplicate_provider"
    UNKNOWN_PROVIDER = "unknown_provider"


_SAFE_MESSAGES = {
    ProviderErrorCode.PROVIDER_UNAVAILABLE: "provider is unavailable",
    ProviderErrorCode.CREDENTIAL_MISSING: "provider credential is not configured",
    ProviderErrorCode.INVALID_REQUEST: "provider request or configuration is invalid",
    ProviderErrorCode.TIMEOUT: "provider request timed out",
    ProviderErrorCode.RATE_LIMIT: "provider rate limit was reached",
    ProviderErrorCode.UPSTREAM_ERROR: "provider returned an upstream error",
    ProviderErrorCode.INTERNAL_ADAPTER_ERROR: "provider adapter failed internally",
    ProviderErrorCode.DUPLICATE_PROVIDER: "provider is already registered",
    ProviderErrorCode.UNKNOWN_PROVIDER: "provider is not registered",
}


class ProviderError(Exception):
    """Failure whose string, repr, and JSON forms contain allowlisted data only."""

    def __init__(
        self,
        code: ProviderErrorCode,
        provider: ProviderIdentity | str | None = None,
        *,
        model: str | None = None,
        provider_request_id: str | None = None,
        metadata: Mapping[str, JsonValue] | None = None,
    ) -> None:
        self.code = code
        self.provider = ProviderIdentity.normalize(provider) if provider is not None else None
        self.model = model
        self.provider_request_id = provider_request_id
        self.metadata = self._safe_metadata(metadata or {})
        super().__init__(_SAFE_MESSAGES[code])

    @staticmethod
    def _safe_metadata(metadata: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
        allowed = {"operation", "failure_class", "retryable"}
        return {key: value for key, value in metadata.items() if key in allowed}

    def __str__(self) -> str:
        return f"{self.code.value}: {_SAFE_MESSAGES[self.code]}"

    def __repr__(self) -> str:
        return f"ProviderError(code={self.code.value!r}, provider={self.provider!r})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code.value,
                "message": _SAFE_MESSAGES[self.code],
                "provider": self.provider,
                "model": self.model,
                "provider_request_id": self.provider_request_id,
                "metadata": dict(self.metadata),
            }
        }

    def audit_metadata(self) -> dict[str, JsonValue]:
        return {
            "provider": self.provider,
            "model": self.model,
            "outcome": self.code.value,
            "provider_request_id": self.provider_request_id,
        }
