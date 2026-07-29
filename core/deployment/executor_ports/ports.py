"""Dependency-injected ports for future non-production execution."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class NonProductionExecutorPort(Protocol):
    def execute(
        self, request: Mapping[str, Any], *, result_timestamp: str
    ) -> Mapping[str, Any]: ...


class ExecutorCapabilityProvider(Protocol):
    def capability(self) -> Mapping[str, Any]: ...


class ExecutorPolicyValidator(Protocol):
    def validate(
        self, request: Mapping[str, Any], capability: Mapping[str, Any],
        authorization: Mapping[str, Any], *, validation_timestamp: str,
    ) -> Mapping[str, Any]: ...


__all__ = (
    "ExecutorCapabilityProvider", "ExecutorPolicyValidator",
    "NonProductionExecutorPort",
)
