"""Constructor-injected, call-time credential boundary."""
from __future__ import annotations

from typing import Protocol

from .errors import CredentialUnavailableError


class SecretSafeCredential:
    __slots__ = ("_consumer_key", "_consumer_secret")

    def __init__(self, consumer_key: str, consumer_secret: str) -> None:
        if not consumer_key or not consumer_secret:
            raise ValueError("credential values are required")
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret

    @property
    def consumer_key(self) -> str:
        return self._consumer_key

    @property
    def consumer_secret(self) -> str:
        return self._consumer_secret

    def __repr__(self) -> str:
        return "SecretSafeCredential(<redacted>)"

    __str__ = __repr__


class CredentialProvider(Protocol):
    def get_credentials(self) -> SecretSafeCredential: ...


class UnavailableCredentialProvider:
    def get_credentials(self) -> SecretSafeCredential:
        raise CredentialUnavailableError()
