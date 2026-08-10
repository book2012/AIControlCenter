"""Read-only Git evidence boundary owned by Governance."""

from __future__ import annotations

from typing import Protocol

from ..domain import GovernanceAuthorizationRequest, PreconditionBinding


class GitReadonlyEvidencePort(Protocol):
    """Return value-free typed Git evidence without executing Git mutations."""

    def observe_git_evidence(
        self, request: GovernanceAuthorizationRequest
    ) -> PreconditionBinding: ...


__all__ = ("GitReadonlyEvidencePort",)
