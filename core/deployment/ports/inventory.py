"""Capability-specific read-only boundaries used by the DPL application layer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class GitIdentityPort(Protocol):
    def observe_git_identity(self) -> Mapping[str, Any]: ...


class RuntimeMetadataPort(Protocol):
    def observe_runtime_metadata(self) -> Mapping[str, Any]: ...


class LaunchdObservationPort(Protocol):
    def observe_launchd(self) -> Mapping[str, Any]: ...


class CaddyDesiredStatePort(Protocol):
    def observe_caddy_desired_state(self) -> Mapping[str, Any]: ...


class ColimaContractPort(Protocol):
    def observe_colima_contract(self) -> Mapping[str, Any]: ...


class ComposeDesiredStatePort(Protocol):
    def observe_compose_desired_state(self) -> Mapping[str, Any]: ...


class FileContentReadPort(Protocol):
    def read_text(self, relative_path: str) -> str: ...


class ClockPort(Protocol):
    def now_utc(self) -> str: ...


__all__ = (
    "CaddyDesiredStatePort",
    "ClockPort",
    "ColimaContractPort",
    "ComposeDesiredStatePort",
    "FileContentReadPort",
    "GitIdentityPort",
    "LaunchdObservationPort",
    "RuntimeMetadataPort",
)
