"""Single-invocation execution and read-only postcondition boundaries."""

from __future__ import annotations

from typing import Protocol

from ..domain import (
    GovernanceExecutionReceipt,
    GovernanceExecutionRequest,
    GovernancePostconditionReport,
)


class ControlledExecutionPort(Protocol):
    """Cross exactly one bounded invocation boundary and return its factual result."""

    def invoke_once(
        self, request: GovernanceExecutionRequest
    ) -> GovernanceExecutionReceipt: ...


class PostconditionValidationPort(Protocol):
    """Validate an observed outcome without authorizing retry or rollback."""

    def validate_postconditions(
        self, receipt: GovernanceExecutionReceipt
    ) -> GovernancePostconditionReport: ...


__all__ = ("ControlledExecutionPort", "PostconditionValidationPort")
