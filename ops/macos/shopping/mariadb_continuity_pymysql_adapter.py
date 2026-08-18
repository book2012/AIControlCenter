"""Value-free contract for a future injected PyMySQL one-shot seam."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from core.secrets.mariadb_continuity_observations import (
    MariaDBContinuityRuntimeObservation,
)


DRIVER_FAMILY = "PYMYSQL"
DRIVER_VERSION = "1.2.0"
DRIVER_MODE = "SYNCHRONOUS_ONE_SHOT"
AUTH_PLUGIN_STATE = "UNRESOLVED"


class FixedValidationOperation(str, Enum):
    CLOSED_MARIADB_CONTINUITY_VALIDATION = "CLOSED_MARIADB_CONTINUITY_VALIDATION"


class InjectedOneShotDriverSeam(Protocol):
    def observe_once(
        self, operation: FixedValidationOperation
    ) -> MariaDBContinuityRuntimeObservation:
        ...


@dataclass(frozen=True, slots=True)
class PyMySQLDriverReadiness:
    driver_family: str = field(default=DRIVER_FAMILY, init=False)
    driver_version: str = field(default=DRIVER_VERSION, init=False)
    driver_mode: str = field(default=DRIVER_MODE, init=False)
    auth_plugin_state: str = field(default=AUTH_PLUGIN_STATE, init=False)
    maximum_future_connection_count_per_authorization: int = field(default=1, init=False)
    dependency_declared: bool = field(default=True, init=False)
    driver_installed: bool = field(default=False, init=False)
    driver_imported: bool = field(default=False, init=False)
    pymysql_compatibility_established: bool = field(default=False, init=False)

    @property
    def ready(self) -> bool:
        return bool(
            self.driver_installed
            and self.driver_imported
            and self.pymysql_compatibility_established
            and self.auth_plugin_state != "UNRESOLVED"
        )

    def to_projection(self) -> dict[str, Any]:
        return {
            "driver_family": self.driver_family,
            "driver_version": self.driver_version,
            "driver_mode": self.driver_mode,
            "auth_plugin_state": self.auth_plugin_state,
            "maximum_future_connection_count_per_authorization": self.maximum_future_connection_count_per_authorization,
            "dependency_declared": self.dependency_declared,
            "driver_installed": self.driver_installed,
            "driver_imported": self.driver_imported,
            "pymysql_compatibility_established": self.pymysql_compatibility_established,
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


def canonical_driver_readiness() -> PyMySQLDriverReadiness:
    return PyMySQLDriverReadiness()
