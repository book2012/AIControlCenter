"""Injected macOS provider-secret resolver foundation."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from core.secrets.ports import (
    EphemeralSecretLease, SecretReference, SecretResolutionError,
    SecretResolverPort,
)


class ProviderSecretResolver(SecretResolverPort):
    """Use only an explicitly injected reader; never inspect host secret stores."""

    def __init__(
        self,
        reader: Callable[[SecretReference], str | bytes] | None = None,
        *,
        utc_clock: Callable[[], datetime] | None = None,
        clock: Callable[[], datetime] | None = None,
        lease_ttl: timedelta = timedelta(minutes=5),
    ) -> None:
        if reader is not None and not callable(reader):
            raise TypeError("an injected secret reader is required")
        if utc_clock is not None and clock is not None:
            raise ValueError("choose one UTC clock")
        if utc_clock is not None and not callable(utc_clock):
            raise TypeError("an injected UTC clock is required")
        if clock is not None and not callable(clock):
            raise TypeError("an injected UTC clock is required")
        if type(lease_ttl) is not timedelta or not timedelta(0) < lease_ttl <= timedelta(minutes=5):
            raise ValueError("secret lease lifetime is outside the bounded policy")
        self._reader = reader
        self._clock = utc_clock if utc_clock is not None else clock
        self._lease_ttl = lease_ttl

    def resolve(self, reference: SecretReference) -> EphemeralSecretLease:
        if type(reference) is not SecretReference:
            raise SecretResolutionError("secret resolution rejected")
        if self._reader is None:
            raise SecretResolutionError("secret resolution unavailable")
        try:
            secret = self._reader(reference)
            return EphemeralSecretLease(
                secret, utc_clock=self._clock, ttl=self._lease_ttl,
            )
        except Exception:
            raise SecretResolutionError("secret resolution unavailable") from None

    def resolve_secret(self, reference: SecretReference) -> EphemeralSecretLease:
        return self.resolve(reference)


MacProviderSecretResolver = ProviderSecretResolver


__all__ = ("MacProviderSecretResolver", "ProviderSecretResolver")
