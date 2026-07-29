"""DPL-03C approval evidence and bounded execution-authorization contracts."""

from core.deployment.authorization.ports import (
    ApprovalEvidenceVerifier,
    AuthorizationConsumer,
    Clock,
    NonceReplayGuard,
)
from core.deployment.authorization.service import (
    AuthorizationInputError,
    create_approval_decision,
    create_approval_request,
    materialize_execution_authorization,
)

__all__ = (
    "ApprovalEvidenceVerifier",
    "AuthorizationConsumer",
    "AuthorizationInputError",
    "Clock",
    "NonceReplayGuard",
    "create_approval_decision",
    "create_approval_request",
    "materialize_execution_authorization",
)
