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
    protected_parent_required: bool = field(default=True, init=False)
    trusted_uid_gid_required: bool = field(default=True, init=False)
    fd_inode_binding_future_requirement: bool = field(default=True, init=False)
    one_value_acquisition_maximum: bool = field(default=True, init=False)
    acquisition_after_capability_consumption_required: bool = field(default=True, init=False)
    canonical_credential_available: bool = field(default=False, init=False)

    @property
    def ready(self) -> bool:
        return self.canonical_credential_available

    def to_projection(self) -> dict[str, Any]:
        return {
            "slot": self.slot.value,
            "owner": self.owner.value,
            "fixed_authoritative_slot_required": self.fixed_authoritative_slot_required,
            "protected_parent_required": self.protected_parent_required,
            "trusted_uid_gid_required": self.trusted_uid_gid_required,
            "fd_inode_binding_future_requirement": self.fd_inode_binding_future_requirement,
            "one_value_acquisition_maximum": self.one_value_acquisition_maximum,
            "acquisition_after_capability_consumption_required": self.acquisition_after_capability_consumption_required,
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
