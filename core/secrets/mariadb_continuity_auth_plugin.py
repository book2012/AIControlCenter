"""Closed auth-plugin evidence contract; no driver is imported here."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


AUTH_PLUGIN_STATE = "UNRESOLVED"
AUTHORITATIVE_EVIDENCE_AVAILABLE = False
PYMYSQL_COMPATIBILITY_ESTABLISHED = False


class AuthPluginState(str, Enum):
    UNRESOLVED = "UNRESOLVED"


class RuntimeEvidenceState(str, Enum):
    OBSERVED_COMPATIBLE = "OBSERVED_COMPATIBLE"
    OBSERVED_INCOMPATIBLE = "OBSERVED_INCOMPATIBLE"
    NOT_OBSERVED = "NOT_OBSERVED"


def _authority_projection() -> dict[str, bool]:
    return {
        "authorization_authority": False,
        "capability_authority": False,
        "execution_authority": False,
        "mutation_authority": False,
        "retry_authority": False,
        "reconnect_authority": False,
        "rollback_authority": False,
        "value_free": True,
    }


@dataclass(frozen=True, slots=True)
class CanonicalAuthPluginReadiness:
    auth_plugin_state: AuthPluginState = field(default=AuthPluginState.UNRESOLVED, init=False)
    authoritative_evidence_available: bool = field(default=False, init=False)
    pymysql_compatibility_established: bool = field(default=False, init=False)

    @property
    def ready(self) -> bool:
        return bool(
            self.authoritative_evidence_available
            and self.pymysql_compatibility_established
        )

    def to_projection(self) -> dict[str, Any]:
        projection: dict[str, Any] = {
            "auth_plugin_state": self.auth_plugin_state.value,
            "authoritative_evidence_available": self.authoritative_evidence_available,
            "pymysql_compatibility_established": self.pymysql_compatibility_established,
            "ready": self.ready,
        }
        projection.update(_authority_projection())
        return projection


@dataclass(frozen=True, slots=True)
class RuntimeAuthPluginEvidence:
    """Non-canonical test seam that cannot name a plugin or grant readiness."""

    observation: RuntimeEvidenceState

    def __post_init__(self) -> None:
        if type(self.observation) is not RuntimeEvidenceState:
            raise TypeError("observation must be a RuntimeEvidenceState")

    def to_projection(self) -> dict[str, Any]:
        projection: dict[str, Any] = {
            "observation": self.observation.value,
            "canonical": False,
            "canonical_readiness_affected": False,
        }
        projection.update(_authority_projection())
        return projection


def canonical_auth_plugin_readiness() -> CanonicalAuthPluginReadiness:
    return CanonicalAuthPluginReadiness()
