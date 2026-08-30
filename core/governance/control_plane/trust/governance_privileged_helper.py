"""Fail-closed native foundation contract for the sole SEC-02 helper operation.

This module describes package and peer-security readiness.  It does not carry
an authorization external form, connect to XPC, register a service, or mutate a
filesystem.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class PrivilegedHelperOperation(Enum):
    RESTRICT_GOVERNANCE_DIRECTORY_MODE_0755_TO_0700 = (
        "RESTRICT_GOVERNANCE_DIRECTORY_MODE_0755_TO_0700"
    )


class NativeReadiness(Enum):
    READY = "READY"
    NOT_READY = "NOT_READY"
    MISMATCH = "MISMATCH"


@dataclass(frozen=True, slots=True)
class PeerSigningPolicy:
    """Requirements are deployment inputs, never caller assertions."""

    client_requirement: str | None
    helper_requirement: str | None

    @property
    def readiness(self) -> NativeReadiness:
        if not self.client_requirement or not self.helper_requirement:
            return NativeReadiness.NOT_READY
        return NativeReadiness.READY

    def evaluate(self, *, client_matches: bool, helper_matches: bool) -> NativeReadiness:
        if self.readiness is not NativeReadiness.READY:
            return NativeReadiness.NOT_READY
        if type(client_matches) is not bool or type(helper_matches) is not bool:
            return NativeReadiness.MISMATCH
        return (
            NativeReadiness.READY
            if client_matches and helper_matches
            else NativeReadiness.MISMATCH
        )


@dataclass(frozen=True, slots=True)
class SMAppServicePackageContract:
    minimum_macos_major: int = 13
    bundled_launch_daemon: bool = True
    registration_permitted: bool = False

    @property
    def readiness(self) -> NativeReadiness:
        # No repository-native app bundle or authoritative signing identity exists.
        return NativeReadiness.NOT_READY


class FixedPrivilegedHelperProtocol(Protocol):
    """Exactly one semantic RPC; it has no caller-selectable mutation fields."""

    def restrict_governance_directory_mode_0755_to_0700(self) -> None: ...


__all__ = (
    "FixedPrivilegedHelperProtocol", "NativeReadiness", "PeerSigningPolicy",
    "PrivilegedHelperOperation", "SMAppServicePackageContract",
)
