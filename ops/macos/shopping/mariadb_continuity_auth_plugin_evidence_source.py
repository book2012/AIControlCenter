"""Symbolic Mac Control Plane boundary for future auth-plugin evidence."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EvidenceSourceOwner(str, Enum):
    MAC_CONTROL_PLANE = "MAC_CONTROL_PLANE"


@dataclass(frozen=True, slots=True)
class AuthPluginEvidenceSource:
    owner: EvidenceSourceOwner = field(default=EvidenceSourceOwner.MAC_CONTROL_PLANE, init=False)
    auth_plugin_state: str = field(default="UNRESOLVED", init=False)
    authoritative_evidence_available: bool = field(default=False, init=False)
    pymysql_compatibility_established: bool = field(default=False, init=False)

    @property
    def ready(self) -> bool:
        return bool(
            self.authoritative_evidence_available
            and self.pymysql_compatibility_established
        )

    def to_projection(self) -> dict[str, Any]:
        return {
            "owner": self.owner.value,
            "auth_plugin_state": self.auth_plugin_state,
            "authoritative_evidence_available": self.authoritative_evidence_available,
            "pymysql_compatibility_established": self.pymysql_compatibility_established,
            "ready": self.ready,
            "authorization_authority": False,
            "capability_authority": False,
            "execution_authority": False,
            "mutation_authority": False,
            "retry_authority": False,
            "reconnect_authority": False,
            "rollback_authority": False,
            "value_free": True,
        }


def canonical_auth_plugin_evidence_source() -> AuthPluginEvidenceSource:
    return AuthPluginEvidenceSource()
