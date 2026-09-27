"""Mock-only tests for the trusted verification receipt contract seam."""
from datetime import datetime, timedelta, timezone
import json
import socket
import sqlite3

import pytest
from pydantic import ValidationError

from core.api.schemas.customer_auth import (
    ReceiptResponseCode, VerificationReceiptConsumeRequest,
    VerificationReceiptConsumeResponse, public_response_fields,
)
from core.shopping.customer_auth import (
    RECEIPT_MAX_LIFETIME, ReceiptLifecycle, ReceiptValidationResult,
    TrustedReceiptBinding, TrustedVerificationContext, TrustedVerificationReceipt,
    VerificationPurpose, validate_trusted_receipt,
)


START = datetime(2026, 9, 1, tzinfo=timezone.utc)
NOW = START + timedelta(minutes=1)
RECEIPT_ID = "AG-VRF-" + "1" * 12 + "4" + "1" * 3 + "8" + "1" * 15
CHALLENGE = "AG-CHL-" + "2" * 12 + "4" + "2" * 3 + "8" + "2" * 15
OTHER_CHALLENGE = "AG-CHL-" + "3" * 12 + "4" + "3" * 3 + "8" + "3" * 15
ISSUER = "AG-ISS-" + "4" * 12 + "4" + "4" * 3 + "8" + "4" * 15
CUSTOMER = "AG-CUS-" + "5" * 12 + "4" + "5" * 3 + "8" + "5" * 15


@pytest.fixture(autouse=True)
def isolated_mock_environment(monkeypatch):
    """The contract must not initialize runtime state or perform I/O."""
    attempts = []

    def blocked(*args, **kwargs):
        attempts.append(True)
        raise AssertionError("network and database access are prohibited")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    monkeypatch.setattr(sqlite3, "connect", blocked)
    yield
    assert not attempts


def receipt(**updates):
    payload = dict(
        receipt_id=RECEIPT_ID, purpose=VerificationPurpose.SESSION_ISSUANCE,
        browser_challenge=CHALLENGE, issuer_ref=ISSUER, customer_id=CUSTOMER,
        issued_at=START, expires_at=START + RECEIPT_MAX_LIFETIME,
        lifecycle=ReceiptLifecycle.ISSUED,
    )
    payload.update(updates)
    return TrustedVerificationReceipt(**payload)


def context(**updates):
    payload = dict(accepted_bindings=frozenset({TrustedReceiptBinding(RECEIPT_ID, ISSUER, CUSTOMER)}),
                   consumed_receipt_ids=frozenset())
    payload.update(updates)
    return TrustedVerificationContext(**payload)


def valid(receipt_value=None, **kwargs):
    return validate_trusted_receipt(receipt_value or receipt(), now=NOW,
                                    expected_challenge=CHALLENGE,
                                    context=context(**kwargs))


def test_valid_policy_requires_explicit_server_trusted_binding():
    assert valid() is ReceiptValidationResult.ACCEPTED
    assert valid(accepted_bindings=frozenset()) is ReceiptValidationResult.UNTRUSTED_PROVENANCE


def test_purpose_and_cross_purpose_fail_closed():
    # The closed model rejects unsupported purpose before policy can accept it.
    with pytest.raises(ValidationError):
        receipt(purpose="SMS_NOTIFICATION")
    assert valid(receipt(purpose=VerificationPurpose.SESSION_ISSUANCE),
                 accepted_bindings=frozenset()) is ReceiptValidationResult.UNTRUSTED_PROVENANCE


def test_wrong_browser_challenge_is_denied():
    assert validate_trusted_receipt(receipt(), now=NOW, expected_challenge=OTHER_CHALLENGE,
                                    context=context()) is ReceiptValidationResult.CHALLENGE_MISMATCH


@pytest.mark.parametrize("now,expected", [
    (START - timedelta(seconds=1), ReceiptValidationResult.INVALID_TIME),
    (START + RECEIPT_MAX_LIFETIME, ReceiptValidationResult.EXPIRED),
    (START + RECEIPT_MAX_LIFETIME + timedelta(seconds=1), ReceiptValidationResult.EXPIRED),
])
def test_expiration_and_exact_boundary_are_fail_closed(now, expected):
    assert validate_trusted_receipt(receipt(), now=now, expected_challenge=CHALLENGE,
                                    context=context()) is expected


def test_invalid_timestamp_ordering_and_lifetime_rejected():
    with pytest.raises(ValidationError):
        receipt(expires_at=START)
    with pytest.raises(ValidationError):
        receipt(expires_at=START + RECEIPT_MAX_LIFETIME + timedelta(microseconds=1))


def test_missing_untrusted_and_ambiguous_provenance_fail_closed():
    assert valid(accepted_bindings=frozenset()) is ReceiptValidationResult.UNTRUSTED_PROVENANCE
    wrong = TrustedReceiptBinding(RECEIPT_ID, ISSUER, CUSTOMER.replace("5", "6"))
    assert valid(accepted_bindings=frozenset({wrong})) is ReceiptValidationResult.UNTRUSTED_PROVENANCE
    with pytest.raises(ValueError):
        TrustedVerificationContext(accepted_bindings=frozenset({
            TrustedReceiptBinding(RECEIPT_ID, ISSUER, CUSTOMER), wrong}))


def test_forged_client_identity_and_issuer_strings_do_not_grant_authority():
    forged = receipt(customer_id=CUSTOMER.replace("5", "6"))
    assert validate_trusted_receipt(forged, now=NOW, expected_challenge=CHALLENGE,
                                    context=context()) is ReceiptValidationResult.UNTRUSTED_PROVENANCE
    issuer_only = TrustedVerificationContext(
        accepted_bindings=frozenset({TrustedReceiptBinding(RECEIPT_ID, ISSUER, "") }))
    assert validate_trusted_receipt(receipt(), now=NOW, expected_challenge=CHALLENGE,
                                    context=issuer_only) is ReceiptValidationResult.UNTRUSTED_PROVENANCE


@pytest.mark.parametrize("value", [None, {}, {"receipt_id": RECEIPT_ID}, "raw", 7])
def test_malformed_receipts_fail_closed(value):
    assert validate_trusted_receipt(value, now=NOW, expected_challenge=CHALLENGE,
                                    context=context()) is ReceiptValidationResult.INVALID_RECEIPT


def test_unknown_fields_and_invalid_lifecycle_are_rejected():
    with pytest.raises(ValidationError):
        TrustedVerificationReceipt.model_validate({**receipt().model_dump(), "extra": "x"})
    consumed = receipt(lifecycle=ReceiptLifecycle.CONSUMED)
    assert valid(consumed) is ReceiptValidationResult.INVALID_LIFECYCLE
    revoked = receipt(lifecycle=ReceiptLifecycle.REVOKED)
    assert valid(revoked) is ReceiptValidationResult.INVALID_LIFECYCLE


def test_explicit_consumed_and_replayed_evidence_are_denied():
    consumed = context(consumed_receipt_ids=frozenset({RECEIPT_ID}))
    assert validate_trusted_receipt(receipt(), now=NOW, expected_challenge=CHALLENGE,
                                    context=consumed) is ReceiptValidationResult.REPLAYED


def test_public_request_cannot_assert_trusted_values():
    request = VerificationReceiptConsumeRequest(
        receipt_id="VRF-CLIENT01", browser_challenge="CHL-CLIENT01")
    assert set(request.model_dump()) == {"schema_version", "receipt_id", "browser_challenge"}
    for field in ("customer_id", "issuer_ref", "verified", "authenticated", "otp", "phone_number"):
        with pytest.raises(ValidationError):
            VerificationReceiptConsumeRequest.model_validate({**request.model_dump(), field: "claim"})


def test_public_response_is_secret_free_and_closed():
    response = VerificationReceiptConsumeResponse(
        outcome=ReceiptResponseCode.REJECTED, detail_code="UNTRUSTED_PROVENANCE")
    dumped = public_response_fields(response)
    encoded = json.dumps(dumped)
    assert set(dumped) == {"schema_version", "outcome", "detail_code"}
    for secret in ("phone", "otp", "secret", "hash", "credential", "configuration"):
        assert secret not in encoded.lower()
    with pytest.raises(ValidationError):
        VerificationReceiptConsumeResponse.model_validate({**dumped, "receipt": receipt().model_dump()})


def test_persistence_records_alone_do_not_create_authority():
    assert valid(accepted_bindings=frozenset()) is ReceiptValidationResult.UNTRUSTED_PROVENANCE
    assert not hasattr(receipt(), "authenticated")


def test_policy_does_not_claim_durable_single_use_or_authentication():
    assert valid() is ReceiptValidationResult.ACCEPTED
    assert "consumed" not in receipt().model_dump()
    assert not hasattr(receipt(), "session_secret")
    assert not hasattr(receipt(), "authenticated")


def test_contract_compatibility_uses_existing_opaque_customer_reference():
    from core.shopping.customer_identity import CustomerId
    assert isinstance(CUSTOMER, str)
    assert CustomerId.__metadata__
    assert receipt().customer_id == CUSTOMER
