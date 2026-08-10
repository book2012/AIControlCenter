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
    AuthorizationSnapshotBindingMismatch,
    DuplicatePreconditionBinding,
    InvalidAuthorizationInput,
    InvalidAuthorizationTransition,
    InvalidPreconditionComparisonInput,
    InvalidPreconditionModel,
    InvalidStaleEvaluationState,
    RequestDecisionBindingMismatch,
    TerminalAuthorizationReuse,
)
from .identity import GovernanceIdentity
from .preconditions import (
    GovernancePreconditionSnapshot,
    PreconditionBinding,
    PreconditionComparisonResult,
    PreconditionComparisonStatus,
    PreconditionDriftReason,
    PreconditionEvaluationResult,
    compare_precondition_snapshots,
    evaluate_authorization_expiry,
    evaluate_authorization_preconditions,
    validate_authorization_snapshot_binding,
)

__all__ = (
    "ALLOWED_TRANSITIONS", "TERMINAL_STATES", "ApprovalRequired",
    "AuthorizationBindingMismatch", "AuthorizationDecision", "AuthorizationDomainError",
    "AuthorizationSnapshotBindingMismatch", "AuthorizationState",
    "AuthorizationTransitionResult", "DuplicatePreconditionBinding", "GovernanceAuthorization",
    "GovernanceAuthorizationDecision", "GovernanceAuthorizationReceipt",
    "GovernanceAuthorizationRequest", "GovernanceAuthorizationStateRecord",
    "GovernanceIdentity", "InvalidAuthorizationInput", "InvalidAuthorizationTransition",
    "RequestDecisionBindingMismatch", "TerminalAuthorizationReuse", "transition_authorization",
    "GovernancePreconditionSnapshot", "InvalidPreconditionComparisonInput",
    "InvalidPreconditionModel", "InvalidStaleEvaluationState", "PreconditionBinding",
    "PreconditionComparisonResult", "PreconditionComparisonStatus", "PreconditionDriftReason",
    "PreconditionEvaluationResult", "compare_precondition_snapshots",
    "evaluate_authorization_expiry", "evaluate_authorization_preconditions",
    "validate_authorization_snapshot_binding",
)
