"""Fail-closed composition for protected-source metadata inspection."""

from threading import Lock

from core.secrets.mariadb_continuity_protected_source_metadata import (
    OPERATIONAL_METADATA_EVIDENCE_ISSUER_IMPLEMENTED,
    ProtectedSourceMetadataInspectionRequest,
)
from core.secrets.mariadb_continuity_protected_source_metadata_port import (
    ProtectedSourceMetadataInspectionCapability,
    _CapabilityState,
)
from ops.macos.shopping.mariadb_continuity_protected_source_metadata_adapter import (
    MacProtectedSourceMetadataAdapter,
    _BoundMetadataObservation,
    _ClosedInertObservationSource,
    _InertObservationMarker,
)


OPERATIONAL_CANONICAL_PATH_ISSUER_IMPLEMENTED = False
PRODUCTION_OPERATIONAL_INSPECTION_AVAILABLE = False


def _issue_inert_test_inspection_capability(
    request: ProtectedSourceMetadataInspectionRequest,
) -> ProtectedSourceMetadataInspectionCapability:
    """Issue test authority usable only with an injected inert/fake binding."""
    if type(request) is not ProtectedSourceMetadataInspectionRequest:
        raise TypeError("closed request required")
    capability = object.__new__(ProtectedSourceMetadataInspectionCapability)
    capability._request = request
    capability._state = _CapabilityState.AUTHORIZED
    capability._lock = Lock()
    return capability


def _compose_inert_test_metadata_inspector(
    payload: _BoundMetadataObservation | _InertObservationMarker,
) -> MacProtectedSourceMetadataAdapter:
    """Build a callback-free adapter over one closed, value-free test payload."""
    if type(payload) not in (_BoundMetadataObservation, _InertObservationMarker):
        raise TypeError("closed inert observation payload required")
    source = object.__new__(_ClosedInertObservationSource)
    source.observation = payload
    adapter = object.__new__(MacProtectedSourceMetadataAdapter)
    adapter._source = source
    return adapter


def compose_production_metadata_inspector() -> None:
    """No path issuer exists; production filesystem inspection is unavailable."""
    return None
