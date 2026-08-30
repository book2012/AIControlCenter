from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timedelta, timezone

import pytest

from core.governance.control_plane.trust.fresh_human_evidence import (
    ALGORITHM, BOUNDED_MUTATION, FreshHumanChallengeIssuer, FreshHumanEvidenceV1,
    FreshHumanVerificationResult, PURPOSE, SCHEMA_VERSION, verify_fresh_human_evidence,
)
from core.governance.control_plane.trust.pre_bootstrap_remediation_journal import AuthorizationReplayKey

NOW = datetime(2026, 8, 31, 1, 2, 3, tzinfo=timezone.utc)
KEY = AuthorizationReplayKey.derive_from_ephemeral_capability(b"capability-one")
OTHER_KEY = AuthorizationReplayKey.derive_from_ephemeral_capability(b"capability-two")
FINGERPRINT = "p256-key-fingerprint"


class ExactVerifier:
    def __init__(self, message): self.message = message
    def verify(self, **kwargs):
        return (FreshHumanVerificationResult.VERIFIED
                if kwargs["message"] == self.message and kwargs["signature"] == b"valid"
                else FreshHumanVerificationResult.DENIED)


def challenge():
    return FreshHumanChallengeIssuer(clock=lambda: NOW,
        entropy=lambda size: b"n" * size).issue(request_identity="request-immutable-1", replay_key=KEY)


def evidence(value=None):
    value = value or challenge()
    return FreshHumanEvidenceV1(value, b"valid", FINGERPRINT)


def verify(value=None, expected=None, key=KEY, now=NOW):
    expected = expected or challenge()
    value = value or evidence(expected)
    return verify_fresh_human_evidence(value, expected_challenge=expected,
        expected_replay_key=key, expected_public_key_fingerprint=FINGERPRINT,
        verifier=ExactVerifier(expected.canonical_bytes()), now=now)


def test_exact_challenge_is_immutable_and_canonical():
    item = challenge()
    with pytest.raises(FrozenInstanceError): item.nonce = "caller"
    assert item.canonical_bytes() == challenge().canonical_bytes()


@pytest.mark.parametrize("field,value", [
    ("schema_version", "V2"), ("purpose", "OTHER"),
    ("bounded_mutation", "OTHER"), ("request_identity", "other-request"),
    ("authorization_replay_key", OTHER_KEY.value), ("nonce", "00" * 32),
])
def test_exact_binding_substitutions_are_denied(field, value):
    expected = challenge()
    assert verify(evidence(replace(expected, **{field: value})), expected) is FreshHumanVerificationResult.DENIED


def test_wrong_replay_key_is_denied():
    assert verify(key=OTHER_KEY) is FreshHumanVerificationResult.DENIED


def test_expired_and_future_issued_are_denied():
    assert verify(now=NOW + timedelta(minutes=5)) is FreshHumanVerificationResult.EXPIRED
    assert verify(now=NOW - timedelta(microseconds=1)) is FreshHumanVerificationResult.DENIED


def test_malformed_timestamp_signature_algorithm_and_key_fail_closed():
    expected = challenge()
    malformed_time = replace(expected, issued_at="not-a-time")
    assert verify_fresh_human_evidence(
        evidence(malformed_time), expected_challenge=malformed_time,
        expected_replay_key=KEY, expected_public_key_fingerprint=FINGERPRINT,
        verifier=ExactVerifier(b"unused"), now=NOW,
    ) is FreshHumanVerificationResult.ERROR
    assert verify(replace(evidence(expected), signature=b""), expected) is FreshHumanVerificationResult.DENIED
    assert verify(replace(evidence(expected), algorithm="OTHER"), expected) is FreshHumanVerificationResult.NOT_READY
    wrong_key = replace(evidence(expected), public_key_fingerprint="wrong")
    assert verify(wrong_key, expected) is FreshHumanVerificationResult.DENIED


def test_evidence_is_minimized_and_carries_no_authority_or_secret_fields():
    names = {field.name.lower() for field in fields(FreshHumanEvidenceV1)}
    forbidden = {"password", "biometric", "lacontext", "authorizationref",
                 "authorizationexternalform", "authority", "retry", "rollback"}
    assert names == {"challenge", "signature", "public_key_fingerprint", "algorithm"}
    assert names.isdisjoint(forbidden)
    assert not hasattr(evidence(), "execute")


def test_constants_freeze_exact_contract():
    item = challenge()
    assert (item.schema_version, item.purpose, item.bounded_mutation) == (
        SCHEMA_VERSION, PURPOSE, BOUNDED_MUTATION)
    assert evidence().algorithm == ALGORITHM
