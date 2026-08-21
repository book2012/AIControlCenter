"""Inert Mac projection of the trusted account-home repository policy."""

from dataclasses import dataclass, field

from core.secrets.mariadb_continuity_trusted_mac_account_home_policy import (
    TrustedMacAccountHomePolicy,
    canonical_trusted_mac_account_home_policy,
)


@dataclass(frozen=True, slots=True)
class MariaDBContinuityTrustedMacAccountHomePolicySource:
    policy: TrustedMacAccountHomePolicy = field(
        default_factory=canonical_trusted_mac_account_home_policy,
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
    account_lookup_exposed: bool = field(default=False, init=False)
    path_resolver_exposed: bool = field(default=False, init=False)
    home_resolver_exposed: bool = field(default=False, init=False)
    filesystem_adapter_exposed: bool = field(default=False, init=False)
    protected_source_adapter_exposed: bool = field(default=False, init=False)
    production_adapter_exposed: bool = field(default=False, init=False)
    authority_bearing_capability_exposed: bool = field(default=False, init=False)
    filesystem_io_performed: bool = field(default=False, init=False)
    protected_source_access_performed: bool = field(default=False, init=False)
    production_access_performed: bool = field(default=False, init=False)


def canonical_mariadb_continuity_trusted_mac_account_home_policy_source(
) -> MariaDBContinuityTrustedMacAccountHomePolicySource:
    return MariaDBContinuityTrustedMacAccountHomePolicySource()
