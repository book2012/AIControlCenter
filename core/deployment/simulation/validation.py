"""Pure validation result for simulation authorization decisions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationValidationResult:
    status: str
    reason_codes: tuple[str, ...]

    @property
    def allowed(self) -> bool:
        return not self.reason_codes


__all__ = ("SimulationValidationResult",)
