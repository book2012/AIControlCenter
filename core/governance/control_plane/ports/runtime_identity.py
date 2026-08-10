"""Read-only runtime identity observation boundary."""

from __future__ import annotations

from typing import Protocol

from ..domain import GovernanceAuthorizationRequest, PreconditionBinding


class RuntimeIdentityObservationPort(Protocol):
    """Observe identity only; activation and restart are outside this port."""

    def observe_runtime_identity(
        self, request: GovernanceAuthorizationRequest
    ) -> PreconditionBinding: ...


__all__ = ("RuntimeIdentityObservationPort",)
