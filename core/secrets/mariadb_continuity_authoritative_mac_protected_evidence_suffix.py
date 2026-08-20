"""Closed repository policy for the authoritative Mac evidence suffix."""

from dataclasses import dataclass, field, fields
from enum import Enum

from core.secrets.mariadb_continuity_evidence_attestation_reference import (
    RecoverEvidenceGate,
    SemanticsChangeRequired,
)
from core.secrets.mariadb_continuity_evidence_source_profile import (
    OfflineAcquisitionAssessment,
)


class AuthoritativeMacProtectedEvidenceSuffixPolicyIdentity(str, Enum):
    """The sole suffix-policy identity; it is not a base or concrete path."""

    AUTHORITATIVE_MAC_PROTECTED_EVIDENCE_SUFFIX_POLICY = (
        "AUTHORITATIVE_MAC_PROTECTED_EVIDENCE_SUFFIX_POLICY"
    )


EXACT_PROTECTED_EVIDENCE_SUFFIX = (
    "Library/Application Support/AIControlCenter/"
    "protected-external-evidence/mariadb-continuity"
)


@dataclass(frozen=True, slots=True, init=False)
class AuthoritativeMacProtectedEvidenceSuffixPolicy:
    """Repository-owned relative suffix without runtime path resolution."""

    identity: AuthoritativeMacProtectedEvidenceSuffixPolicyIdentity = field(init=False)
    suffix: str = field(init=False)
    frozen: bool = field(default=True, init=False)
    slotted: bool = field(default=True, init=False)
    repository_owned: bool = field(default=True, init=False)
    mac_control_plane_owned: bool = field(default=True, init=False)
    fail_closed: bool = field(default=True, init=False)
    zero_authority: bool = field(default=True, init=False)
    exact_suffix_policy_layer_required: bool = field(default=True, init=False)
    exact_suffix_policy_evidence_established_by_architecture_decision: bool = field(default=True, init=False)
    exact_suffix_value_established: bool = field(default=True, init=False)
    suffix_is_relative_to_trusted_account_home: bool = field(default=True, init=False)
    absolute_path_established: bool = field(default=False, init=False)
    concrete_path_value_established: bool = field(default=False, init=False)
    runtime_home_resolver_available: bool = field(default=False, init=False)
    authoritative_base_location_already_exists: bool = field(default=False, init=False)
    source_existence_established: bool = field(default=False, init=False)
    historical_evidence_existence_established: bool = field(default=False, init=False)
    metadata_inspection_performed: bool = field(default=False, init=False)
    source_metadata_safe: bool = field(default=False, init=False)
    content_acquisition_performed: bool = field(default=False, init=False)
    evidence_admitted: bool = field(default=False, init=False)
    evidence_verified: bool = field(default=False, init=False)
    recover_evidence_sufficient: bool = field(default=False, init=False)
    offline_acquisition_possible: OfflineAcquisitionAssessment = field(
        default=OfflineAcquisitionAssessment.UNKNOWN, init=False
    )
    production_access_currently_justified: bool = field(default=False, init=False)
    production_validation_ready: bool = field(default=False, init=False)
    shopping_runtime_activated: bool = field(default=False, init=False)
    caller_suffix_selection_allowed: bool = field(default=False, init=False)
    caller_base_path_selection_allowed: bool = field(default=False, init=False)
    caller_home_selection_allowed: bool = field(default=False, init=False)
    caller_absolute_path_selection_allowed: bool = field(default=False, init=False)
    caller_concrete_path_selection_allowed: bool = field(default=False, init=False)
    filesystem_io_allowed: bool = field(default=False, init=False)
    authorization_authority: bool = field(default=False, init=False)
    capability_authority: bool = field(default=False, init=False)
    execution_authority: bool = field(default=False, init=False)
    mutation_authority: bool = field(default=False, init=False)
    retry_authority: bool = field(default=False, init=False)
    reconnect_authority: bool = field(default=False, init=False)
    rollback_authority: bool = field(default=False, init=False)
    acquisition_authority: bool = field(default=False, init=False)
    admission_authority: bool = field(default=False, init=False)
    verification_authority: bool = field(default=False, init=False)
    production_access_allowed: bool = field(default=False, init=False)
    protected_source_access_allowed: bool = field(default=False, init=False)
    ubuntu_access_allowed: bool = field(default=False, init=False)
    governance_core_coupled: bool = field(default=False, init=False)
    sec_02_coupled: bool = field(default=False, init=False)
    controlled_execution_port_coupled: bool = field(default=False, init=False)
    legacy_caller_path_observer_reachable: bool = field(default=False, init=False)
    recover_evidence_gate: RecoverEvidenceGate = field(
        default=RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT, init=False
    )
    sm_01b_02d_06_semantics_change_required: SemanticsChangeRequired = field(
        default=SemanticsChangeRequired.NO, init=False
    )

    def __init__(self) -> None:
        raise TypeError(
            "AuthoritativeMacProtectedEvidenceSuffixPolicy is constructed only "
            "by canonical repository policy"
        )


def canonical_authoritative_mac_protected_evidence_suffix_policy(
) -> AuthoritativeMacProtectedEvidenceSuffixPolicy:
    policy = object.__new__(AuthoritativeMacProtectedEvidenceSuffixPolicy)
    object.__setattr__(
        policy,
        "identity",
        AuthoritativeMacProtectedEvidenceSuffixPolicyIdentity.AUTHORITATIVE_MAC_PROTECTED_EVIDENCE_SUFFIX_POLICY,
    )
    object.__setattr__(policy, "suffix", EXACT_PROTECTED_EVIDENCE_SUFFIX)
    for policy_field in fields(AuthoritativeMacProtectedEvidenceSuffixPolicy):
        if policy_field.name not in {"identity", "suffix"}:
            object.__setattr__(policy, policy_field.name, policy_field.default)
    return policy
