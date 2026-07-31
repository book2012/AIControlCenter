"""Process-local, test-only single-use claim simulation."""

from .models import TestOnlyAuthorizationSimulationError


class InMemoryTestOnlyReplayGuard:
    def __init__(self) -> None:
        self._claimed: set[str] = set()

    def claim_once(self, permit_id: str) -> None:
        if permit_id in self._claimed:
            raise TestOnlyAuthorizationSimulationError("DUPLICATE_SIMULATED_CLAIM")
        self._claimed.add(permit_id)

    def reject_reuse(self, permit_id: str) -> None:
        if permit_id in self._claimed:
            raise TestOnlyAuthorizationSimulationError("SIMULATED_PERMIT_REUSE")
