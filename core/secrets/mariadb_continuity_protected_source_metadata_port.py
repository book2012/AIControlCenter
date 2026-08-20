"""Closed authorization and port for protected-source metadata inspection."""

from enum import Enum, auto
from threading import Lock
from typing import Callable, Protocol, TypeVar, runtime_checkable

from core.secrets.mariadb_continuity_protected_source_metadata import (
    ProtectedSourceMetadataEvidence,
    ProtectedSourceMetadataInspectionRequest,
)

T = TypeVar("T")


class InspectionAuthorizationError(RuntimeError):
    pass


class _CapabilityState(Enum):
    AUTHORIZED = auto()
    CONSUMED = auto()


class ProtectedSourceMetadataInspectionCapability:
    """Opaque, process-local, canonical-request-bound, zero-mutation grant."""

    __slots__ = ("_request", "_state", "_lock")

    def __init__(self, request: ProtectedSourceMetadataInspectionRequest) -> None:
        del request
        raise InspectionAuthorizationError("direct capability construction is prohibited")

    def _consume_then(self, request: ProtectedSourceMetadataInspectionRequest, operation: Callable[[], T]) -> T:
        with self._lock:
            if request is not self._request:
                raise InspectionAuthorizationError("capability is bound to another request")
            if self._state is not _CapabilityState.AUTHORIZED:
                raise InspectionAuthorizationError("capability has already been consumed")
            self._state = _CapabilityState.CONSUMED
        return operation()

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("inspection capability cannot be serialized")

    __reduce__ = __reduce_ex__

    def __copy__(self) -> object:
        raise TypeError("inspection capability cannot be copied")

    def __deepcopy__(self, memo: object) -> object:
        del memo
        raise TypeError("inspection capability cannot be copied")


@runtime_checkable
class ProtectedSourceMetadataInspectionPort(Protocol):
    def inspect_once(
        self,
        request: ProtectedSourceMetadataInspectionRequest,
        capability: ProtectedSourceMetadataInspectionCapability,
    ) -> ProtectedSourceMetadataEvidence: ...
