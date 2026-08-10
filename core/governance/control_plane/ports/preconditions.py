"""Read-only governance precondition observation boundary."""

from __future__ import annotations

from typing import Protocol

from ..domain import GovernanceAuthorizationRequest, GovernancePreconditionSnapshot


class PreconditionObservationPort(Protocol):
    """Collect one already-typed snapshot; policy evaluation remains in Governance."""

    def observe_preconditions(
        self, request: GovernanceAuthorizationRequest
    ) -> GovernancePreconditionSnapshot: ...


__all__ = ("PreconditionObservationPort",)
