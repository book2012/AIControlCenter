"""Unregistered router in isolated ASGI with real auth and fake order writer."""
from pathlib import Path
import json
from datetime import timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from test_shop_order_001c_session_composition import api, clients, composed, deny_network
from test_shop_ai_001b3_session_api import issue, auth_headers, ORIGIN, SECRET, COOKIE_NAME, CSRF_HEADER
from core.api.routes.order_create import router, get_order_create_application, MAX_REQUEST_BYTES
from core.shopping.order_core import OrderCreateAmbiguousFailure, OrderCreateDefinitiveFailure

PATH = "/shopping/orders"
PAYLOAD = {"line_items": [{"product_id": "123", "quantity": 1}], "idempotency_key": "order-session-001"}


@pytest.fixture
def http(api, composed):
    application, store, writer = composed
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_order_create_application] = lambda: application
    with TestClient(app, base_url=ORIGIN) as client:
        yield client, store, writer


def headers(api):
    response = issue(api)
    return {**auth_headers(response), "Cookie": COOKIE_NAME + "=" + SECRET}


def safe(response):
    assert response.headers["cache-control"] == "no-store"
    assert "access-control-allow-origin" not in response.headers
    assert CSRF_HEADER not in response.headers
    for forbidden in (SECRET, "AG-CUS-", "AG-SES-", "order-auth-", "order-corr-", "order-audit-",
                      "command_digest", "customer_reference", "synthetic-private-provider-detail"):
        assert forbidden not in response.text


def code(response, status, suffix):
    safe(response)
    assert response.status_code == status, response.text
    assert response.json()["detail"]["code"] == "order_create_" + suffix
    assert set(response.json()["detail"]) == {"code", "message"}


def test_created_and_completed_replay_have_closed_public_result(api, http):
    client, store, writer = http
    auth = headers(api)
    first = client.post(PATH, json=PAYLOAD, headers=auth)
    safe(first)
    assert first.status_code == 201
    assert first.json() == {"outcome": "COMPLETED", "provider_order_id": 501,
                            "status": "pending", "currency": "KRW", "total": "10000",
                            "total_tax": "0", "idempotent_replay": False}
    api.time.now += timedelta(seconds=1)
    replay = client.post(PATH, json=PAYLOAD, headers=auth)
    safe(replay)
    assert replay.status_code == 200 and replay.json()["idempotent_replay"] is True
    assert len(writer.calls) == 1


@pytest.mark.parametrize("field", ["customer_id", "session_id", "price", "total", "billing", "payment",
                                   "requested_at", "authorization_reference"])
def test_extra_fields_are_redacted_and_never_claim(api, http, field):
    client, store, writer = http
    response = client.post(PATH, json={**PAYLOAD, field: SECRET}, headers=headers(api))
    code(response, 422, "invalid_request")
    assert store.inspect_operation("order-session-001") is None and writer.calls == []


@pytest.mark.parametrize("payload", [{}, {**PAYLOAD, "line_items": []},
    {**PAYLOAD, "line_items": [{"product_id": 123}]},
    {**PAYLOAD, "line_items": [{"product_id": "123", "quantity": True}]},
    {**PAYLOAD, "line_items": [{"product_id": "123", "quantity": 1001}]},
    {**PAYLOAD, "line_items": [{"product_id": "123", "price": "100"}]},
    {**PAYLOAD, "idempotency_key": "bad key"}])
def test_invalid_intent_is_bounded(api, http, payload):
    client, store, writer = http
    code(client.post(PATH, json=payload, headers=headers(api)), 422, "invalid_request")
    assert writer.calls == []


def test_malformed_json_and_duplicate_product_rejected(api, http):
    client, store, writer = http
    auth = headers(api)
    code(client.post(PATH, content='{"secret":"' + SECRET, headers={**auth, "Content-Type": "application/json"}), 422, "invalid_request")
    code(client.post(PATH, json={**PAYLOAD, "line_items": PAYLOAD["line_items"] * 2}, headers=auth), 422, "invalid_request")
    assert store.inspect_operation("order-session-001") is None and writer.calls == []


@pytest.mark.parametrize("case,status,suffix", [("cookie",401,"denied"), ("origin",403,"origin_denied"),
    ("csrf",403,"csrf_denied"), ("expired",401,"denied"), ("revoked",401,"denied")])
def test_auth_errors_are_public_and_preclaim(api, http, case, status, suffix):
    client, store, writer = http
    auth = headers(api)
    if case == "cookie": auth["Cookie"] = COOKIE_NAME + "=" + "x" * 43
    if case == "origin": auth["Origin"] = "https://evil.example.test"
    if case == "csrf": auth[CSRF_HEADER] = "0" * 64
    if case == "expired": api.time.now += timedelta(minutes=30)
    if case == "revoked":
        projection = api.boundary.authenticate(SECRET, now=api.time.now)
        api.boundary.revoke(SECRET, projection, now=api.time.now)
    response = client.post(PATH, json=PAYLOAD, headers=auth)
    code(response, status, suffix)
    if status == 401:
        assert "__Host-aicc_customer=" in response.headers["set-cookie"]
        assert "Secure" in response.headers["set-cookie"] and "HttpOnly" in response.headers["set-cookie"]
    assert store.inspect_operation("order-session-001") is None and writer.calls == []


def test_conflict_does_not_repeat_provider(api, http):
    client, store, writer = http
    auth = headers(api)
    assert client.post(PATH, json=PAYLOAD, headers=auth).status_code == 201
    changed = {**PAYLOAD, "line_items": [{"product_id": "123", "quantity": 2}]}
    code(client.post(PATH, json=changed, headers=auth), 409, "conflict")
    assert len(writer.calls) == 1


@pytest.mark.parametrize("error,first_status,first_code,next_code", [
    (OrderCreateAmbiguousFailure("TEST_UNKNOWN"),409,"unknown_outcome","unknown_outcome"),
    (OrderCreateDefinitiveFailure("TEST_REJECTED"),422,"provider_rejected","terminal_failed"),
    (RuntimeError("synthetic-private-provider-detail"),500,"internal_error","unknown_outcome")])
def test_writer_errors_redacted_and_next_call_blocked(api, http, error, first_status, first_code, next_code):
    client, store, writer = http
    auth = headers(api)
    def fail(command):
        writer.calls.append(command)
        raise error
    writer.create_order = fail
    code(client.post(PATH, json=PAYLOAD, headers=auth), first_status, first_code)
    code(client.post(PATH, json=PAYLOAD, headers=auth), 409, next_code)
    assert len(writer.calls) == 1


@pytest.mark.parametrize("method", ["GET", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def test_unsupported_methods_are_no_store(http, method):
    client, store, writer = http
    response = client.request(method, PATH)
    assert response.status_code == 405 and response.headers["allow"] == "POST"
    assert response.headers["cache-control"] == "no-store"
    assert writer.calls == []


def test_slash_variant_is_handled_without_redirect(api, http):
    client, store, writer = http
    response = client.post(PATH + "/", json=PAYLOAD, headers=headers(api), follow_redirects=False)
    assert response.status_code == 201 and "location" not in response.headers
    safe(response)


def test_no_default_composition_and_no_prod_registration():
    app = FastAPI()
    app.include_router(router)
    with TestClient(app, base_url=ORIGIN) as client:
        code(client.post(PATH, json=PAYLOAD), 503, "unavailable")
    source = (Path(__file__).resolve().parents[1] / "core/api/app.py").read_text()
    assert "routes.order_create" not in source


@pytest.mark.parametrize("advertised", [None, "1"])
def test_actual_body_limit_prevents_claim(api, http, advertised):
    client, store, writer = http
    auth = headers(api)
    if advertised is not None: auth["Content-Length"] = advertised
    def body():
        yield b" " * 16000
        yield b" " * (MAX_REQUEST_BYTES - 16000 + 1)
    code(client.post(PATH, content=body(), headers={**auth, "Content-Type": "application/json"}), 413, "request_too_large")
    assert writer.calls == [] and store.inspect_operation("order-session-001") is None


def test_catalog_rejection_has_bounded_error_and_terminal_replay(api, http, composed):
    from core.shopping.order_core import OrderCreateCatalogResolutionError
    client, store, writer = http
    application, _, _ = composed
    auth = headers(api)
    def reject(command):
        raise OrderCreateCatalogResolutionError("synthetic-private-provider-detail")
    application._orders._catalog_resolver.resolve = reject
    code(client.post(PATH, json=PAYLOAD, headers=auth), 422, "catalog_rejected")
    code(client.post(PATH, json=PAYLOAD, headers=auth), 409, "terminal_failed")
    assert writer.calls == []


def test_ledger_unavailable_has_no_writer_call(api, http):
    import sqlite3
    client, store, writer = http
    auth = headers(api)
    def unavailable(*args):
        raise sqlite3.OperationalError("synthetic-private-provider-detail")
    store.claim = unavailable
    code(client.post(PATH, json=PAYLOAD, headers=auth), 503, "unavailable")
    assert writer.calls == []


def test_inflight_claim_is_not_reissued(api, http):
    from core.shopping.order_core import OrderCreateCommand, OrderCreateLine, OrderCreateAuthority
    client, store, writer = http
    auth = headers(api)
    projection = api.boundary.authenticate(SECRET, now=api.time.now)
    cmd = OrderCreateCommand(customer_id=projection.customer_id, line_items=(OrderCreateLine("123"),),
        idempotency_key="order-session-001", correlation_id="test-corr", audit_reference="test-audit",
        requested_at=api.time.now)
    authority = OrderCreateAuthority(projection.customer_id, projection.id, "test-auth", api.time.now,
                                     api.time.now + timedelta(seconds=30))
    store.claim(cmd, authority)
    code(client.post(PATH, json=PAYLOAD, headers=auth), 409, "in_flight")
    assert writer.calls == []


def test_postwrite_contract_mismatch_is_unknown_and_not_retried(api, http):
    from dataclasses import replace
    client, store, writer = http
    auth = headers(api)
    original = writer.create_order
    def mismatch(command):
        snapshot = original(command)
        return replace(snapshot, line_items=(replace(snapshot.line_items[0], quantity=2),))
    writer.create_order = mismatch
    code(client.post(PATH, json=PAYLOAD, headers=auth), 409, "unknown_outcome")
    code(client.post(PATH, json=PAYLOAD, headers=auth), 409, "unknown_outcome")
    assert len(writer.calls) == 1


def test_duplicate_cookie_and_csrf_are_denied_before_claim(api, http):
    client, store, writer = http
    auth = headers(api)
    duplicate_cookie = {**auth, "Cookie": auth["Cookie"] + "; " + auth["Cookie"]}
    code(client.post(PATH, json=PAYLOAD, headers=duplicate_cookie), 401, "denied")
    repeated = list(auth.items()) + [(CSRF_HEADER, auth[CSRF_HEADER])]
    code(client.post(PATH, json=PAYLOAD, headers=repeated), 403, "csrf_denied")
    assert writer.calls == [] and store.inspect_operation("order-session-001") is None
