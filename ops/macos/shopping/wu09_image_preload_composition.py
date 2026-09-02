"""Mac-only composition root for the exact WU09 Production image preload."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from weakref import WeakKeyDictionary

from core.governance.control_plane.adapters.sqlite import (
    SQLiteAuthorizationConsumptionAdapter,
    SQLiteOwnershipIdentity,
)
from core.governance.control_plane.application.wu09_authorization_intake import (
    intake_wu09_trusted_production_authorization,
)
from core.governance.control_plane.application.wu09_image_preload_coordinator import (
    WU09ImagePreloadCoordinator,
    WU09PreloadLifecycle,
)
from core.governance.control_plane.ports.authorization_consumption import (
    AuthorizationConsumptionCommand,
    AuthorizationConsumptionResult,
)
from core.governance.control_plane.domain import (
    GovernancePreconditionSnapshot,
    validate_authorization_snapshot_binding,
)
from core.governance.control_plane.trust.operator_identity import (
    ProductionMacOperatorObserver,
    observe_operator,
)
from ops.macos.shopping.wu09_image_preload import (
    WU09ExactImagePreloadExecution,
    WU09PreloadPostconditionValidator,
    WU09PreloadPreconditionObserver,
    WU09ProductionReadOnlyObservation,
    validate_expected_precondition_snapshot,
)


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_FACTORY_PROVENANCE_LOCK = Lock()


@dataclass(frozen=True, slots=True)
class WU09ProductionCompositionInput:
    raw_authorization_envelope: bytes
    expected_preconditions: GovernancePreconditionSnapshot
    repository_root: Path

    def __post_init__(self) -> None:
        if type(self.raw_authorization_envelope) is not bytes:
            raise TypeError("raw_authorization_envelope must be bytes")
        if type(self.expected_preconditions) is not GovernancePreconditionSnapshot:
            raise TypeError("expected_preconditions must be a complete typed snapshot")
        if not isinstance(self.repository_root, Path) or not self.repository_root.is_absolute():
            raise TypeError("repository_root must be an absolute Path")
        if self.repository_root.resolve() != _REPOSITORY_ROOT:
            raise ValueError("repository_root must be the AIControlCenter repository")


class WU09ProductionComposition:
    """Opaque process-local identity for a factory-issued WU09 assembly."""

    __slots__ = ("__weakref__",)

    def __init__(self, *_: object, **__: object) -> None:
        raise TypeError("direct WU09 Production composition construction is prohibited")

    def __reduce__(self) -> object:
        raise TypeError("WU09 Production composition cannot be serialized")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("WU09 Production composition cannot be serialized")

    def __copy__(self) -> object:
        raise TypeError("WU09 Production composition cannot be copied")

    def __deepcopy__(self, memo: object) -> object:
        del memo
        raise TypeError("WU09 Production composition cannot be copied")


@dataclass(frozen=True, slots=True)
class _WU09IssuedState:
    coordinator: WU09ImagePreloadCoordinator
    lifecycle: WU09PreloadLifecycle


_FACTORY_ISSUED_STATES: WeakKeyDictionary[
    WU09ProductionComposition, _WU09IssuedState
] = WeakKeyDictionary()


def conduct_wu09_production_image_preload(
    composition: WU09ProductionComposition,
) -> object:
    """Cross the prepared ceremony boundary once using only the sealed assembly.

    Calling this function is the future Production mutation.  Repository
    preparation and composition never call it.
    """
    if type(composition) is not WU09ProductionComposition:
        raise TypeError("composition must be the exact sealed WU09 composition")
    with _FACTORY_PROVENANCE_LOCK:
        issued_state = _FACTORY_ISSUED_STATES.pop(composition, None)
        if issued_state is None:
            raise TypeError("composition was not actively issued by the WU09 factory")
    return issued_state.coordinator.coordinate(issued_state.lifecycle)


class _DeferredProductionAuthorizationConsumption:
    """Keep read-only composition from creating the durable consumption store."""

    __slots__ = ("_repository_root", "_ownership_identity", "_home")

    def __init__(
        self,
        *,
        repository_root: Path,
        ownership_identity: SQLiteOwnershipIdentity,
        home: Path,
    ) -> None:
        self._repository_root = repository_root
        self._ownership_identity = ownership_identity
        self._home = home

    def consume_once(
        self, command: AuthorizationConsumptionCommand
    ) -> AuthorizationConsumptionResult:
        adapter = SQLiteAuthorizationConsumptionAdapter(
            repository_root=self._repository_root,
            ownership_identity=self._ownership_identity,
            home=self._home,
        )
        return adapter.consume_once(command)


def compose_wu09_production_image_preload(
    request: WU09ProductionCompositionInput,
) -> WU09ProductionComposition:
    """Validate and assemble without deciding, consuming, invoking, or mutating Production."""
    if type(request) is not WU09ProductionCompositionInput:
        raise TypeError("request must be exactly WU09ProductionCompositionInput")
    trusted = intake_wu09_trusted_production_authorization(
        request.raw_authorization_envelope
    )
    validate_expected_precondition_snapshot(
        trusted.facts.authorization.request, request.expected_preconditions
    )
    validate_authorization_snapshot_binding(
        trusted.facts.authorization, request.expected_preconditions
    )
    observed_operator = observe_operator(ProductionMacOperatorObserver())
    if observed_operator.governance_identity != trusted.facts.expected_operator:
        raise ValueError("observed Mac ownership identity does not match signed authority")

    observation = WU09ProductionReadOnlyObservation(request.repository_root)
    consumer = _DeferredProductionAuthorizationConsumption(
        repository_root=request.repository_root,
        ownership_identity=SQLiteOwnershipIdentity(
            observed_operator.uid, observed_operator.gid
        ),
        home=Path(observed_operator.passwd_home),
    )
    coordinator = WU09ImagePreloadCoordinator(
        authorization_consumption=consumer,
        precondition_observation=WU09PreloadPreconditionObserver(
            observation.observe_preload_preconditions
        ),
        controlled_execution=WU09ExactImagePreloadExecution(),
        postcondition_validation=WU09PreloadPostconditionValidator(
            observation.observe_preload_postconditions
        ),
    )
    lifecycle = WU09PreloadLifecycle(
        trusted.facts.authorization,
        trusted.facts.mutation_budget,
        trusted.facts.execution_request,
        request.expected_preconditions,
    )
    composed = object.__new__(WU09ProductionComposition)
    issued_state = _WU09IssuedState(coordinator, lifecycle)
    with _FACTORY_PROVENANCE_LOCK:
        _FACTORY_ISSUED_STATES[composed] = issued_state
    return composed


__all__ = (
    "WU09ProductionComposition", "WU09ProductionCompositionInput",
    "compose_wu09_production_image_preload", "conduct_wu09_production_image_preload",
)
