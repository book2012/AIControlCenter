"""Symbolic zero-I/O Mac projection for external evidence attestations."""

from dataclasses import dataclass, field
from typing import Any

from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    ExternalEvidenceAttestationReferenceContract,
    canonical_external_evidence_attestation_reference_contract,
)


@dataclass(frozen=True, slots=True)
class ExternalEvidenceAttestationReferenceSource:
    contract: ExternalEvidenceAttestationReferenceContract = field(
        default_factory=canonical_external_evidence_attestation_reference_contract,
        init=False,
    )
    mac_aicontrolcenter_sole_control_plane: bool = field(default=True, init=False)
    ubuntu_stateless_infrastructure_worker: bool = field(default=True, init=False)
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
        """Return closed symbolic facts; this performs no discovery or validation."""
        return {
            "evidence_requirements": self.contract.evidence_requirements,
            "reference_identity_classes": self.contract.reference_identity_classes,
            "reference_verification_state": self.contract.reference_verification_state,
            "data_identity_categories": self.contract.data_identity_categories,
            "continuity_evidence_categories": self.contract.continuity_evidence_categories,
            "evidence_exists": self.contract.evidence_exists,
            "provenance_valid": self.contract.provenance_valid,
            "integrity_binding_satisfied": self.contract.integrity_binding_satisfied,
            "account_baseline_binding_satisfied": self.contract.account_baseline_binding_satisfied,
            "authority": self.contract.authority,
            "compatible": self.contract.compatible,
            "reference_local_ready": self.contract.reference_local_ready,
            "five_category_data_identity_complete": self.contract.five_category_data_identity_complete,
            "three_category_continuity_lineage_complete": self.contract.three_category_continuity_lineage_complete,
            "recover_evidence_sufficient": self.contract.recover_evidence_sufficient,
            "mac_aicontrolcenter_sole_control_plane": self.mac_aicontrolcenter_sole_control_plane,
            "ubuntu_stateless_infrastructure_worker": self.ubuntu_stateless_infrastructure_worker,
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


def canonical_external_evidence_attestation_reference_source(
) -> ExternalEvidenceAttestationReferenceSource:
    return ExternalEvidenceAttestationReferenceSource()
