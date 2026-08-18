"""Closed symbolic credential-slot resolver owned by the Mac Control Plane."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CredentialSlot(str, Enum):
    FIXED_AUTHORITATIVE_PRODUCTION_SLOT = "FIXED_AUTHORITATIVE_PRODUCTION_SLOT"


class ResolverOwner(str, Enum):
    MAC_CONTROL_PLANE = "MAC_CONTROL_PLANE"


@dataclass(frozen=True, slots=True)
class CredentialSlotResolution:
    slot: CredentialSlot = field(default=CredentialSlot.FIXED_AUTHORITATIVE_PRODUCTION_SLOT, init=False)
    owner: ResolverOwner = field(default=ResolverOwner.MAC_CONTROL_PLANE, init=False)
    fixed_authoritative_slot_required: bool = field(default=True, init=False)
    fixed_closed_source_required: bool = field(default=True, init=False)
    protected_parent_required: bool = field(default=True, init=False)
    protected_parent_exact_mode_0700_required: bool = field(default=True, init=False)
    regular_non_symlink_leaf_required: bool = field(default=True, init=False)
    leaf_permissions_no_broader_than_0600_required: bool = field(default=True, init=False)
    trusted_uid_gid_required: bool = field(default=True, init=False)
    fd_inode_binding_future_requirement: bool = field(default=True, init=False)
    one_value_acquisition_maximum: bool = field(default=True, init=False)
    maximum_acquisitions_per_authorization: int = field(default=1, init=False)
    acquisition_after_capability_consumption_required: bool = field(default=True, init=False)
    fallback_forbidden: bool = field(default=True, init=False)
    enumeration_forbidden: bool = field(default=True, init=False)
    candidate_iteration_forbidden: bool = field(default=True, init=False)
    environment_or_home_authority_forbidden: bool = field(default=True, init=False)
    secret_value_in_argv_forbidden: bool = field(default=True, init=False)
    secret_value_in_json_forbidden: bool = field(default=True, init=False)
    secret_value_in_logs_forbidden: bool = field(default=True, init=False)
    secret_value_hashing_forbidden: bool = field(default=True, init=False)
    canonical_credential_available: bool = field(default=False, init=False)

    @property
    def ready(self) -> bool:
        return self.canonical_credential_available

    def to_projection(self) -> dict[str, Any]:
        return {
            "slot": self.slot.value,
            "owner": self.owner.value,
            "fixed_authoritative_slot_required": self.fixed_authoritative_slot_required,
            "fixed_closed_source_required": self.fixed_closed_source_required,
            "protected_parent_required": self.protected_parent_required,
            "protected_parent_exact_mode_0700_required": self.protected_parent_exact_mode_0700_required,
            "regular_non_symlink_leaf_required": self.regular_non_symlink_leaf_required,
            "leaf_permissions_no_broader_than_0600_required": self.leaf_permissions_no_broader_than_0600_required,
            "trusted_uid_gid_required": self.trusted_uid_gid_required,
            "fd_inode_binding_future_requirement": self.fd_inode_binding_future_requirement,
            "one_value_acquisition_maximum": self.one_value_acquisition_maximum,
            "maximum_acquisitions_per_authorization": self.maximum_acquisitions_per_authorization,
            "acquisition_after_capability_consumption_required": self.acquisition_after_capability_consumption_required,
            "fallback_forbidden": self.fallback_forbidden,
            "enumeration_forbidden": self.enumeration_forbidden,
            "candidate_iteration_forbidden": self.candidate_iteration_forbidden,
            "environment_or_home_authority_forbidden": self.environment_or_home_authority_forbidden,
            "secret_value_in_argv_forbidden": self.secret_value_in_argv_forbidden,
            "secret_value_in_json_forbidden": self.secret_value_in_json_forbidden,
            "secret_value_in_logs_forbidden": self.secret_value_in_logs_forbidden,
            "secret_value_hashing_forbidden": self.secret_value_hashing_forbidden,
            "canonical_credential_available": self.canonical_credential_available,
            "ready": self.ready,
            "authorization_authority": False,
            "capability_authority": False,
            "execution_authority": False,
            "mutation_authority": False,
            "retry_authority": False,
            "reconnect_authority": False,
            "rollback_authority": False,
            "value_free": True,
        }


def canonical_credential_slot_resolution() -> CredentialSlotResolution:
    return CredentialSlotResolution()
