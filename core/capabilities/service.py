"""AIControlCenter-owned composition facade for external capabilities."""

from __future__ import annotations

from .contracts import CapabilityObserver


class CapabilityStatusService:
    def __init__(self, observer: CapabilityObserver) -> None:
        self._observer = observer

    def status(self) -> dict[str, object]:
        return self._observer.observe().to_dict()
