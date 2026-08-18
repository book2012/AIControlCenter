"""Closed, value-free descriptors for MariaDB continuity prerequisites."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.secrets.mariadb_continuity_sources import ContinuityEvidenceCategory


class DescriptorCategory(str, Enum):
    EXPECTED_DATABASE_IDENTITY = "EXPECTED_DATABASE_IDENTITY"
    EXPECTED_ACCOUNT_IDENTITY = "EXPECTED_ACCOUNT_IDENTITY"
    REQUIRED_GRANTS_PROFILE = "REQUIRED_GRANTS_PROFILE"
    DATA_IDENTITY_BASELINE = "DATA_IDENTITY_BASELINE"
    DATA_CONTINUITY_BASELINE = "DATA_CONTINUITY_BASELINE"


def _authority_projection() -> dict[str, bool]:
    return {
        "authorization_authority": False,
        "capability_authority": False,
        "execution_authority": False,
        "mutation_authority": False,
        "retry_authority": False,
        "reconnect_authority": False,
        "rollback_authority": False,
        "value_free": True,
    }


@dataclass(frozen=True, slots=True)
class DescriptorAvailability:
    """Canonical availability; B2B-1A has no authoritative values."""

    categories: tuple[DescriptorCategory, ...] = field(
        default=tuple(DescriptorCategory), init=False
    )
    available_categories: tuple[DescriptorCategory, ...] = field(
        default=(), init=False
    )

    @property
    def ready(self) -> bool:
        return self.available_categories == self.categories

    def to_projection(self) -> dict[str, Any]:
        projection: dict[str, Any] = {
            "categories": tuple(item.value for item in self.categories),
            "available_categories": (),
            "ready": self.ready,
        }
        projection.update(_authority_projection())
        return projection


@dataclass(frozen=True, slots=True)
class ContinuityMetadataFacts:
    """Conceptual provenance facts, closed to the unresolved canonical state."""

    evidence_categories: tuple[ContinuityEvidenceCategory, ...] = field(
        default=tuple(ContinuityEvidenceCategory), init=False
    )
    immutable_artifact_identity_available: bool = field(default=False, init=False)
    source_lineage_available: bool = field(default=False, init=False)
    timestamp_metadata_available: bool = field(default=False, init=False)
    recovery_verification_available: bool = field(default=False, init=False)
    bound_to_data_identity_baseline: bool = field(default=False, init=False)

    @property
    def ready(self) -> bool:
        return all(
            (
                self.immutable_artifact_identity_available,
                self.source_lineage_available,
                self.timestamp_metadata_available,
                self.recovery_verification_available,
                self.bound_to_data_identity_baseline,
            )
        )

    def to_projection(self) -> dict[str, Any]:
        projection: dict[str, Any] = {
            "evidence_categories": tuple(item.value for item in self.evidence_categories),
            "immutable_artifact_identity_available": self.immutable_artifact_identity_available,
            "source_lineage_available": self.source_lineage_available,
            "timestamp_metadata_available": self.timestamp_metadata_available,
            "recovery_verification_available": self.recovery_verification_available,
            "bound_to_data_identity_baseline": self.bound_to_data_identity_baseline,
            "ready": self.ready,
        }
        projection.update(_authority_projection())
        return projection


def canonical_descriptor_availability() -> DescriptorAvailability:
    return DescriptorAvailability()


def canonical_continuity_metadata_facts() -> ContinuityMetadataFacts:
    return ContinuityMetadataFacts()
