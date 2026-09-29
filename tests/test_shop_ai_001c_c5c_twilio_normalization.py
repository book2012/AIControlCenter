from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core.shopping.adapters.twilio_verify_read import (
    TwilioServiceSid,
    TwilioTransportFailure,
    TwilioVerificationSid,
    TwilioVerificationStatus,
    normalize_service_response,
    normalize_transport_failure,
    normalize_verification_response,
)
from core.shopping.ports.provider_activation import (
    ProviderOperation,
    ProviderRequestIdentity,
)
from core.shopping.ports.provider_authenticated_read import (
    ProviderReadStatus,
)


SERVICE = "VA" + "a" * 32
VERIFY = "VE" + "b" * 32
NOW = datetime(2026, 9, 29, 3, 0, tzinfo=timezone.utc)


def identity() -> ProviderRequestIdentity:
    return ProviderRequestIdentity(
        request_id="request-c5c-1",
        correlation_id="correlation-c5c-1",
    )


def test_service_200_normalizes_to_health_only() -> None:
    result = normalize_service_response(
        http_status=200,
        payload={
            "sid": SERVICE,
            "friendly_name": "must-be-discarded",
        },
        expected_sid=TwilioServiceSid(SERVICE),
        identity=identity(),
        observed_at=NOW,
    )

    assert result.operation is ProviderOperation.READ_HEALTH
    assert result.status is ProviderReadStatus.HEALTHY
    assert result.provider_verification_id is None


def test_verification_status_remains_provider_evidence_not_c4_truth() -> None:
    evidence = normalize_verification_response(
        http_status=200,
        payload={
            "sid": VERIFY,
            "status": "approved",
            "to": "+821012345678",
            "account_sid": "AC-secret",
        },
        expected_sid=TwilioVerificationSid(VERIFY),
        identity=identity(),
        observed_at=NOW,
    )

    assert evidence.read_result.operation is ProviderOperation.READ_EVIDENCE
    assert evidence.read_result.status is ProviderReadStatus.AVAILABLE
    assert evidence.provider_status is TwilioVerificationStatus.APPROVED
    assert evidence.read_result.provider_verification_id is not None

    # Provider-specific "approved" remains bounded evidence.
    assert evidence.read_result.status.name != "VERIFIED"


def test_unknown_provider_status_fails_closed() -> None:
    evidence = normalize_verification_response(
        http_status=200,
        payload={
            "sid": VERIFY,
            "status": "future-new-status",
        },
        expected_sid=TwilioVerificationSid(VERIFY),
        identity=identity(),
        observed_at=NOW,
    )

    assert evidence.provider_status is None
    assert evidence.read_result.status is ProviderReadStatus.MALFORMED
    assert evidence.read_result.provider_verification_id is None


@pytest.mark.parametrize(
    ("http_status", "expected"),
    [
        (404, ProviderReadStatus.NOT_FOUND),
        (429, ProviderReadStatus.UNAVAILABLE),
        (500, ProviderReadStatus.UNAVAILABLE),
        (503, ProviderReadStatus.UNAVAILABLE),
    ],
)
def test_http_failures_do_not_invent_terminal_truth(
    http_status: int,
    expected: ProviderReadStatus,
) -> None:
    evidence = normalize_verification_response(
        http_status=http_status,
        payload=None,
        expected_sid=TwilioVerificationSid(VERIFY),
        identity=identity(),
        observed_at=NOW,
    )

    assert evidence.provider_status is None
    assert evidence.read_result.status is expected
    assert evidence.read_result.provider_verification_id is None


@pytest.mark.parametrize(
    "failure",
    list(TwilioTransportFailure),
)
def test_transport_uncertainty_stays_unknown_outcome(
    failure: TwilioTransportFailure,
) -> None:
    result = normalize_transport_failure(
        operation=ProviderOperation.READ_EVIDENCE,
        failure=failure,
        identity=identity(),
        observed_at=NOW,
    )

    assert result.status is ProviderReadStatus.UNKNOWN_OUTCOME
    assert result.provider_verification_id is None
