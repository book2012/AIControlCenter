"""Frozen zero-I/O Mac projection of protected evidence source profiles."""

from dataclasses import dataclass, field

from core.secrets.mariadb_continuity_evidence_source_profile import (
    MariaDBContinuityEvidenceSourceProfileContract,
    canonical_mariadb_continuity_evidence_source_profile_contract,
)


@dataclass(frozen=True, slots=True)
class MariaDBContinuityEvidenceSourceProfileSource:
    contract: MariaDBContinuityEvidenceSourceProfileContract = field(
        default_factory=canonical_mariadb_continuity_evidence_source_profile_contract,
        init=False,
    )
    frozen: bool = field(default=True, init=False)
    slotted: bool = field(default=True, init=False)
    repository_only: bool = field(default=True, init=False)
    zero_io: bool = field(default=True, init=False)
    zero_authority: bool = field(default=True, init=False)
    mac_aicontrolcenter_sole_control_plane: bool = field(default=True, init=False)
    ubuntu_stateless_infrastructure_worker: bool = field(default=True, init=False)
    ubuntu_control_plane_authority: bool = field(default=False, init=False)
    path_resolver_exposed: bool = field(default=False, init=False)
    filesystem_io_performed: bool = field(default=False, init=False)
    metadata_inspection_performed: bool = field(default=False, init=False)
    source_resolution_performed: bool = field(default=False, init=False)
    content_acquisition_performed: bool = field(default=False, init=False)
    evidence_admission_performed: bool = field(default=False, init=False)
    evidence_verification_performed: bool = field(default=False, init=False)
    network_performed: bool = field(default=False, init=False)
    process_performed: bool = field(default=False, init=False)
    sql_performed: bool = field(default=False, init=False)
    production_access_performed: bool = field(default=False, init=False)
    runtime_mutation_performed: bool = field(default=False, init=False)


def canonical_mariadb_continuity_evidence_source_profile_source(
) -> MariaDBContinuityEvidenceSourceProfileSource:
    return MariaDBContinuityEvidenceSourceProfileSource()
