"""Opaque, transient destination capability contracts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from core.shopping.customer_auth import VerificationPurpose
from core.shopping.phone_normalization import CanonicalPhone, OpaquePhoneBinding


class DestinationResolutionError(RuntimeError):
    """A destination capability operation was rejected without contact data."""


class DestinationHandle:
    """An opaque process-local capability with no public token representation."""

    __slots__ = ("_token", "_initialized")

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("destination handles are not publicly reconstructable")

    @classmethod
    def _issue(cls) -> "DestinationHandle":
        import secrets

        handle = object.__new__(cls)
        object.__setattr__(handle, "_token", secrets.token_bytes(32))
        object.__setattr__(handle, "_initialized", True)
        return handle

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_initialized", False):
            raise AttributeError("destination handles are immutable")
        object.__setattr__(self, name, value)

    def __repr__(self) -> str:
        return "DestinationHandle(<opaque>)"

    def __str__(self) -> str:
        return "<opaque destination handle>"

    def __reduce__(self):  # type: ignore[no-untyped-def]
        raise TypeError("destination handles are not serializable")

    def __copy__(self):  # type: ignore[no-untyped-def]
        raise TypeError("destination handles are not copyable")

    def __deepcopy__(self, memo):  # type: ignore[no-untyped-def]
        raise TypeError("destination handles are not copyable")


@dataclass(frozen=True, slots=True)
class DestinationScope:
    """All trusted dimensions that must match before a handle is consumed."""

    provider_source: str
    purpose: VerificationPurpose
    challenge_reference: str
    replay_reference: str
    customer_id: str
    phone_binding: OpaquePhoneBinding
    browser_challenge: str | None = None

    def __post_init__(self) -> None:
        if type(self.provider_source) is not str or not self.provider_source:
            raise TypeError("destination scope provider is invalid")
        if type(self.purpose) is not VerificationPurpose:
            raise TypeError("destination scope purpose is invalid")
        for name in (
            "challenge_reference", "replay_reference", "customer_id",
        ):
            value = getattr(self, name)
            if type(value) is not str or not value:
                raise TypeError("destination scope is invalid")
        if type(self.phone_binding) is not OpaquePhoneBinding:
            raise TypeError("destination scope binding is invalid")
        if self.browser_challenge is not None and (
            type(self.browser_challenge) is not str or not self.browser_challenge
        ):
            raise TypeError("destination scope challenge is invalid")


DestinationResolutionScope = DestinationScope


@runtime_checkable
class DestinationResolutionPort(Protocol):
    """Issue and consume transient provider destination capabilities."""

    def issue(
        self, destination: CanonicalPhone, scope: DestinationScope,
    ) -> DestinationHandle:
        ...

    def resolve(
        self, handle: DestinationHandle, scope: DestinationScope,
    ) -> CanonicalPhone:
        ...


__all__ = (
    "DestinationHandle",
    "DestinationResolutionError",
    "DestinationResolutionPort",
    "DestinationResolutionScope",
    "DestinationScope",
)
