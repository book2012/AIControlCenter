from types import SimpleNamespace

import pytest

from core.shopping.adapters.twilio_recovery_messaging import (
    TwilioMessageReceipt,
    TwilioRecoveryLinkSMS,
    TwilioRecoveryMessagingConfig,
    TwilioRecoveryMessagingError,
)


ACCOUNT = "AC" + "a" * 32
SERVICE = "MG" + "b" * 32
MESSAGE = "SM" + "c" * 32
CFG = {
    "environment": "DEV",
    "credentials": {
        "account_sid": ACCOUNT,
        "auth_token": "TEST_AUTH_TOKEN_NOT_REAL",
        "messaging_service_sid": SERVICE,
    },
    "test_phone": "+821012345678",
    "allowed_link_hosts": ["dev.bokstory.duckdns.org"],
}
PHONE = "+821012345678"
BODY = "agachichi 비밀번호 재설정: https://dev.bokstory.duckdns.org/my-account/reset-password/?key=secret"


class Session:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append(("POST", args, kwargs))
        if self.error:
            raise self.error
        return self.response

    def get(self, *args, **kwargs):
        self.calls.append(("GET", args, kwargs))
        if self.error:
            raise self.error
        return self.response


def response(status=201, *, sid=MESSAGE, state="queued", to=PHONE, service=SERVICE):
    payload = {
        "sid": sid,
        "status": state,
        "to": to,
        "messaging_service_sid": service,
    }
    raw = __import__("json").dumps(payload).encode()
    return SimpleNamespace(
        status_code=status,
        iter_content=lambda chunk_size: iter([raw]),
        close=lambda: None,
    )


def adapter(session):
    return TwilioRecoveryLinkSMS(TwilioRecoveryMessagingConfig.from_mapping(CFG), session=session)


def test_config_requires_dev_messaging_service_and_repr_hides_credentials():
    with pytest.raises(ValueError, match="CONFIGURATION_REQUIRED"):
        TwilioRecoveryMessagingConfig.from_mapping({
            **CFG,
            "credentials": {"account_sid": ACCOUNT, "auth_token": "secret"},
        })
    with pytest.raises(ValueError, match="CONFIGURATION_REQUIRED"):
        TwilioRecoveryMessagingConfig.from_mapping({**CFG, "test_phone": "+12025550123"})
    with pytest.raises(ValueError, match="DEV_ONLY"):
        TwilioRecoveryMessagingConfig.from_mapping({**CFG, "environment": "PROD"})
    config = TwilioRecoveryMessagingConfig.from_mapping(CFG)
    assert "TEST_AUTH_TOKEN_NOT_REAL" not in repr(config)


def test_send_is_single_attempt_pinned_and_receipt_bound():
    session = Session(response())
    client = adapter(session)
    receipt = client.send(PHONE, BODY, "recovery-event-0001")
    assert receipt == TwilioMessageReceipt(
        "recovery-event-0001", MESSAGE, "QUEUED",
        "DEV_FIXED_TEST_RECIPIENT",
    )
    assert len(session.calls) == 1
    method, args, kwargs = session.calls[0]
    assert method == "POST"
    assert args[0] == f"https://api.twilio.com/2010-04-01/Accounts/{ACCOUNT}/Messages.json"
    assert kwargs["allow_redirects"] is False
    assert kwargs["auth"] == (ACCOUNT, "TEST_AUTH_TOKEN_NOT_REAL")
    assert kwargs["data"]["MessagingServiceSid"] == SERVICE
    assert kwargs["data"]["To"] == PHONE


def test_unknown_send_is_not_retried_and_does_not_leak_error():
    session = Session(error=TimeoutError("private transport details"))
    client = adapter(session)
    with pytest.raises(TwilioRecoveryMessagingError) as caught:
        client.send(PHONE, BODY, "recovery-event-0002")
    assert caught.value.code == "UNKNOWN_OUTCOME"
    assert "private transport details" not in str(caught.value)
    assert len(session.calls) == 1


def test_reconcile_requires_exact_bound_recipient_and_service():
    session = Session(response(state="delivered"))
    client = adapter(session)
    initial = client.send(PHONE, BODY, "recovery-event-0003")
    session.response = response(status=200, state="delivered")
    session.response = response(status=200, state="delivered")
    checked = client.reconcile(initial)
    assert checked.state == "DELIVERED"
    assert len(session.calls) == 2
    session.response = response(status=200, state="delivered", to="+821099999999")
    with pytest.raises(TwilioRecoveryMessagingError) as caught:
        client.reconcile(initial)
    assert caught.value.code == "RECEIPT_MISMATCH"


@pytest.mark.parametrize("body", [
    "https://evil.example/reset?key=x",
    "https://dev.bokstory.duckdns.org.evil.example/reset?key=x",
    "http://dev.bokstory.duckdns.org/reset?key=x",
    "https://dev.bokstory.duckdns.org/reset?key=x https://evil.example",
])
def test_reset_link_host_is_allowlisted(body):
    client = adapter(Session(response()))
    with pytest.raises(TwilioRecoveryMessagingError) as caught:
        client.send(PHONE, body, "recovery-event-0004")
    assert caught.value.code == "INVALID_REQUEST"


def test_rejects_non_korean_test_recipient_and_malformed_provider_receipt():
    client = adapter(Session(response(to="+821099999999")))
    with pytest.raises(TwilioRecoveryMessagingError) as caught:
        client.send("+821099999999", BODY, "recovery-event-0005")
    assert caught.value.code == "INVALID_REQUEST"
    bad = adapter(Session(response(service="MG" + "d" * 32)))
    with pytest.raises(TwilioRecoveryMessagingError) as caught:
        bad.send(PHONE, BODY, "recovery-event-0006")
    assert caught.value.code == "RECEIPT_MISMATCH"
