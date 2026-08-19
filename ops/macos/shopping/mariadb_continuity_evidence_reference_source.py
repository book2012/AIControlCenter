"""Zero-I/O Mac Control Plane projection of evidence-reference requirements."""

from dataclasses import dataclass, field
from typing import Any

from core.secrets.mariadb_continuity_evidence_reference_manifest import (
    EvidenceReferenceManifest,
    canonical_evidence_reference_manifest,
)


@dataclass(frozen=True, slots=True)
class EvidenceReferenceSource:
    manifest: EvidenceReferenceManifest = field(
        default_factory=canonical_evidence_reference_manifest, init=False
    )
    mac_control_plane_owned: bool = field(default=True, init=False)
    ubuntu_control_plane_authority: bool = field(default=False, init=False)
    authorization_authority: bool = field(default=False, init=False)
    capability_authority: bool = field(default=False, init=False)
    execution_authority: bool = field(default=False, init=False)
    mutation_authority: bool = field(default=False, init=False)
    retry_authority: bool = field(default=False, init=False)
    reconnect_authority: bool = field(default=False, init=False)
    rollback_authority: bool = field(default=False, init=False)
    value_free: bool = field(default=True, init=False)

    def to_projection(self) -> dict[str, Any]:
        return {
            "evidence_requirements": tuple(
                item.value for item in self.manifest.evidence_requirements
            ),
            "data_identity_requirements": tuple(
                item.value for item in self.manifest.data_identity_requirements
            ),
            "continuity_requirements": tuple(
                item.value for item in self.manifest.continuity_requirements
            ),
            "evidence_reference_state": self.manifest.evidence_reference_state.value,
            "evidence_exists": self.manifest.evidence_exists,
            "provenance_valid": self.manifest.provenance_valid,
            "authority": self.manifest.authority,
            "compatible": self.manifest.compatible,
            "reference_readiness_established": self.manifest.reference_readiness_established,
            "recover_evidence_sufficient": self.manifest.recover_evidence_sufficient,
            "mac_control_plane_owned": self.mac_control_plane_owned,
            "ubuntu_control_plane_authority": self.ubuntu_control_plane_authority,
            "authorization_authority": self.authorization_authority,
            "capability_authority": self.capability_authority,
            "execution_authority": self.execution_authority,
            "mutation_authority": self.mutation_authority,
            "retry_authority": self.retry_authority,
            "reconnect_authority": self.reconnect_authority,
            "rollback_authority": self.rollback_authority,
            "value_free": self.value_free,
        }


def canonical_evidence_reference_source() -> EvidenceReferenceSource:
    return EvidenceReferenceSource()
