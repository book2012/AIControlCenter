"""Public SEC-02 authorization domain API."""

from .authorization import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATES,
    AuthorizationDecision,
    AuthorizationState,
    AuthorizationTransitionResult,
    GovernanceAuthorization,
    GovernanceAuthorizationDecision,
    GovernanceAuthorizationReceipt,
    GovernanceAuthorizationRequest,
    GovernanceAuthorizationStateRecord,
    transition_authorization,
)
from .failures import (
    ApprovalRequired,
    AuthorizationBindingMismatch,
    AuthorizationDomainError,
    InvalidAuthorizationInput,
    InvalidAuthorizationTransition,
    RequestDecisionBindingMismatch,
    TerminalAuthorizationReuse,
)
from .identity import GovernanceIdentity

__all__ = (
    "ALLOWED_TRANSITIONS", "TERMINAL_STATES", "ApprovalRequired",
    "AuthorizationBindingMismatch", "AuthorizationDecision", "AuthorizationDomainError",
    "AuthorizationState", "AuthorizationTransitionResult", "GovernanceAuthorization",
    "GovernanceAuthorizationDecision", "GovernanceAuthorizationReceipt",
    "GovernanceAuthorizationRequest", "GovernanceAuthorizationStateRecord",
    "GovernanceIdentity", "InvalidAuthorizationInput", "InvalidAuthorizationTransition",
    "RequestDecisionBindingMismatch", "TerminalAuthorizationReuse", "transition_authorization",
)
