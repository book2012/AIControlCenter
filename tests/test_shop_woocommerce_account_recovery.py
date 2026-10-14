import json
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from core.shopping.adapters.woocommerce_account_recovery import (
    WooCommerceAccountRecoveryAdapter, WooRecoveryAdapterError,
)


PHONE = "+821012345678"
ACCOUNT = {
    "match": True,
    "account_ref": "woo-customer:42",
    "login_id": "hong123",
    "full_name": "홍길동",
    "phone": PHONE,
}


class Response:
    def __init__(self, body, *, status=200, headers=None):
        self.status_code = status
        self.headers = headers or {"Cache-Control": "no-store, private"}
        self.body = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.closed = False

    def iter_content(self, chunk_size):
        for start in range(0, len(self.body), chunk_size):
            yield self.body[start:start + chunk_size]

    def close(self):
        self.closed = True


class Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.trust_env = True

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def make_adapter(responses):
    session = Session(responses)
    adapter = WooCommerceAccountRecoveryAdapter(
        base_url="https://dev.bokstory.duckdns.org",
        service_username="aicc-recovery-dev",
        application_password=SecretStr("private-app-password"),
        session=session,
    )
    return adapter, session


def test_exact_name_phone_lookup_returns_validated_account_and_scoped_request():
    adapter, session = make_adapter([Response(ACCOUNT)])
    result = adapter.find_by_name_phone("홍길동", PHONE)
    assert result.account_ref == "woo-customer:42"
    assert result.login_id == "hong123"
    url, request = session.calls[0]
    assert url.endswith("/lookup-id")
    assert request["json"] == {"name": "홍길동", "phone": PHONE}
    assert request["auth"] == ("aicc-recovery-dev", "private-app-password")
    assert request["allow_redirects"] is False
    assert request["headers"]["Cache-Control"] == "no-store"
    assert session.trust_env is False


def test_nonmatching_lookup_is_generic():
    adapter, _ = make_adapter([Response({"match": False})])
    assert adapter.find_by_name_phone("없는 이름", PHONE) is None


def test_password_lookup_uses_exact_requested_tuple():
    adapter, session = make_adapter([Response(ACCOUNT)])
    result = adapter.find_by_login_name_phone("hong123", "홍길동", PHONE)
    assert result.account_ref == "woo-customer:42"
    assert result.login_id == "hong123"
    assert session.calls[0][1]["json"] == {
        "login_id": "hong123", "name": "홍길동", "phone": PHONE,
    }


def test_phone_or_name_mismatch_in_provider_response_is_rejected():
    adapter, _ = make_adapter([Response({**ACCOUNT, "phone": "+821099999999"})])
    with pytest.raises(WooRecoveryAdapterError):
        adapter.find_by_name_phone("홍길동", PHONE)


def test_verified_account_resolution_binds_account_ref_and_phone():
    adapter, session = make_adapter([Response(ACCOUNT)])
    account = adapter.find_by_ref_phone("woo-customer:42", PHONE)
    assert account.full_name == "홍길동"
    assert session.calls[0][1]["json"] == {
        "account_ref": "woo-customer:42", "phone": PHONE,
    }


def test_password_change_is_single_narrow_request_and_validates_receipt():
    adapter, session = make_adapter([Response({
        "changed": True, "account_ref": "woo-customer:42",
    })])
    assert adapter.change_password("woo-customer:42", "new-password-123") is True
    url, request = session.calls[0]
    assert url.endswith("/change-password")
    assert request["json"] == {
        "account_ref": "woo-customer:42", "new_password": "new-password-123",
    }
    assert "new-password-123" not in repr(adapter)


def test_invalid_account_or_password_is_rejected_before_network():
    adapter, session = make_adapter([])
    assert adapter.change_password("woo-customer:0", "new-password-123") is False
    assert adapter.change_password("woo-customer:42", "short") is False
    assert session.calls == []


def test_redirect_http_error_or_cacheable_reply_fails_closed():
    for response in (
        Response(ACCOUNT, status=302),
        Response(ACCOUNT, status=500),
        Response(ACCOUNT, headers={"Cache-Control": "private"}),
    ):
        adapter, _ = make_adapter([response])
        with pytest.raises(WooRecoveryAdapterError):
            adapter.find_by_name_phone("홍길동", PHONE)


def test_response_size_and_duplicate_keys_are_rejected():
    adapter, _ = make_adapter([Response(b'{"match":false,"match":true}')])
    with pytest.raises(WooRecoveryAdapterError):
        adapter.find_by_name_phone("홍길동", PHONE)


def test_origin_must_be_the_fixed_dev_storefront():
    for origin in (
        "http://dev.bokstory.duckdns.org",
        "https://evil.example",
        "https://dev.bokstory.duckdns.org/path",
        "https://user@dev.bokstory.duckdns.org",
    ):
        with pytest.raises(ValueError):
            WooCommerceAccountRecoveryAdapter(
                base_url=origin,
                service_username="aicc-recovery-dev",
                application_password=SecretStr("private"),
                session=SimpleNamespace(),
            )


def test_adapter_repr_does_not_expose_service_identity_or_password():
    adapter, _ = make_adapter([])
    rendered = repr(adapter)
    assert "private-app-password" not in rendered
    assert "aicc-recovery-dev" not in rendered
