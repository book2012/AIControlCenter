"""Fail-closed native foundation contract for the sole SEC-02 helper operation.

This module describes package and peer-security readiness.  It does not carry
an authorization external form, connect to XPC, register a service, or mutate a
filesystem.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


AUTHORITATIVE_BUNDLE_NAMESPACE = "com.aicontrolcenter"
CLIENT_CODE_SIGNING_REQUIREMENT = None
HELPER_CODE_SIGNING_REQUIREMENT = None


class PrivilegedHelperOperation(Enum):
    RESTRICT_GOVERNANCE_DIRECTORY_MODE_0755_TO_0700 = (
        "RESTRICT_GOVERNANCE_DIRECTORY_MODE_0755_TO_0700"
    )


class NativeReadiness(Enum):
    READY = "READY"
    NOT_READY = "NOT_READY"
    MISMATCH = "MISMATCH"


@dataclass(frozen=True, slots=True)
class ResolvedSigningRequirement:
    """Repository model for future native requirement-resolver output.

    Python privacy and the marker below are not cryptographic provenance or a
    Production trust boundary. Native code-signing resolution and validation
    must eventually establish actual peer identity.
    """

    expression: str
    role: str
    _resolution_marker: object

    @classmethod
    def _from_trusted_resolver(cls, expression: str, role: str, marker: object):
        return cls(expression, role, marker)


_TRUSTED_RESOLUTION_MARKER = object()  # domain-model readiness marker only


@dataclass(frozen=True, slots=True)
class PeerSigningPolicy:
    """Only trusted, resolved, role-bound requirements can become ready."""

    client_requirement: ResolvedSigningRequirement | None
    helper_requirement: ResolvedSigningRequirement | None

    @property
    def readiness(self) -> NativeReadiness:
        if not self._is_resolved(self.client_requirement, "client") or not self._is_resolved(self.helper_requirement, "helper"):
            return NativeReadiness.NOT_READY
        if self.client_requirement.expression == self.helper_requirement.expression:
            return NativeReadiness.MISMATCH
        return NativeReadiness.READY

    @staticmethod
    def _is_resolved(requirement: object, role: str) -> bool:
        return (type(requirement) is ResolvedSigningRequirement and requirement.role == role
                and requirement._resolution_marker is _TRUSTED_RESOLUTION_MARKER)

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
        # Repository packaging exists, but authoritative bundle/signing identity does not.
        return NativeReadiness.NOT_READY


class FixedPrivilegedHelperProtocol(Protocol):
    """Exactly one semantic RPC; it has no caller-selectable mutation fields."""

    def restrict_governance_directory_mode_0755_to_0700(self) -> None: ...


__all__ = (
    "AUTHORITATIVE_BUNDLE_NAMESPACE", "CLIENT_CODE_SIGNING_REQUIREMENT",
    "FixedPrivilegedHelperProtocol", "HELPER_CODE_SIGNING_REQUIREMENT",
    "NativeReadiness", "PeerSigningPolicy", "ResolvedSigningRequirement",
    "PrivilegedHelperOperation", "SMAppServicePackageContract",
)
