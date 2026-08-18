"""Closed symbolic contract for future Mac-owned target resolution."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TargetProfile(str, Enum):
    CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE = (
        "CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE"
    )


class TargetResolutionOwner(str, Enum):
    MAC_CONTROL_PLANE = "MAC_CONTROL_PLANE"


@dataclass(frozen=True, slots=True)
class MariaDBContinuityTargetContract:
    target_profile: TargetProfile = (
        field(
            default=TargetProfile.CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE,
            init=False,
        )
    )
    target_resolution_owner: TargetResolutionOwner = (
        field(default=TargetResolutionOwner.MAC_CONTROL_PLANE, init=False)
    )
    canonical_target_contract_defined: bool = field(default=True, init=False)
    numeric_loopback_port_assigned: bool = field(default=False, init=False)
    target_deployed: bool = field(default=False, init=False)

    @property
    def production_target_ready(self) -> bool:
        return bool(self.numeric_loopback_port_assigned and self.target_deployed)

    def to_projection(self) -> dict[str, Any]:
        return {
            "target_profile": self.target_profile.value,
            "target_resolution_owner": self.target_resolution_owner.value,
            "canonical_target_contract_defined": self.canonical_target_contract_defined,
            "numeric_loopback_port_assigned": self.numeric_loopback_port_assigned,
            "target_deployed": self.target_deployed,
            "production_target_ready": self.production_target_ready,
            "value_free": True,
        }


def canonical_phase_b1_target() -> MariaDBContinuityTargetContract:
    return MariaDBContinuityTargetContract()
