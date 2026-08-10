"""Typed, value-safe authorization domain failures."""


class AuthorizationDomainError(ValueError):
    """Base class for fail-closed authorization failures."""

    code = "AUTHORIZATION_DOMAIN_ERROR"

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"{self.code}: {reason}")


class InvalidAuthorizationInput(AuthorizationDomainError):
    code = "INVALID_AUTHORIZATION_INPUT"


class InvalidAuthorizationTransition(AuthorizationDomainError):
    code = "INVALID_AUTHORIZATION_TRANSITION"


class TerminalAuthorizationReuse(InvalidAuthorizationTransition):
    code = "TERMINAL_AUTHORIZATION_REUSE"


class RequestDecisionBindingMismatch(AuthorizationDomainError):
    code = "REQUEST_DECISION_BINDING_MISMATCH"


class ApprovalRequired(AuthorizationDomainError):
    code = "APPROVAL_REQUIRED"


class AuthorizationBindingMismatch(AuthorizationDomainError):
    code = "AUTHORIZATION_BINDING_MISMATCH"


class InvalidPreconditionModel(AuthorizationDomainError):
    code = "INVALID_PRECONDITION_MODEL"


class DuplicatePreconditionBinding(InvalidPreconditionModel):
    code = "DUPLICATE_PRECONDITION_BINDING"


class AuthorizationSnapshotBindingMismatch(AuthorizationDomainError):
    code = "AUTHORIZATION_SNAPSHOT_BINDING_MISMATCH"


class InvalidPreconditionComparisonInput(AuthorizationDomainError):
    code = "INVALID_PRECONDITION_COMPARISON_INPUT"


class InvalidStaleEvaluationState(AuthorizationDomainError):
    code = "INVALID_STALE_EVALUATION_STATE"
