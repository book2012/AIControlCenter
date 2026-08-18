"""Value-free readiness facts for future MariaDB continuity validation."""

from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any


class InspectionMode(str, Enum):
    READ_ONLY = "READ_ONLY"


class ProductionBoundary(str, Enum):
    MARIADB_LOOPBACK_PORT_DEPLOYMENT = "MARIADB_LOOPBACK_PORT_DEPLOYMENT"
    MARIADB_CREDENTIAL_SLOT_PROVISIONING = "MARIADB_CREDENTIAL_SLOT_PROVISIONING"
    MARIADB_CONTINUITY_VALIDATION = "MARIADB_CONTINUITY_VALIDATION"


@dataclass(frozen=True, slots=True)
class MariaDBContinuityPrerequisites:
    """Factual prerequisites only; this object grants no authority."""

    authorization_composition_defined: bool
    credential_source_contract_defined: bool
    credential_material_available: bool
    canonical_network_target_defined: bool
    canonical_network_target_deployed: bool
    expected_identity_source_defined: bool
    data_identity_baseline_available: bool
    data_continuity_baseline_available: bool
    driver_available: bool

    def __post_init__(self) -> None:
        for item in fields(self):
            if type(getattr(self, item.name)) is not bool:
                raise TypeError(f"{item.name} must be bool")

    @classmethod
    def phase_a(cls) -> "MariaDBContinuityPrerequisites":
        return cls(
            authorization_composition_defined=True,
            credential_source_contract_defined=True,
            credential_material_available=False,
            canonical_network_target_defined=False,
            canonical_network_target_deployed=False,
            expected_identity_source_defined=True,
            data_identity_baseline_available=False,
            data_continuity_baseline_available=False,
            driver_available=False,
        )

    @property
    def production_validation_ready(self) -> bool:
        return all(getattr(self, item.name) for item in fields(self))

    def to_projection(self) -> dict[str, Any]:
        projection: dict[str, Any] = {
            "schema_version": "1.0",
            "inspection": InspectionMode.READ_ONLY.value,
        }
        projection.update(
            (item.name, getattr(self, item.name)) for item in fields(self)
        )
        projection.update(
            production_validation_ready=self.production_validation_ready,
            mutation_authority=False,
            authorization_authority=False,
            execution_authority=False,
            retry_authority=False,
            secret_values_read=False,
            production_access_performed=False,
            value_free=True,
        )
        return projection


def canonical_phase_a_prerequisites() -> MariaDBContinuityPrerequisites:
    return MariaDBContinuityPrerequisites.phase_a()


@dataclass(frozen=True, slots=True)
class ProductionBoundaryFacts:
    boundaries: tuple[ProductionBoundary, ...] = field(default=tuple(ProductionBoundary), init=False)
    loopback_port_deployment_separate_production_mutation: bool = field(default=True, init=False)
    credential_slot_provisioning_separate_production_mutation: bool = field(default=True, init=False)
    continuity_validation_separate_read_only_production_access_boundary: bool = field(default=True, init=False)
    fresh_human_authorization_required_for_each_boundary: bool = field(default=True, init=False)
    continuity_validation_mutation_budget: int = field(default=0, init=False)
    maximum_connection_auth_attempts: int = field(default=1, init=False)
    production_authorization_reuse_allowed: bool = field(default=False, init=False)

    def to_projection(self) -> dict[str, Any]:
        return {
            "boundaries": tuple(item.value for item in self.boundaries),
            "loopback_port_deployment_separate_production_mutation": self.loopback_port_deployment_separate_production_mutation,
            "credential_slot_provisioning_separate_production_mutation": self.credential_slot_provisioning_separate_production_mutation,
            "continuity_validation_separate_read_only_production_access_boundary": self.continuity_validation_separate_read_only_production_access_boundary,
            "fresh_human_authorization_required_for_each_boundary": self.fresh_human_authorization_required_for_each_boundary,
            "continuity_validation_mutation_budget": self.continuity_validation_mutation_budget,
            "maximum_connection_auth_attempts": self.maximum_connection_auth_attempts,
            "production_authorization_reuse_allowed": self.production_authorization_reuse_allowed,
            "authorization_authority": False,
            "capability_authority": False,
            "execution_authority": False,
            "mutation_authority": False,
            "retry_authority": False,
            "reconnect_authority": False,
            "rollback_authority": False,
            "value_free": True,
        }


def canonical_production_boundary_facts() -> ProductionBoundaryFacts:
    return ProductionBoundaryFacts()
