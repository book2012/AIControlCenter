from dataclasses import replace
from datetime import datetime, timezone

import pytest

from core.governance.control_plane.domain import (
    AuthorizationState, FailureClass, FailurePhase, GovernanceFailureEvidence,
    InvalidFailureEvidence, InvalidReceiptCounts, RetryProhibitionViolation,
    RollbackProhibitionViolation,
)

NOW = datetime(2026, 8, 10, tzinfo=timezone.utc)


def failure(**changes: object) -> GovernanceFailureEvidence:
    values = dict(
        schema_version="1.0.0", failure_id="failure-1", lifecycle_id="lifecycle-1",
        phase=FailurePhase.EXECUTION, failure_class=FailureClass.EXECUTION_FAILED,
        reason_codes=("EXECUTION_STOPPED",), authorization_state=AuthorizationState.CONSUMED,
        claim_consumed=True, actual_invocation_count=1, completed_count=0,
        uncertain_count=0, retry_prohibited=True, rollback_prohibited=True,
        manual_action_required=True, occurred_at=NOW,
    )
    values.update(changes)
    return GovernanceFailureEvidence(**values)  # type: ignore[arg-type]


def test_retry_and_rollback_prohibition_are_mandatory() -> None:
    with pytest.raises(RetryProhibitionViolation):
        failure(retry_prohibited=False)
    with pytest.raises(RollbackProhibitionViolation):
        failure(rollback_prohibited=False)


@pytest.mark.parametrize(("phase", "failure_class"), [
    (FailurePhase.EXECUTION, FailureClass.EXECUTION_FAILED),
    (FailurePhase.EXECUTION, FailureClass.EXECUTION_UNCERTAIN),
    (FailurePhase.POSTCONDITION, FailureClass.POSTCONDITION_FAILED),
    (FailurePhase.EVIDENCE_PERSISTENCE, FailureClass.EVIDENCE_PERSISTENCE_FAILED),
    (FailurePhase.CLOSEOUT, FailureClass.CLOSEOUT_FAILED),
])
def test_post_consumption_and_unsafe_classes_require_manual_action(
    phase: FailurePhase, failure_class: FailureClass,
) -> None:
    with pytest.raises(InvalidFailureEvidence):
        failure(phase=phase, failure_class=failure_class, manual_action_required=False)


def test_uncertain_execution_remains_non_retryable() -> None:
    value = failure(
        failure_class=FailureClass.EXECUTION_UNCERTAIN,
        actual_invocation_count=1, uncertain_count=1,
    )
    assert value.retry_prohibited is True


@pytest.mark.parametrize("changes", [
    {"actual_invocation_count": -1},
    {"actual_invocation_count": 1, "completed_count": 2},
    {"actual_invocation_count": 1, "uncertain_count": 2},
    {"actual_invocation_count": 1, "completed_count": 1, "uncertain_count": 1},
])
def test_invalid_counts_fail_closed(changes: dict[str, int]) -> None:
    with pytest.raises(InvalidReceiptCounts):
        replace(failure(), **changes)


def test_no_retry_or_rollback_api_and_safe_errors() -> None:
    value = failure()
    for forbidden in ("retry", "retry_allowed", "rollback", "compensate"):
        assert not hasattr(value, forbidden)
    with pytest.raises(InvalidFailureEvidence) as captured:
        failure(failure_id="")
    assert "GovernanceFailureEvidence(" not in str(captured.value)
    assert "EXECUTION_STOPPED" not in str(captured.value)
