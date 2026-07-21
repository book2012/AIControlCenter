from datetime import datetime, timezone

from core.governance.operations.domain.severity import (
    OperationalCondition,
    Severity,
    build_signal,
    classify_severity,
)


def observed_at() -> datetime:
    return datetime(
        2026,
        7,
        21,
        1,
        tzinfo=timezone.utc,
    )


def test_severity_mapping_is_explicit():
    assert (
        classify_severity(
            OperationalCondition.SUCCESS
        )
        is Severity.INFO
    )
    assert (
        classify_severity(
            OperationalCondition.EXECUTION_FAILURE
        )
        is Severity.WARNING
    )
    assert (
        classify_severity(
            OperationalCondition.MISSED_RUN
        )
        is Severity.CRITICAL
    )


def test_signal_contains_deduplication_and_evidence():
    signal = build_signal(
        OperationalCondition.MISSED_RUN,
        observed_at(),
        "audit-snapshot:2026-07-21T01:00:00Z",
        evidence={
            "automatic_remediation": False,
        },
    )

    assert signal.severity is Severity.CRITICAL
    assert signal.deduplication_key
    assert (
        signal.evidence["automatic_remediation"]
        is False
    )
