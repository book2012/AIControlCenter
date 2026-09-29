from __future__ import annotations

from datetime import datetime, timezone

from core.shopping.adapters.twilio_verify_read import (
    TwilioVerificationSid,
    normalize_verification_response,
)
from core.shopping.ports.provider_activation import ProviderRequestIdentity


VERIFY = "VE" + "b" * 32
NOW = datetime(2026, 9, 29, 3, 0, tzinfo=timezone.utc)


def identity() -> ProviderRequestIdentity:
    return ProviderRequestIdentity(
        request_id="request-privacy-1",
        correlation_id="correlation-privacy-1",
    )


def test_raw_provider_payload_and_destination_are_discarded() -> None:
    payload = {
        "sid": VERIFY,
        "status": "pending",
        "to": "+821012345678",
        "account_sid": "AC-super-secret",
        "lookup": {"carrier": "private"},
        "send_code_attempts": [{"time": "private"}],
        "url": "https://provider.example/private",
        "links": {"x": "secret-link"},
        "unexpected": "secret-extra-field",
    }

    evidence = normalize_verification_response(
        http_status=200,
        payload=payload,
        expected_sid=TwilioVerificationSid(VERIFY),
        identity=identity(),
        observed_at=NOW,
    )

    rendered = " ".join([
        repr(evidence),
        repr(evidence.read_result),
        repr(evidence.to_log_dict()),
    ])

    for forbidden in (
        "+821012345678",
        "AC-super-secret",
        "private",
        "provider.example",
        "secret-link",
        "secret-extra-field",
    ):
        assert forbidden not in rendered

    assert not hasattr(evidence, "payload")
    assert not hasattr(evidence.read_result, "payload")


def test_log_dict_is_bounded() -> None:
    evidence = normalize_verification_response(
        http_status=200,
        payload={
            "sid": VERIFY,
            "status": "pending",
            "to": "+821012345678",
        },
        expected_sid=TwilioVerificationSid(VERIFY),
        identity=identity(),
        observed_at=NOW,
    )

    logged = evidence.to_log_dict()

    assert "to" not in logged
    assert "payload" not in logged
    assert "credential" not in logged
    assert set(logged).issubset({
        "provider_source",
        "operation",
        "request_id",
        "correlation_id",
        "status",
        "observed_at",
        "evidence_code",
        "provider_status",
    })
