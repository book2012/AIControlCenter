"""Value-free symbolic provenance source for continuity baselines."""

from dataclasses import dataclass, field
from typing import Any

from core.secrets.mariadb_continuity_sources import ContinuityEvidenceCategory


@dataclass(frozen=True, slots=True)
class LineageSource:
    evidence_categories: tuple[ContinuityEvidenceCategory, ...] = field(default=tuple(ContinuityEvidenceCategory), init=False)
    independent_historical_provenance_required: bool = field(default=True, init=False)
    immutable_artifact_identity_available: bool = field(default=False, init=False)
    source_lineage_available: bool = field(default=False, init=False)
    timestamp_metadata_available: bool = field(default=False, init=False)
    recovery_verification_available: bool = field(default=False, init=False)
    bound_to_data_identity_baseline: bool = field(default=False, init=False)
    continuity_baseline_available: bool = field(default=False, init=False)

    @property
    def mandatory_provenance_facts_available(self) -> bool:
        return all((self.immutable_artifact_identity_available, self.source_lineage_available, self.timestamp_metadata_available, self.recovery_verification_available, self.bound_to_data_identity_baseline))

    @property
    def ready(self) -> bool:
        return bool(self.continuity_baseline_available and self.mandatory_provenance_facts_available)

    def to_projection(self) -> dict[str, Any]:
        return {
            "evidence_categories": tuple(item.value for item in self.evidence_categories),
            "independent_historical_provenance_required": self.independent_historical_provenance_required,
            "immutable_artifact_identity_available": self.immutable_artifact_identity_available,
            "source_lineage_available": self.source_lineage_available,
            "timestamp_metadata_available": self.timestamp_metadata_available,
            "recovery_verification_available": self.recovery_verification_available,
            "bound_to_data_identity_baseline": self.bound_to_data_identity_baseline,
            "continuity_baseline_available": self.continuity_baseline_available,
            "mandatory_provenance_facts_available": self.mandatory_provenance_facts_available,
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


def canonical_lineage_source() -> LineageSource:
    return LineageSource()
