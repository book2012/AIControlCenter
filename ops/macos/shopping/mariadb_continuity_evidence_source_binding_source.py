"""Frozen zero-I/O Mac projection of the canonical source-binding contract."""

from dataclasses import dataclass, field

from core.secrets.mariadb_continuity_evidence_source_binding import (
    MariaDBContinuityEvidenceSourceBindingContract,
    canonical_mariadb_continuity_evidence_source_binding_contract,
)


@dataclass(frozen=True, slots=True)
class MariaDBContinuityEvidenceSourceBindingSource:
    contract: MariaDBContinuityEvidenceSourceBindingContract = field(
        default_factory=canonical_mariadb_continuity_evidence_source_binding_contract,
        init=False,
    )
    frozen: bool = field(default=True, init=False)
    slotted: bool = field(default=True, init=False)
    mac_aicontrolcenter_sole_control_plane: bool = field(default=True, init=False)
    ubuntu_stateless_infrastructure_worker: bool = field(default=True, init=False)
    ubuntu_control_plane_authority: bool = field(default=False, init=False)
    path_resolver_exposed: bool = field(default=False, init=False)
    filesystem_io_performed: bool = field(default=False, init=False)
    metadata_inspection_performed: bool = field(default=False, init=False)
    discovery_performed: bool = field(default=False, init=False)
    network_performed: bool = field(default=False, init=False)
    sql_performed: bool = field(default=False, init=False)
    production_access_performed: bool = field(default=False, init=False)


def canonical_mariadb_continuity_evidence_source_binding_source(
) -> MariaDBContinuityEvidenceSourceBindingSource:
    return MariaDBContinuityEvidenceSourceBindingSource()
