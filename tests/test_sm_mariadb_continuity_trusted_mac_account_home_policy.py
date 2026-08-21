import inspect
from dataclasses import FrozenInstanceError, fields

import pytest

from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    RecoverEvidenceGate,
    SemanticsChangeRequired,
)
from core.secrets.mariadb_continuity_evidence_source_profile import (
    OfflineAcquisitionAssessment,
)
from core.secrets.mariadb_continuity_trusted_mac_account_home_policy import (
    AccountHomeLookupRule,
    AccountIdentityBinding,
    AuthoritativeRemainingRange,
    EffectiveUidSource,
    MacPlatformRequirement,
    RealUidSource,
    TrustedMacAccountHomePolicy,
    TrustedMacAccountHomePolicyIdentity,
    WorkUnitStatus,
    canonical_trusted_mac_account_home_policy,
)


def test_closed_policy_identity_and_symbolic_darwin_account_rules_are_exact():
    policy = canonical_trusted_mac_account_home_policy()
    assert tuple(TrustedMacAccountHomePolicyIdentity) == (
        TrustedMacAccountHomePolicyIdentity.TRUSTED_MAC_ACCOUNT_HOME_POLICY,
    )
    assert policy.platform_requirement is MacPlatformRequirement.DARWIN
    assert policy.platform_requirement.value == "Darwin"
    assert not policy.root_account_allowed
    assert policy.real_uid_source is RealUidSource.OS_GETUID
    assert policy.real_uid_source.value == "os.getuid()"
    assert policy.effective_uid_source is EffectiveUidSource.OS_GETEUID
    assert policy.effective_uid_source.value == "os.geteuid()"
    assert policy.uid_equivalence_required
    assert policy.account_identity_binding is AccountIdentityBinding.REAL_UID_EQUALS_EFFECTIVE_UID
    assert policy.account_home_lookup_rule is AccountHomeLookupRule.PASSWD_BOUND_UID_HOME
    assert policy.account_home_lookup_rule.value == "pwd.getpwuid(bound_uid).pw_dir"


def test_policy_is_zero_argument_nonconstructible_frozen_and_caller_unselectable():
    factory = canonical_trusted_mac_account_home_policy
    assert not inspect.signature(factory).parameters
    with pytest.raises(TypeError):
        TrustedMacAccountHomePolicy()
    policy = factory()
    assert all(item.init is False for item in fields(policy))
    with pytest.raises(FrozenInstanceError):
        policy.root_account_allowed = True
    with pytest.raises(TypeError):
        factory(home="caller-value")


def test_runtime_resolution_values_io_and_rejected_authorities_remain_closed():
    policy = canonical_trusted_mac_account_home_policy()
    assert all((policy.frozen, policy.slotted, policy.repository_owned, policy.mac_control_plane_owned, policy.fail_closed, policy.zero_authority))
    assert not any((policy.runtime_home_resolver_available, policy.trusted_home_value_established, policy.absolute_path_established, policy.concrete_path_value_established, policy.filesystem_io_performed, policy.protected_source_access_performed, policy.production_access_performed, policy.recover_evidence_sufficient))
    assert not any((policy.home_environment_authority_allowed, policy.path_home_authority_allowed, policy.expanduser_authority_allowed, policy.caller_home_authority_allowed, policy.caller_path_authority_allowed, policy.argv_home_authority_allowed, policy.argv_path_authority_allowed, policy.fallback_allowed, policy.enumeration_allowed, policy.candidate_iteration_allowed))
    assert policy.offline_acquisition_possible is OfflineAcquisitionAssessment.UNKNOWN
    assert policy.recover_evidence_gate is RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT


def test_zero_authority_separation_and_work_unit_facts_are_preserved():
    policy = canonical_trusted_mac_account_home_policy()
    assert not any((policy.authorization_authority, policy.capability_authority, policy.execution_authority, policy.mutation_authority, policy.acquisition_authority, policy.admission_authority, policy.verification_authority, policy.production_access_allowed, policy.protected_source_access_allowed, policy.ubuntu_access_allowed, policy.ubuntu_control_plane_authority, policy.governance_core_coupled, policy.sec_02_coupled, policy.controlled_execution_port_coupled))
    assert policy.sm_01b_02d_06_semantics_change_required is SemanticsChangeRequired.NO
    assert policy.macro_wu_06 is WorkUnitStatus.IN_PROGRESS
    assert policy.remaining_authoritative_macro_wus == 7
    assert policy.authoritative_remaining_range is AuthoritativeRemainingRange.WU06_WU12
