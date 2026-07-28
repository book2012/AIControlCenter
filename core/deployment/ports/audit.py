"""Read-only DPL audit-evidence boundary."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class AuditEvidenceSinkPort(Protocol):
    """Optional observer; implementations must not mutate deployment state."""

    def record(self, evidence: Mapping[str, Any]) -> None: ...


__all__ = ("AuditEvidenceSinkPort",)
