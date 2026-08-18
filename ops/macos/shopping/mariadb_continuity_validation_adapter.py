"""Fake-driven Mac adapter for one-shot MariaDB continuity validation."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from core.secrets.mariadb_continuity_validation import (
    ConsumerCompatibility,
    MariaDBContinuityValidationRequest,
    MariaDBContinuityValidationResult,
    ValidationFact,
    ValidationOutcome,
    ValidationReasonCode,
)


class CapabilityDisposition(str, Enum):
    OBSERVED = "OBSERVED"
    UNAVAILABLE_BEFORE_ATTEMPT = "UNAVAILABLE_BEFORE_ATTEMPT"
    UNSAFE_BEFORE_ATTEMPT = "UNSAFE_BEFORE_ATTEMPT"


@dataclass(frozen=True, slots=True)
class OneShotValidationObservation:
    disposition: CapabilityDisposition
    credential_acceptance: ValidationFact = ValidationFact.NOT_EVALUATED
    expected_database_identity: ValidationFact = ValidationFact.NOT_EVALUATED
    expected_account_identity: ValidationFact = ValidationFact.NOT_EVALUATED
    required_grants: ValidationFact = ValidationFact.NOT_EVALUATED
    data_identity: ValidationFact = ValidationFact.NOT_EVALUATED
    data_continuity: ValidationFact = ValidationFact.NOT_EVALUATED


class OneShotMariaDBValidationCapability(Protocol):
    """Opaque external authority exposing only one fixed validation operation."""

    def validate_once(self) -> OneShotValidationObservation:
        ...


class MacMariaDBContinuityValidationAdapter:
    """Map one opaque capability invocation into value-free factual evidence."""

    def validate_once(
        self, request: MariaDBContinuityValidationRequest, capability: object
    ) -> MariaDBContinuityValidationResult:
        if type(request) is not MariaDBContinuityValidationRequest:
            raise TypeError("request must be MariaDBContinuityValidationRequest")
        operation = getattr(capability, "validate_once", None)
        if not callable(operation):
            return self._zero_attempt(
                request,
                ValidationOutcome.MALFORMED,
                ValidationReasonCode.CAPABILITY_OBSERVATION_MALFORMED,
            )

        try:
            observation = operation()
        except Exception:
            return self._uncertain(request)

        if type(observation) is not OneShotValidationObservation:
            return self._uncertain(request)
        if type(observation.disposition) is not CapabilityDisposition:
            return self._uncertain(request)
        facts = self._facts(observation)
        if any(type(fact) is not ValidationFact for fact in facts):
            return self._uncertain(request)

        if observation.disposition is CapabilityDisposition.UNAVAILABLE_BEFORE_ATTEMPT:
            if any(fact is not ValidationFact.NOT_EVALUATED for fact in facts):
                return self._uncertain(request)
            return self._zero_attempt(
                request,
                ValidationOutcome.UNAVAILABLE,
                ValidationReasonCode.CAPABILITY_UNAVAILABLE_BEFORE_ATTEMPT,
            )
        if observation.disposition is CapabilityDisposition.UNSAFE_BEFORE_ATTEMPT:
            if any(fact is not ValidationFact.NOT_EVALUATED for fact in facts):
                return self._uncertain(request)
            return self._zero_attempt(
                request,
                ValidationOutcome.UNSAFE,
                ValidationReasonCode.VALIDATION_PRECONDITION_UNSAFE,
            )
        if facts[0] is ValidationFact.REJECTED and all(
            fact is ValidationFact.NOT_EVALUATED for fact in facts[1:]
        ):
            return self._result(
                request,
                ValidationOutcome.REJECTED,
                1,
                facts,
                ValidationReasonCode.CREDENTIAL_EXPLICITLY_REJECTED,
            )
        if all(fact is ValidationFact.CONFIRMED for fact in facts):
            return self._result(
                request,
                ValidationOutcome.VALIDATED,
                1,
                facts,
                ValidationReasonCode.ALL_MANDATORY_FACTS_CONFIRMED,
            )
        return self._uncertain(request, facts)

    @staticmethod
    def _facts(
        observation: OneShotValidationObservation,
    ) -> tuple[ValidationFact, ...]:
        return (
            observation.credential_acceptance,
            observation.expected_database_identity,
            observation.expected_account_identity,
            observation.required_grants,
            observation.data_identity,
            observation.data_continuity,
        )

    def _zero_attempt(
        self,
        request: MariaDBContinuityValidationRequest,
        outcome: ValidationOutcome,
        reason: ValidationReasonCode,
    ) -> MariaDBContinuityValidationResult:
        return self._result(
            request,
            outcome,
            0,
            (ValidationFact.NOT_EVALUATED,) * 6,
            reason,
        )

    def _uncertain(
        self,
        request: MariaDBContinuityValidationRequest,
        facts: tuple[ValidationFact, ...] | None = None,
    ) -> MariaDBContinuityValidationResult:
        safe_facts = list(facts or (ValidationFact.NOT_EVALUATED,) * 6)
        safe_facts = [
            ValidationFact.UNCERTAIN if fact is ValidationFact.REJECTED else fact
            for fact in safe_facts
        ]
        if ValidationFact.UNCERTAIN not in safe_facts:
            first_incomplete = next(
                (index for index, fact in enumerate(safe_facts) if fact is not ValidationFact.CONFIRMED),
                5,
            )
            safe_facts[first_incomplete] = ValidationFact.UNCERTAIN
        return self._result(
            request,
            ValidationOutcome.UNCERTAIN,
            1,
            tuple(safe_facts),
            ValidationReasonCode.ATTEMPT_RESULT_UNCERTAIN,
        )

    @staticmethod
    def _result(
        request: MariaDBContinuityValidationRequest,
        outcome: ValidationOutcome,
        attempted_count: int,
        facts: tuple[ValidationFact, ...],
        reason: ValidationReasonCode,
    ) -> MariaDBContinuityValidationResult:
        return MariaDBContinuityValidationResult(
            outcome=outcome,
            attempted_count=attempted_count,
            request=request,
            credential_acceptance=facts[0],
            expected_database_identity=facts[1],
            expected_account_identity=facts[2],
            required_grants=facts[3],
            data_identity=facts[4],
            data_continuity=facts[5],
            consumer_compatibility=ConsumerCompatibility.NOT_EVALUATED,
            reason_code=reason,
        )
