"""Typed, simulation-only ports for DPL-03D."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SimulationIntent:
    action_id: str
    action_type: str
    target: str
    dependency_ids: tuple[str, ...]
    result_expectation: str


class ReplayGuard(Protocol):
    def consume(self, authorization_id: str, nonce: str) -> bool: ...


class SimulationExecutor(Protocol):
    executor_type: str

    def execute(self, intents: tuple[SimulationIntent, ...]) -> tuple[dict, ...]: ...


__all__ = ("ReplayGuard", "SimulationExecutor", "SimulationIntent")
