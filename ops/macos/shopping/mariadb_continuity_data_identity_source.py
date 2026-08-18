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
    independently_established_historical_source_required: bool = field(default=True, init=False)
    provenance_required: bool = field(default=True, init=False)
    immutable_identity_required: bool = field(default=True, init=False)
    timestamp_required: bool = field(default=True, init=False)
    trusted_issuer_required: bool = field(default=True, init=False)
    baseline_binding_required: bool = field(default=True, init=False)
    complete_five_category_coverage_required: bool = field(default=True, init=False)
    infrastructure_names_alone_sufficient: bool = field(default=False, init=False)

    @property
    def ready(self) -> bool:
        return self.historical_data_identity_baseline_available

    def to_projection(self) -> dict[str, Any]:
        return {
            "fact_categories": tuple(item.value for item in self.fact_categories),
            "historical_data_identity_baseline_available": self.historical_data_identity_baseline_available,
            "independently_established_historical_source_required": self.independently_established_historical_source_required,
            "provenance_required": self.provenance_required,
            "immutable_identity_required": self.immutable_identity_required,
            "timestamp_required": self.timestamp_required,
            "trusted_issuer_required": self.trusted_issuer_required,
            "baseline_binding_required": self.baseline_binding_required,
            "complete_five_category_coverage_required": self.complete_five_category_coverage_required,
            "infrastructure_names_alone_sufficient": self.infrastructure_names_alone_sufficient,
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
