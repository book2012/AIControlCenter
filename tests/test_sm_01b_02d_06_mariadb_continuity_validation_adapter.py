import json
import ast
from pathlib import Path

from core.secrets.mariadb_continuity_validation import (
    MariaDBContinuityValidationRequest,
    ValidationFact,
    ValidationOutcome,
)
from ops.macos.shopping.mariadb_continuity_validation_adapter import (
    CapabilityDisposition,
    MacMariaDBContinuityValidationAdapter,
    OneShotValidationObservation,
)


def invoke(capability):
    return MacMariaDBContinuityValidationAdapter().validate_once(
        MariaDBContinuityValidationRequest.canonical(), capability
    )


class FakeCapability:
    def __init__(self, observation=None, failure=None):
        self.observation = observation
        self.failure = failure
        self.calls = 0

    def validate_once(self):
        self.calls += 1
        if self.failure:
            raise RuntimeError(self.failure)
        return self.observation


def test_adapter_validates_only_when_all_six_facts_are_confirmed():
    capability = FakeCapability(OneShotValidationObservation(
        CapabilityDisposition.OBSERVED,
        *(ValidationFact.CONFIRMED,) * 6,
    ))
    observed = invoke(capability)
    assert observed.outcome is ValidationOutcome.VALIDATED
    assert capability.calls == 1


def test_explicit_rejection_is_one_attempt_without_fallback():
    capability = FakeCapability(OneShotValidationObservation(
        CapabilityDisposition.OBSERVED,
        credential_acceptance=ValidationFact.REJECTED,
    ))
    observed = invoke(capability)
    assert observed.outcome is ValidationOutcome.REJECTED
    assert observed.attempted_count == 1
    assert capability.calls == 1


def test_proven_pre_attempt_unavailability_is_zero_attempts():
    capability = FakeCapability(OneShotValidationObservation(
        CapabilityDisposition.UNAVAILABLE_BEFORE_ATTEMPT
    ))
    observed = invoke(capability)
    assert observed.outcome is ValidationOutcome.UNAVAILABLE
    assert observed.attempted_count == 0
    assert capability.calls == 1


def test_proven_pre_attempt_unsafe_is_zero_attempts_and_not_retried():
    capability = FakeCapability(OneShotValidationObservation(
        CapabilityDisposition.UNSAFE_BEFORE_ATTEMPT
    ))
    observed = invoke(capability)
    assert observed.outcome is ValidationOutcome.UNSAFE
    assert observed.attempted_count == 0
    assert all(fact is ValidationFact.NOT_EVALUATED for fact in observed.mandatory_facts)
    assert capability.calls == 1


def test_missing_capability_is_malformed_without_invocation():
    observed = invoke(object())
    assert observed.outcome is ValidationOutcome.MALFORMED
    assert observed.attempted_count == 0


def test_exception_after_invocation_is_uncertain_and_redacted():
    marker = "driver-secret-error-text"
    capability = FakeCapability(failure=marker)
    observed = invoke(capability)
    rendered = json.dumps(observed.to_projection(), sort_keys=True)
    assert observed.outcome is ValidationOutcome.UNCERTAIN
    assert observed.attempted_count == 1
    assert capability.calls == 1
    assert marker not in rendered


def test_adapter_catches_exception_but_not_base_exception():
    adapter_path = (
        Path(__file__).resolve().parents[1]
        / "ops/macos/shopping/mariadb_continuity_validation_adapter.py"
    )
    tree = ast.parse(adapter_path.read_text())
    caught = {
        handler.type.id for handler in ast.walk(tree)
        if isinstance(handler, ast.ExceptHandler) and isinstance(handler.type, ast.Name)
    }
    assert "Exception" in caught
    assert "BaseException" not in caught


def test_malformed_return_is_uncertain_and_never_retried():
    capability = FakeCapability({"credential": "must-not-escape"})
    observed = invoke(capability)
    assert observed.outcome is ValidationOutcome.UNCERTAIN
    assert observed.attempted_count == 1
    assert capability.calls == 1
    assert "must-not-escape" not in json.dumps(observed.to_projection())


def test_partial_authentication_never_becomes_validated():
    capability = FakeCapability(OneShotValidationObservation(
        CapabilityDisposition.OBSERVED,
        credential_acceptance=ValidationFact.CONFIRMED,
    ))
    observed = invoke(capability)
    assert observed.outcome is ValidationOutcome.UNCERTAIN
    assert observed.credential_acceptance is ValidationFact.CONFIRMED
    assert observed.data_continuity is ValidationFact.NOT_EVALUATED
    assert capability.calls == 1
