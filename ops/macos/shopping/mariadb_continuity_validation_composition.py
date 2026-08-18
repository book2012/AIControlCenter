"""Process-local, fake-driven composition for MariaDB continuity validation."""

from enum import Enum, auto
from threading import Lock
from typing import Protocol

from core.secrets.mariadb_continuity_validation import (
    MariaDBContinuityValidationRequest,
)


class HumanPresenceGrantError(RuntimeError):
    pass


class MariaDBContinuityCompositionError(RuntimeError):
    pass


class _GrantState(Enum):
    AUTHORIZED = auto()
    CONSUMED = auto()


class HumanPresenceGrant:
    """Non-serializable, process-local, one-shot composition prerequisite."""

    __slots__ = ("_request", "_state", "_lock")

    def __init__(self, request: MariaDBContinuityValidationRequest) -> None:
        del request
        raise HumanPresenceGrantError("direct grant construction is prohibited")

    def _consume_for(self, request: MariaDBContinuityValidationRequest) -> None:
        with self._lock:
            if request != self._request:
                raise HumanPresenceGrantError("grant is not bound to this request")
            if self._state is not _GrantState.AUTHORIZED:
                raise HumanPresenceGrantError("grant has already been consumed")
            self._state = _GrantState.CONSUMED

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("HumanPresenceGrant cannot be serialized")

    def __reduce__(self) -> object:
        raise TypeError("HumanPresenceGrant cannot be serialized")

    def __copy__(self) -> object:
        raise TypeError("HumanPresenceGrant cannot be copied")

    def __deepcopy__(self, memo: object) -> object:
        del memo
        raise TypeError("HumanPresenceGrant cannot be copied")


def _issue_phase_a_inert_test_grant(
    request: MariaDBContinuityValidationRequest,
) -> HumanPresenceGrant:
    """Create fake Phase-A test support; this is not Production authorization."""
    if type(request) is not MariaDBContinuityValidationRequest:
        raise TypeError("request must be MariaDBContinuityValidationRequest")
    if request != MariaDBContinuityValidationRequest.canonical():
        raise ValueError("test grant requires the canonical request profile")
    grant = object.__new__(HumanPresenceGrant)
    grant._request = request
    grant._state = _GrantState.AUTHORIZED
    grant._lock = Lock()
    return grant


class MariaDBContinuityCapabilityAssembler(Protocol):
    def assemble(self, request: MariaDBContinuityValidationRequest) -> object:
        ...


class MariaDBContinuityValidationCompositionService:
    """Consume one grant, then assemble one opaque capability without invoking it."""

    __slots__ = ("_assembler",)

    def __init__(self, assembler: MariaDBContinuityCapabilityAssembler) -> None:
        if not callable(getattr(assembler, "assemble", None)):
            raise TypeError("assembler must implement assemble")
        self._assembler = assembler

    def compose(
        self,
        request: MariaDBContinuityValidationRequest,
        grant: HumanPresenceGrant,
    ) -> object:
        if type(request) is not MariaDBContinuityValidationRequest:
            raise TypeError("request must be MariaDBContinuityValidationRequest")
        if request != MariaDBContinuityValidationRequest.canonical():
            raise ValueError("composition requires the canonical request profile")
        if type(grant) is not HumanPresenceGrant:
            raise TypeError("grant must be HumanPresenceGrant")

        grant._consume_for(request)
        try:
            capability = self._assembler.assemble(request)
        except Exception:
            assembly_failed = True
        else:
            assembly_failed = False
        if assembly_failed:
            raise MariaDBContinuityCompositionError("capability assembly failed")
        return capability
