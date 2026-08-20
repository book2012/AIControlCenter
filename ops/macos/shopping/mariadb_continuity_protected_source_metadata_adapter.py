"""Path-free classification over a closed, already-supplied inert observation."""

from dataclasses import dataclass
from enum import Enum

from core.secrets.mariadb_continuity_protected_source_metadata import (
    MetadataInspectionReason,
    ProtectedSourceMetadataEvidence,
    ProtectedSourceMetadataInspectionRequest,
    metadata_evidence_for_reason,
)
from core.secrets.mariadb_continuity_protected_source_metadata_port import (
    ProtectedSourceMetadataInspectionCapability,
)


@dataclass(frozen=True, slots=True)
class _BoundMetadataObservation:
    reason: MetadataInspectionReason


class _InertObservationMarker(Enum):
    FAILURE = "FAILURE"
    AMBIGUOUS = "AMBIGUOUS"


class _ClosedInertObservationSource:
    __slots__ = ("observation",)

    def __init__(self, observation: object) -> None:
        del observation
        raise TypeError("inert observation sources are repository-created only")


class MacProtectedSourceMetadataAdapter:
    """Classify one already-bound observation; never accepts or reads a path."""

    __slots__ = ("_source",)

    def __init__(self, source: object) -> None:
        del source
        raise TypeError("direct adapter construction is prohibited")

    def inspect_once(
        self,
        request: ProtectedSourceMetadataInspectionRequest,
        capability: ProtectedSourceMetadataInspectionCapability,
    ) -> ProtectedSourceMetadataEvidence:
        if type(request) is not ProtectedSourceMetadataInspectionRequest:
            raise TypeError("closed request required")
        if type(capability) is not ProtectedSourceMetadataInspectionCapability:
            raise TypeError("closed inspection capability required")

        def inspect() -> ProtectedSourceMetadataEvidence:
            observation = self._source.observation
            if observation is _InertObservationMarker.FAILURE:
                return metadata_evidence_for_reason(MetadataInspectionReason.METADATA_ACCESS_FAILURE)
            if type(observation) is not _BoundMetadataObservation or type(observation.reason) is not MetadataInspectionReason:
                return metadata_evidence_for_reason(MetadataInspectionReason.AMBIGUOUS_METADATA_RESULT)
            return metadata_evidence_for_reason(observation.reason)

        return capability._consume_then(request, inspect)
