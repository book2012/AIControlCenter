"""Closed repository policy for a future trusted Mac account-home lookup."""

from dataclasses import dataclass, field, fields
from enum import Enum

from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    RecoverEvidenceGate,
    SemanticsChangeRequired,
)
from core.secrets.mariadb_continuity_evidence_source_profile import (
    OfflineAcquisitionAssessment,
)


class TrustedMacAccountHomePolicyIdentity(str, Enum):
    """The sole policy identity; it is not an account, home, or path."""

    TRUSTED_MAC_ACCOUNT_HOME_POLICY = "TRUSTED_MAC_ACCOUNT_HOME_POLICY"


class MacPlatformRequirement(str, Enum):
    DARWIN = "Darwin"


class RealUidSource(str, Enum):
    OS_GETUID = "os.getuid()"


class EffectiveUidSource(str, Enum):
    OS_GETEUID = "os.geteuid()"


class AccountIdentityBinding(str, Enum):
    REAL_UID_EQUALS_EFFECTIVE_UID = "REAL_UID_EQUALS_EFFECTIVE_UID"


class AccountHomeLookupRule(str, Enum):
    PASSWD_BOUND_UID_HOME = "pwd.getpwuid(bound_uid).pw_dir"


class WorkUnitStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"


class AuthoritativeRemainingRange(str, Enum):
    WU06_WU12 = "WU06-WU12"


@dataclass(frozen=True, slots=True, init=False)
class TrustedMacAccountHomePolicy:
    """Symbolic account-home policy without runtime lookup or path values."""

    identity: TrustedMacAccountHomePolicyIdentity = field(init=False)
    platform_requirement: MacPlatformRequirement = field(init=False)
    real_uid_source: RealUidSource = field(init=False)
    effective_uid_source: EffectiveUidSource = field(init=False)
    account_identity_binding: AccountIdentityBinding = field(init=False)
    account_home_lookup_rule: AccountHomeLookupRule = field(init=False)
    frozen: bool = field(default=True, init=False)
    slotted: bool = field(default=True, init=False)
    repository_owned: bool = field(default=True, init=False)
    mac_control_plane_owned: bool = field(default=True, init=False)
    fail_closed: bool = field(default=True, init=False)
    zero_authority: bool = field(default=True, init=False)
    trusted_account_home_policy_layer_required: bool = field(default=True, init=False)
    trusted_account_home_architecture_evidence_sufficient_to_freeze: bool = field(
        default=True, init=False
    )
    root_account_allowed: bool = field(default=False, init=False)
    uid_equivalence_required: bool = field(default=True, init=False)
    runtime_home_resolver_available: bool = field(default=False, init=False)
    trusted_home_value_established: bool = field(default=False, init=False)
    absolute_path_established: bool = field(default=False, init=False)
    concrete_path_value_established: bool = field(default=False, init=False)
    filesystem_io_performed: bool = field(default=False, init=False)
    protected_source_access_performed: bool = field(default=False, init=False)
    production_access_performed: bool = field(default=False, init=False)
    recover_evidence_sufficient: bool = field(default=False, init=False)
    offline_acquisition_possible: OfflineAcquisitionAssessment = field(
        default=OfflineAcquisitionAssessment.UNKNOWN, init=False
    )
    home_environment_authority_allowed: bool = field(default=False, init=False)
    path_home_authority_allowed: bool = field(default=False, init=False)
    expanduser_authority_allowed: bool = field(default=False, init=False)
    caller_home_authority_allowed: bool = field(default=False, init=False)
    caller_path_authority_allowed: bool = field(default=False, init=False)
    argv_home_authority_allowed: bool = field(default=False, init=False)
    argv_path_authority_allowed: bool = field(default=False, init=False)
    fallback_allowed: bool = field(default=False, init=False)
    enumeration_allowed: bool = field(default=False, init=False)
    candidate_iteration_allowed: bool = field(default=False, init=False)
    authorization_authority: bool = field(default=False, init=False)
    capability_authority: bool = field(default=False, init=False)
    execution_authority: bool = field(default=False, init=False)
    mutation_authority: bool = field(default=False, init=False)
    acquisition_authority: bool = field(default=False, init=False)
    admission_authority: bool = field(default=False, init=False)
    verification_authority: bool = field(default=False, init=False)
    production_access_allowed: bool = field(default=False, init=False)
    protected_source_access_allowed: bool = field(default=False, init=False)
    ubuntu_access_allowed: bool = field(default=False, init=False)
    ubuntu_control_plane_authority: bool = field(default=False, init=False)
    governance_core_coupled: bool = field(default=False, init=False)
    sec_02_coupled: bool = field(default=False, init=False)
    controlled_execution_port_coupled: bool = field(default=False, init=False)
    recover_evidence_gate: RecoverEvidenceGate = field(
        default=RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT, init=False
    )
    sm_01b_02d_06_semantics_change_required: SemanticsChangeRequired = field(
        default=SemanticsChangeRequired.NO, init=False
    )
    macro_wu_06: WorkUnitStatus = field(default=WorkUnitStatus.IN_PROGRESS, init=False)
    remaining_authoritative_macro_wus: int = field(default=7, init=False)
    authoritative_remaining_range: AuthoritativeRemainingRange = field(
        default=AuthoritativeRemainingRange.WU06_WU12, init=False
    )

    def __init__(self) -> None:
        raise TypeError(
            "TrustedMacAccountHomePolicy is constructed only by canonical "
            "repository policy"
        )


def canonical_trusted_mac_account_home_policy() -> TrustedMacAccountHomePolicy:
    policy = object.__new__(TrustedMacAccountHomePolicy)
    symbolic_facts = {
        "identity": TrustedMacAccountHomePolicyIdentity.TRUSTED_MAC_ACCOUNT_HOME_POLICY,
        "platform_requirement": MacPlatformRequirement.DARWIN,
        "real_uid_source": RealUidSource.OS_GETUID,
        "effective_uid_source": EffectiveUidSource.OS_GETEUID,
        "account_identity_binding": AccountIdentityBinding.REAL_UID_EQUALS_EFFECTIVE_UID,
        "account_home_lookup_rule": AccountHomeLookupRule.PASSWD_BOUND_UID_HOME,
    }
    for policy_field in fields(TrustedMacAccountHomePolicy):
        value = symbolic_facts.get(policy_field.name, policy_field.default)
        object.__setattr__(policy, policy_field.name, value)
    return policy
