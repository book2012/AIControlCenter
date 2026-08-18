"""Symbolic source for a future historical data-identity baseline."""

from dataclasses import dataclass, field
from typing import Any

from core.secrets.mariadb_continuity_sources import DataIdentityCategory


@dataclass(frozen=True, slots=True)
class DataIdentitySource:
    fact_categories: tuple[DataIdentityCategory, ...] = field(
        default=tuple(DataIdentityCategory), init=False
    )
    historical_data_identity_baseline_available: bool = field(default=False, init=False)

    @property
    def ready(self) -> bool:
        return self.historical_data_identity_baseline_available

    def to_projection(self) -> dict[str, Any]:
        return {
            "fact_categories": tuple(item.value for item in self.fact_categories),
            "historical_data_identity_baseline_available": self.historical_data_identity_baseline_available,
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


def canonical_data_identity_source() -> DataIdentitySource:
    return DataIdentitySource()
