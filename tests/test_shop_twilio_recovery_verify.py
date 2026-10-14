from types import SimpleNamespace

import pytest

from core.shopping.adapters.twilio_recovery_verify import TwilioRecoveryVerifyAdapter


PHONE = "+821012345678"
VERIFY_SID = "VE" + "a" * 32


class ProviderRejected(RuntimeError):
    code = "REJECTED"


class Transport:
    phone = SimpleNamespace(value=PHONE)

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def invoke(self, path, body):
        self.calls.append((path, body))
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def test_start_challenge_is_fixed_to_configured_dev_phone():
    transport = Transport([{
        "sid": VERIFY_SID, "to": PHONE, "channel": "sms", "status": "pending",
    }])
    adapter = TwilioRecoveryVerifyAdapter(transport)
    assert adapter.start(PHONE, "event-1") == VERIFY_SID
    assert transport.calls == [(
        "Verifications", {"To": PHONE, "Channel": "sms", "Locale": "ko"},
    )]


def test_start_rejects_any_recipient_outside_dev_allowlist_without_provider_call():
    transport = Transport([])
    adapter = TwilioRecoveryVerifyAdapter(transport)
    with pytest.raises(ValueError):
        adapter.start("+821099999999", "event-1")
    assert transport.calls == []


@pytest.mark.parametrize("result,expected", [
    ({"sid": VERIFY_SID, "to": PHONE, "channel": "sms", "status": "approved"}, True),
    ({"sid": VERIFY_SID, "to": PHONE, "channel": "sms", "status": "pending"}, False),
    ({"sid": VERIFY_SID, "to": "+821099999999", "channel": "sms", "status": "approved"}, False),
    ({"sid": "VE" + "b" * 32, "to": PHONE, "channel": "sms", "status": "approved"}, False),
])
def test_verify_requires_exact_provider_receipt_binding(result, expected):
    transport = Transport([result])
    adapter = TwilioRecoveryVerifyAdapter(transport)
    assert adapter.verify(PHONE, VERIFY_SID, "123456") is expected
    assert transport.calls[0][0] == "VerificationCheck"


def test_definitive_provider_rejection_is_a_failed_code_not_unknown():
    transport = Transport([ProviderRejected("private")])
    adapter = TwilioRecoveryVerifyAdapter(transport)
    assert adapter.verify(PHONE, VERIFY_SID, "123456") is False


def test_ambiguous_provider_failure_propagates_for_unknown_outcome_quarantine():
    transport = Transport([TimeoutError("private")])
    adapter = TwilioRecoveryVerifyAdapter(transport)
    with pytest.raises(TimeoutError):
        adapter.verify(PHONE, VERIFY_SID, "123456")


def test_invalid_verification_input_never_reaches_provider():
    transport = Transport([])
    adapter = TwilioRecoveryVerifyAdapter(transport)
    assert adapter.verify(PHONE, "VE-invalid", "12") is False
    assert transport.calls == []


def test_adapter_repr_does_not_include_recipient():
    adapter = TwilioRecoveryVerifyAdapter(Transport([]))
    assert PHONE not in repr(adapter)
