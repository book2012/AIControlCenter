from __future__ import annotations

import requests

from core.shopping.adapters.woocommerce_read_transport import WooCommerceReadTransportSession

class Response:
    def __init__(self, status_code, headers=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.closed = False

    def close(self):
        self.closed = True

class Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, *, params, auth, headers, timeout, allow_redirects):
        self.calls.append({"timeout": timeout, "allow_redirects": allow_redirects})
        return self.responses.pop(0)

class Clock:
    def __init__(self, values):
        self.values = iter(values)

    def __call__(self):
        return next(self.values)

def test_connect_read_timeout_and_redirect_policy():
    session = Session([Response(200)])
    transport = WooCommerceReadTransportSession(session=session, monotonic=Clock([0.0, 0.0, 1.0]))
    response = transport.get("https://shop.example", allow_redirects=False)
    assert response.status_code == 200
    assert session.calls[0]["timeout"] == (5.0, 15.0)
    assert session.calls[0]["allow_redirects"] is False

def test_retry_statuses_make_exactly_one_get_attempt():
    for status_code in (429, 502, 503, 504):
        session = Session([Response(status_code), Response(200)])
        transport = WooCommerceReadTransportSession(
            session=session,
            max_retries=99,
            monotonic=Clock([0.0, 1.0, 1.0]),
        )
        response = transport.get("https://shop.example")
        assert response.status_code == status_code
        assert len(session.calls) == 1

def test_retry_after_cannot_sleep_or_retry():
    sleeps = []
    session = Session([Response(429, {"Retry-After": "60"}), Response(200)])
    transport = WooCommerceReadTransportSession(
        session=session,
        max_retries=1,
        retry_after_max_seconds=5.0,
        monotonic=Clock([0.0, 1.0, 1.0]),
        sleep=sleeps.append,
    )
    response = transport.get("https://shop.example")
    assert response.status_code == 429
    assert len(session.calls) == 1
    assert sleeps == []

def test_non_retry_status_does_not_retry():
    session = Session([Response(400)])
    transport = WooCommerceReadTransportSession(session=session, monotonic=Clock([0.0, 0.0, 1.0]))
    response = transport.get("https://shop.example")
    assert response.status_code == 400
    assert len(session.calls) == 1

def test_total_deadline_guard():
    response = Response(200)
    session = Session([response])
    transport = WooCommerceReadTransportSession(session=session, total_timeout_seconds=20.0, monotonic=Clock([0.0, 0.0, 21.0]))
    try:
        transport.get("https://shop.example")
    except requests.Timeout:
        pass
    else:
        raise AssertionError("expected total timeout")
    assert response.closed is True
