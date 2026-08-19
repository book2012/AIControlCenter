"""Zero-I/O Mac projection of the repository acquisition descriptor contract."""

from dataclasses import dataclass, field
from typing import Any

from core.secrets.mariadb_continuity_evidence_acquisition_descriptor import (
    MariaDBContinuityEvidenceAcquisitionContract,
    canonical_mariadb_continuity_evidence_acquisition_contract,
)


@dataclass(frozen=True, slots=True)
class MariaDBContinuityEvidenceAcquisitionDescriptorSource:
    contract: MariaDBContinuityEvidenceAcquisitionContract = field(
        default_factory=canonical_mariadb_continuity_evidence_acquisition_contract,
        init=False,
    )
    mac_aicontrolcenter_sole_control_plane: bool = field(default=True, init=False)
    ubuntu_stateless_infrastructure_worker: bool = field(default=True, init=False)
    ubuntu_control_plane_authority: bool = field(default=False, init=False)

    def to_projection(self) -> dict[str, Any]:
        """Project canonical facts without locating or acquiring a source."""
        return {
            item.name: getattr(self.contract, item.name)
            for item in self.contract.__dataclass_fields__.values()
        } | {
            "mac_aicontrolcenter_sole_control_plane": self.mac_aicontrolcenter_sole_control_plane,
            "ubuntu_stateless_infrastructure_worker": self.ubuntu_stateless_infrastructure_worker,
            "ubuntu_control_plane_authority": self.ubuntu_control_plane_authority,
        }


def canonical_mariadb_continuity_evidence_acquisition_descriptor_source(
) -> MariaDBContinuityEvidenceAcquisitionDescriptorSource:
    return MariaDBContinuityEvidenceAcquisitionDescriptorSource()
