"""Value-free readiness facts for future MariaDB continuity validation."""

from dataclasses import dataclass, fields
from enum import Enum
from typing import Any


class InspectionMode(str, Enum):
    READ_ONLY = "READ_ONLY"


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
