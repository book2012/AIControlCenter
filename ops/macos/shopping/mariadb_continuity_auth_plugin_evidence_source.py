"""Symbolic Mac Control Plane boundary for future auth-plugin evidence."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.secrets.mariadb_continuity_auth_plugin import (
    AUTH_PLUGIN_STATE,
    AUTHORITATIVE_EVIDENCE_AVAILABLE,
    PYMYSQL_COMPATIBILITY_ESTABLISHED,
)


class EvidenceSourceOwner(str, Enum):
    MAC_CONTROL_PLANE = "MAC_CONTROL_PLANE"


@dataclass(frozen=True, slots=True)
class AuthPluginEvidenceSource:
    owner: EvidenceSourceOwner = field(default=EvidenceSourceOwner.MAC_CONTROL_PLANE, init=False)
    auth_plugin_state: str = field(default=AUTH_PLUGIN_STATE, init=False)
    authoritative_evidence_available: bool = field(
        default=AUTHORITATIVE_EVIDENCE_AVAILABLE, init=False
    )
    pymysql_compatibility_established: bool = field(
        default=PYMYSQL_COMPATIBILITY_ESTABLISHED, init=False
    )
    independent_pre_existing_historical_evidence_required: bool = field(default=True, init=False)
    account_binding_required: bool = field(default=True, init=False)
    provenance_required: bool = field(default=True, init=False)
    timestamp_required: bool = field(default=True, init=False)
    immutable_integrity_identity_required: bool = field(default=True, init=False)
    trusted_issuer_required: bool = field(default=True, init=False)
    credential_material_forbidden: bool = field(default=True, init=False)
    production_authority: bool = field(default=False, init=False)

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
            "independent_pre_existing_historical_evidence_required": self.independent_pre_existing_historical_evidence_required,
            "account_binding_required": self.account_binding_required,
            "provenance_required": self.provenance_required,
            "timestamp_required": self.timestamp_required,
            "immutable_integrity_identity_required": self.immutable_integrity_identity_required,
            "trusted_issuer_required": self.trusted_issuer_required,
            "credential_material_forbidden": self.credential_material_forbidden,
            "production_authority": self.production_authority,
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
