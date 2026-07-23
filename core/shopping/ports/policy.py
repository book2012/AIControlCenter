"""Transport-neutral read-only Shopping port."""

from __future__ import annotations

from typing import Protocol

from core.shopping.contracts.provisional import (
    PolicyDecision,
    ReadContext,
    ReadPolicyRequest,
)

__all__ = ('PolicyDecisionPort',)


class PolicyDecisionPort(Protocol):
    """Read-only or compute-only application port."""

    async def evaluate_read(
        self,
        *,
        context: ReadContext,
        request: ReadPolicyRequest,
    ) -> PolicyDecision:
        ...
