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


class ExternalEvidenceDescriptor(str, Enum):
    EXTERNAL_VALUE_FREE_REDACTED_HISTORICAL_AUTH_PLUGIN_ATTESTATION_DESCRIPTOR = (
        "EXTERNAL_VALUE_FREE_REDACTED_HISTORICAL_AUTH_PLUGIN_ATTESTATION_DESCRIPTOR"
    )


class ExternalEvidenceClass(str, Enum):
    OPERATOR_SUPPLIED_HISTORICAL_ATTESTATION = "OPERATOR_SUPPLIED_HISTORICAL_ATTESTATION"
    IMMUTABLE_HISTORICAL_ADMINISTRATIVE_ARTIFACT = "IMMUTABLE_HISTORICAL_ADMINISTRATIVE_ARTIFACT"


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


@dataclass(frozen=True, slots=True)
class HistoricalAuthPluginEvidenceContract:
    """Value-free trust requirements; defining this DTO proves no plugin fact."""

    descriptor: ExternalEvidenceDescriptor = field(
        default=ExternalEvidenceDescriptor.EXTERNAL_VALUE_FREE_REDACTED_HISTORICAL_AUTH_PLUGIN_ATTESTATION_DESCRIPTOR,
        init=False,
    )
    acceptable_evidence_classes: tuple[ExternalEvidenceClass, ...] = field(
        default=tuple(ExternalEvidenceClass), init=False
    )
    independent_pre_existing_historical_evidence_required: bool = field(default=True, init=False)
    account_binding_required: bool = field(default=True, init=False)
    provenance_required: bool = field(default=True, init=False)
    timestamp_required: bool = field(default=True, init=False)
    immutable_integrity_identity_required: bool = field(default=True, init=False)
    trusted_issuer_required: bool = field(default=True, init=False)
    credential_material_forbidden: bool = field(default=True, init=False)
    production_authority: bool = field(default=False, init=False)
    authoritative_evidence_available: bool = field(default=False, init=False)

    @property
    def ready(self) -> bool:
        return self.authoritative_evidence_available

    def to_projection(self) -> dict[str, Any]:
        projection: dict[str, Any] = {
            "descriptor": self.descriptor.value,
            "acceptable_evidence_classes": tuple(item.value for item in self.acceptable_evidence_classes),
            "independent_pre_existing_historical_evidence_required": self.independent_pre_existing_historical_evidence_required,
            "account_binding_required": self.account_binding_required,
            "provenance_required": self.provenance_required,
            "timestamp_required": self.timestamp_required,
            "immutable_integrity_identity_required": self.immutable_integrity_identity_required,
            "trusted_issuer_required": self.trusted_issuer_required,
            "credential_material_forbidden": self.credential_material_forbidden,
            "production_authority": self.production_authority,
            "authoritative_evidence_available": self.authoritative_evidence_available,
            "ready": self.ready,
        }
        projection.update(_authority_projection())
        return projection


def canonical_auth_plugin_readiness() -> CanonicalAuthPluginReadiness:
    return CanonicalAuthPluginReadiness()


def canonical_historical_auth_plugin_evidence_contract() -> HistoricalAuthPluginEvidenceContract:
    return HistoricalAuthPluginEvidenceContract()
