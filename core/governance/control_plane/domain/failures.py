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


class InvalidMutationBudgetModel(AuthorizationDomainError):
    code = "INVALID_MUTATION_BUDGET_MODEL"


class DuplicateMutationActionType(InvalidMutationBudgetModel):
    code = "DUPLICATE_MUTATION_ACTION_TYPE"


class UnknownMutationActionType(AuthorizationDomainError):
    code = "UNKNOWN_MUTATION_ACTION_TYPE"


class InvocationBeforeAuthorizationConsumption(AuthorizationDomainError):
    code = "INVOCATION_BEFORE_AUTHORIZATION_CONSUMPTION"


class MutationBudgetExhausted(AuthorizationDomainError):
    code = "MUTATION_BUDGET_EXHAUSTED"


class MutationBudgetViolated(AuthorizationDomainError):
    code = "MUTATION_BUDGET_VIOLATED"


class MutationInvocationCountExceeded(AuthorizationDomainError):
    code = "MUTATION_INVOCATION_COUNT_EXCEEDED"


class InvalidMutationInvocationOutcome(AuthorizationDomainError):
    code = "INVALID_MUTATION_INVOCATION_OUTCOME"


class InvalidMutationCountInvariant(InvalidMutationBudgetModel):
    code = "INVALID_MUTATION_COUNT_INVARIANT"


class RepeatedAuthorizationConsumption(AuthorizationDomainError):
    code = "REPEATED_AUTHORIZATION_CONSUMPTION"


class InvalidReceiptModel(AuthorizationDomainError):
    code = "INVALID_RECEIPT_MODEL"


class ReceiptBindingMismatch(AuthorizationDomainError):
    code = "RECEIPT_BINDING_MISMATCH"


class InvalidReceiptCounts(InvalidReceiptModel):
    code = "INVALID_RECEIPT_COUNTS"


class InvalidPostconditionModel(AuthorizationDomainError):
    code = "INVALID_POSTCONDITION_MODEL"


class InvalidFailureEvidence(AuthorizationDomainError):
    code = "INVALID_FAILURE_EVIDENCE"


class RetryProhibitionViolation(InvalidFailureEvidence):
    code = "RETRY_PROHIBITION_VIOLATION"


class RollbackProhibitionViolation(InvalidFailureEvidence):
    code = "ROLLBACK_PROHIBITION_VIOLATION"


class InvalidEvidenceReference(AuthorizationDomainError):
    code = "INVALID_EVIDENCE_REFERENCE"


class DuplicateEvidenceReference(InvalidEvidenceReference):
    code = "DUPLICATE_EVIDENCE_REFERENCE"


class InvalidEvidenceManifest(AuthorizationDomainError):
    code = "INVALID_EVIDENCE_MANIFEST"


class InvalidEvidenceBundle(AuthorizationDomainError):
    code = "INVALID_EVIDENCE_BUNDLE"
