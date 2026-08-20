"""Inert Mac projection of the authoritative protected-evidence suffix."""

from dataclasses import dataclass, field

from core.secrets.mariadb_continuity_authoritative_mac_protected_evidence_suffix import (
    AuthoritativeMacProtectedEvidenceSuffixPolicy,
    canonical_authoritative_mac_protected_evidence_suffix_policy,
)


@dataclass(frozen=True, slots=True)
class MariaDBContinuityAuthoritativeMacProtectedEvidenceSuffixPolicySource:
    policy: AuthoritativeMacProtectedEvidenceSuffixPolicy = field(
        default_factory=canonical_authoritative_mac_protected_evidence_suffix_policy,
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
    home_resolver_exposed: bool = field(default=False, init=False)
    filesystem_adapter_exposed: bool = field(default=False, init=False)
    metadata_inspector_exposed: bool = field(default=False, init=False)
    content_reader_exposed: bool = field(default=False, init=False)
    production_adapter_exposed: bool = field(default=False, init=False)
    authority_bearing_capability_exposed: bool = field(default=False, init=False)
    filesystem_io_performed: bool = field(default=False, init=False)
    protected_source_access_performed: bool = field(default=False, init=False)
    production_access_performed: bool = field(default=False, init=False)


def canonical_mariadb_continuity_authoritative_mac_protected_evidence_suffix_policy_source(
) -> MariaDBContinuityAuthoritativeMacProtectedEvidenceSuffixPolicySource:
    return MariaDBContinuityAuthoritativeMacProtectedEvidenceSuffixPolicySource()
