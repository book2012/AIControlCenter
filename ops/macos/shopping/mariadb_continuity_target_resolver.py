"""Fail-closed symbolic resolution for the Mac-owned MariaDB target."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SymbolicTarget(str, Enum):
    CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE = (
        "CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE"
    )


class ResolutionOwner(str, Enum):
    MAC_CONTROL_PLANE = "MAC_CONTROL_PLANE"


@dataclass(frozen=True, slots=True)
class MariaDBContinuityTargetResolution:
    target: SymbolicTarget = field(
        default=SymbolicTarget.CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE,
        init=False,
    )
    owner: ResolutionOwner = field(default=ResolutionOwner.MAC_CONTROL_PLANE, init=False)
    numeric_loopback_port_assigned: bool = field(default=False, init=False)
    target_deployed: bool = field(default=False, init=False)

    @property
    def production_target_ready(self) -> bool:
        return self.numeric_loopback_port_assigned and self.target_deployed

    def to_projection(self) -> dict[str, Any]:
        return {
            "target": self.target.value,
            "owner": self.owner.value,
            "numeric_loopback_port_assigned": self.numeric_loopback_port_assigned,
            "target_deployed": self.target_deployed,
            "production_target_ready": self.production_target_ready,
            "authorization_authority": False,
            "capability_authority": False,
            "execution_authority": False,
            "mutation_authority": False,
            "retry_authority": False,
            "reconnect_authority": False,
            "rollback_authority": False,
            "value_free": True,
        }


def resolve_canonical_target() -> MariaDBContinuityTargetResolution:
    return MariaDBContinuityTargetResolution()
