"""Injected, in-memory macOS foundation for provider destination resolution."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable
from threading import Lock

from core.shopping.customer_identity import require_utc
from core.shopping.phone_normalization import CanonicalPhone
from core.shopping.ports.destination_resolution import (
    DestinationHandle, DestinationResolutionError, DestinationResolutionPort,
    DestinationScope,
)

DEFAULT_DESTINATION_TTL = timedelta(minutes=5)
MAX_DESTINATION_TTL = timedelta(minutes=5)
DEFAULT_MAX_PENDING_DESTINATIONS = 128


@dataclass(frozen=True, slots=True)
class _PendingDestination:
    destination: CanonicalPhone
    scope: DestinationScope
    issued_at: datetime
    expires_at: datetime


class ProviderDestinationResolver(DestinationResolutionPort):
    """Keep destination capabilities local, scoped, and one-shot.

    This foundation deliberately has no host-store, environment, network, or
    provider integration.  A future provider boundary may inject this port.
    """

    def __init__(
        self,
        utc_clock: Callable[[], datetime] | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
        ttl: timedelta = DEFAULT_DESTINATION_TTL,
        max_pending: int = DEFAULT_MAX_PENDING_DESTINATIONS,
    ) -> None:
        if utc_clock is not None and clock is not None:
            raise ValueError("choose one UTC clock")
        if utc_clock is None:
            utc_clock = clock
        if utc_clock is not None and not callable(utc_clock):
            raise TypeError("an injected UTC clock is required")
        if type(ttl) is not timedelta or not timedelta(0) < ttl <= MAX_DESTINATION_TTL:
            raise ValueError("destination TTL is outside the bounded policy")
        if type(max_pending) is not int or isinstance(max_pending, bool) or max_pending < 1:
            raise ValueError("destination capacity is invalid")
        self._clock = (
            utc_clock if utc_clock is not None
            else lambda: datetime.now(timezone.utc)
        )
        self._ttl = ttl
        self._max_pending = max_pending
        self._entries: dict[DestinationHandle, _PendingDestination] = {}
        self._lock = Lock()

    def _now(self) -> datetime:
        try:
            return require_utc(self._clock())
        except (TypeError, ValueError, AttributeError, OverflowError):
            raise DestinationResolutionError("destination resolution unavailable") from None

    def _remove_expired(self, now: datetime) -> None:
        for handle, entry in tuple(self._entries.items()):
            if entry.expires_at <= now:
                del self._entries[handle]

    def issue_destination(
        self, destination: CanonicalPhone, scope: DestinationScope,
    ) -> DestinationHandle:
        if type(destination) is not CanonicalPhone or type(scope) is not DestinationScope:
            raise DestinationResolutionError("destination issue rejected")
        now = self._now()
        with self._lock:
            self._remove_expired(now)
            if len(self._entries) >= self._max_pending:
                raise DestinationResolutionError("destination capacity exhausted")
            handle = DestinationHandle._issue()
            self._entries[handle] = _PendingDestination(
                destination=destination,
                scope=scope,
                issued_at=now,
                expires_at=now + self._ttl,
            )
        return handle

    def resolve_destination(
        self, handle: DestinationHandle, scope: DestinationScope,
    ) -> CanonicalPhone:
        if type(handle) is not DestinationHandle or type(scope) is not DestinationScope:
            raise DestinationResolutionError("destination resolution rejected")
        now = self._now()
        with self._lock:
            self._remove_expired(now)
            entry = self._entries.get(handle)
            if entry is None or entry.scope != scope:
                raise DestinationResolutionError("destination resolution rejected")
            destination = entry.destination
            # Remove the capability before returning contact data.
            del self._entries[handle]
        return destination

    @property
    def pending_count(self) -> int:
        """Return bounded pending capability count without exposing entries."""

        now = self._now()
        with self._lock:
            self._remove_expired(now)
            return len(self._entries)

    # Short names make the port convenient for provider-specific compositions
    # without changing the explicit boundary vocabulary.
    issue = issue_destination
    resolve = resolve_destination


MacProviderDestinationResolver = ProviderDestinationResolver


__all__ = ("MacProviderDestinationResolver", "ProviderDestinationResolver")
