"""Injected read-only port for Shopping service-start evidence."""

from __future__ import annotations

from typing import Protocol

from core.shopping.observability.service_start import ServiceStartEvidence


class ShoppingServiceStartObservationPort(Protocol):
    async def observe(self) -> tuple[ServiceStartEvidence, ...]:
        """Return one immutable observation snapshot without retrying."""
        ...


__all__ = ("ShoppingServiceStartObservationPort",)
