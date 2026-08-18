"""Value-free expected-identity descriptor source boundary."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IdentityDescriptorCategory(str, Enum):
    EXPECTED_DATABASE_IDENTITY = "EXPECTED_DATABASE_IDENTITY"
    EXPECTED_ACCOUNT_IDENTITY = "EXPECTED_ACCOUNT_IDENTITY"
    REQUIRED_GRANTS_PROFILE = "REQUIRED_GRANTS_PROFILE"


class DescriptorOwner(str, Enum):
    MAC_CONTROL_PLANE = "MAC_CONTROL_PLANE"


@dataclass(frozen=True, slots=True)
class IdentityDescriptorSource:
    owner: DescriptorOwner = field(default=DescriptorOwner.MAC_CONTROL_PLANE, init=False)
    categories: tuple[IdentityDescriptorCategory, ...] = field(default=tuple(IdentityDescriptorCategory), init=False)
    value_free: bool = field(default=True, init=False)
    independent_from_credential_evidence: bool = field(default=True, init=False)
    independent_from_compose_container_volume_identity_alone: bool = field(default=True, init=False)
    versionable_closed_profile_required: bool = field(default=True, init=False)
    fail_closed_when_unavailable: bool = field(default=True, init=False)
    expected_database_identity_available: bool = field(default=False, init=False)
    expected_account_identity_available: bool = field(default=False, init=False)
    required_grants_profile_available: bool = field(default=False, init=False)

    @property
    def ready(self) -> bool:
        return all((self.expected_database_identity_available, self.expected_account_identity_available, self.required_grants_profile_available))

    def to_projection(self) -> dict[str, Any]:
        return {
            "owner": self.owner.value,
            "categories": tuple(item.value for item in self.categories),
            "expected_database_identity_available": self.expected_database_identity_available,
            "expected_account_identity_available": self.expected_account_identity_available,
            "required_grants_profile_available": self.required_grants_profile_available,
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


def canonical_identity_descriptor_source() -> IdentityDescriptorSource:
    return IdentityDescriptorSource()
