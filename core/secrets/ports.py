"""Core port for safe secret-backend metadata inspection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Callable, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


_IDENTIFIER = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,126}[A-Za-z0-9]$|^[A-Za-z0-9]$"


class SecretReference(BaseModel):
    """Value-free metadata identifying a secret without resolving it.

    A reference is deliberately not a credential source.  It carries only
    bounded names that an explicitly authorized outer boundary may interpret.
    """

    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True,
        revalidate_instances="always", hide_input_in_errors=True,
    )

    backend: str = Field(
        strict=True, min_length=1, max_length=128, pattern=_IDENTIFIER,
    )
    key_name: str = Field(
        strict=True, min_length=1, max_length=128, pattern=_IDENTIFIER,
    )

    def to_dict(self) -> dict[str, str]:
        """Return metadata only; never a secret value."""

        return {"backend": self.backend, "key_name": self.key_name}


@dataclass(frozen=True, slots=True)
class SecretBackendInspection:
    """Value-free backend readiness metadata returned by an outer adapter."""

    backend_kind: str
    production_status: str
    configuration_valid: bool
    ready: bool
    checks: tuple[tuple[str, bool], ...]
    error_code: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "backend_kind": self.backend_kind,
            "production_status": self.production_status,
            "configuration_valid": self.configuration_valid,
            "ready": self.ready,
            "checks": [
                {"name": name, "passed": passed}
                for name, passed in self.checks
            ],
            "error_code": self.error_code,
            "value_free": True,
            "secret_values_read": False,
        }


class SecretBackendInspectionPort(Protocol):
    def inspect(self) -> SecretBackendInspection:
        """Inspect backend readiness without reading secret material."""
        ...


class SecretLeaseConsumed(RuntimeError):
    """A one-shot secret lease has already been consumed."""


class SecretLeaseExpired(RuntimeError):
    """A one-shot secret lease is no longer within its bounded lifetime."""


class EphemeralSecretLease:
    """A bounded secret value that can be obtained exactly once and never serialized."""

    __slots__ = ("_secret", "_consumed", "_expires_at", "_clock", "_lock")

    def __init__(
        self,
        secret: str | bytes,
        *,
        utc_clock: Callable[[], datetime] | None = None,
        clock: Callable[[], datetime] | None = None,
        ttl: timedelta = timedelta(minutes=5),
    ) -> None:
        if type(secret) not in (str, bytes) or not secret:
            raise ValueError("secret material is invalid")
        if utc_clock is not None and clock is not None:
            raise ValueError("choose one UTC clock")
        clock = utc_clock or clock
        if clock is not None and not callable(clock):
            raise TypeError("an injected UTC clock is required")
        if type(ttl) is not timedelta or not timedelta(0) < ttl <= timedelta(minutes=5):
            raise ValueError("secret lease lifetime is outside the bounded policy")
        clock = clock or (lambda: datetime.now(timezone.utc))
        try:
            issued_at = clock()
            if (not isinstance(issued_at, datetime) or issued_at.tzinfo is None
                    or issued_at.utcoffset() != timedelta(0)):
                raise ValueError
        except (TypeError, ValueError, AttributeError, OverflowError):
            raise ValueError("secret lease clock is invalid") from None
        self._secret = secret
        self._consumed = False
        self._expires_at = issued_at + ttl
        self._clock = clock
        self._lock = Lock()

    def consume(self) -> str | bytes:
        with self._lock:
            if self._consumed:
                raise SecretLeaseConsumed("secret lease already consumed")
            try:
                now = self._clock()
                if (not isinstance(now, datetime) or now.tzinfo is None
                        or now.utcoffset() != timedelta(0) or now >= self._expires_at):
                    raise ValueError
            except (TypeError, ValueError, AttributeError, OverflowError):
                self._consumed = True
                self._secret = None
                raise SecretLeaseExpired("secret lease expired") from None
            self._consumed = True
            secret = self._secret
            self._secret = None
            return secret

    def __repr__(self) -> str:
        return "EphemeralSecretLease(<redacted>)"

    def __str__(self) -> str:
        return "<ephemeral secret lease>"

    def __reduce__(self):  # type: ignore[no-untyped-def]
        raise TypeError("secret leases are not serializable")

    def __copy__(self):  # type: ignore[no-untyped-def]
        raise TypeError("secret leases are not copyable")

    def __deepcopy__(self, memo):  # type: ignore[no-untyped-def]
        raise TypeError("secret leases are not copyable")


class SecretResolutionError(RuntimeError):
    """A secret resolution failure with no material or reader details."""


@runtime_checkable
class SecretResolverPort(Protocol):
    """Resolve value-free metadata into a one-shot ephemeral lease."""

    def resolve(self, reference: SecretReference) -> EphemeralSecretLease:
        ...


__all__ = (
    "EphemeralSecretLease", "SecretBackendInspection", "SecretBackendInspectionPort",
    "SecretLeaseConsumed", "SecretLeaseExpired", "SecretReference", "SecretResolutionError",
    "SecretResolverPort",
)
