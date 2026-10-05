"""Real session boundary + isolated durable ledger + fake catalog/writer."""
from datetime import timedelta
import socket

from fastapi import Request
from pydantic import ValidationError
import pytest
import requests

from test_shop_ai_001b3_session_api import (
    api, clients, issue, auth_headers, ORIGIN, SECRET, COOKIE_NAME, CSRF_HEADER,
)
from test_shop_order_001c_catalog_resolution import Catalog, Writer, product
from core.api.dependencies.customer_session import SessionAPIDenied
from core.api.dependencies.order_create import (
    OrderCreateIntent, SessionBoundOrderCreateApplication,
)
from core.shopping.order_core import (
    OrderCreateService, SQLiteOrderCreateLedger, ShoppingServiceOrderCatalogResolver,
    OrderCreateOperationConflict, OrderCreateOperationUnknownOutcome,
    OrderCreateAmbiguousFailure,
)
from core.shopping.product_drafts.persistence.path_policy import IsolatedTestDatabasePathPolicy


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("external I/O forbidden")
    for name in ("connect", "connect_ex", "sendto"):
        monkeypatch.setattr(socket.socket, name, deny)
    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket, "getaddrinfo", deny)
    monkeypatch.setattr(requests.sessions.Session, "request", deny)


@pytest.fixture
def composed(api, tmp_path):
    store = SQLiteOrderCreateLedger(tmp_path / "orders.sqlite3", clock=lambda: api.time.now,
                                   path_policy=IsolatedTestDatabasePathPolicy(tmp_path))
    store.initialize()
    writer = Writer()
    orders = OrderCreateService(catalog_resolver=ShoppingServiceOrderCatalogResolver(Catalog(product())),
                               order_creator=writer, coordinator=store)
    app = SessionBoundOrderCreateApplication(session_boundary=api.boundary, order_service=orders)
    return app, store, writer


def intent(quantity=1):
    return OrderCreateIntent.model_validate({"line_items": [{"product_id": "123", "quantity": quantity}],
                                            "idempotency_key": "order-session-001"})


def request(headers):
    return Request({"type": "http", "method": "POST", "path": "/isolated-unmounted-order",
                    "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()]})


def authenticated_request(api):
    response = issue(api)
    return request({**auth_headers(response), "Cookie": COOKIE_NAME + "=" + SECRET})


def test_real_boundary_durable_completion_and_refreshed_replay(api, composed):
    app, store, writer = composed
    req = authenticated_request(api)
    first = app.execute(req, intent())
    evidence = store.inspect_operation("order-session-001")
    api.time.now += timedelta(seconds=1)
    replay = app.execute(req, intent())
    assert not first.idempotent_replay and replay.idempotent_replay
    assert len(writer.calls) == 1
    assert store.inspect_operation("order-session-001") == evidence
    assert SECRET not in repr(evidence)


@pytest.mark.parametrize("case", ["origin", "csrf", "cookie", "duplicate_cookie", "duplicate_csrf", "expired", "revoked"])
def test_auth_failures_never_claim_or_call_writer(api, composed, case):
    app, store, writer = composed
    req = authenticated_request(api)
    headers = dict(req.headers)
    if case == "origin": headers["origin"] = "https://evil.example.test"
    if case == "csrf": headers[CSRF_HEADER.lower()] = "0" * 64
    if case == "cookie": headers["cookie"] = COOKIE_NAME + "=" + "x" * 43
    if case == "duplicate_cookie": headers["cookie"] += "; " + COOKIE_NAME + "=" + SECRET
    if case == "expired": api.time.now += timedelta(minutes=30)
    if case == "revoked":
        projection = api.boundary.authenticate(SECRET, now=api.time.now)
        api.boundary.revoke(SECRET, projection, now=api.time.now)
    req = request(headers)
    if case == "duplicate_csrf": req.scope["headers"].append((b"x-csrf-token", headers["x-csrf-token"].encode()))
    with pytest.raises(SessionAPIDenied): app.execute(req, intent())
    assert store.inspect_operation("order-session-001") is None
    assert writer.calls == []


def test_changed_intent_conflicts_before_second_writer(api, composed):
    app, store, writer = composed
    req = authenticated_request(api)
    app.execute(req, intent())
    with pytest.raises(OrderCreateOperationConflict): app.execute(req, intent(quantity=2))
    assert len(writer.calls) == 1


@pytest.mark.parametrize("field", ["customer_id", "session_id", "authorization_reference", "requested_at",
                                   "correlation_id", "audit_reference", "price", "payment", "billing"])
def test_browser_cannot_supply_authority_or_commerce_truth(field):
    payload = {"line_items": [{"product_id": "123"}], "idempotency_key": "order-001", field: "forged"}
    with pytest.raises(ValidationError): OrderCreateIntent.model_validate(payload)


def test_public_projection_cannot_replace_session_boundary(api, composed):
    app, store, writer = composed
    authenticated_request(api)
    projection = api.boundary.authenticate(SECRET, now=api.time.now)
    with pytest.raises(TypeError):
        SessionBoundOrderCreateApplication(session_boundary=projection, order_service=app._orders)


def test_constructed_invalid_intent_fails_before_claim(api, composed):
    app, store, writer = composed
    req = authenticated_request(api)
    forged = OrderCreateIntent.model_construct(line_items=(), idempotency_key="bad key")
    with pytest.raises(ValidationError): app.execute(req, forged)
    assert writer.calls == []
    assert store.inspect_operation("order-session-001") is None


def test_replay_requires_current_authentication_even_when_completed(api, composed):
    app, store, writer = composed
    req = authenticated_request(api)
    app.execute(req, intent())
    projection = api.boundary.authenticate(SECRET, now=api.time.now)
    api.boundary.revoke(SECRET, projection, now=api.time.now)
    with pytest.raises(SessionAPIDenied): app.execute(req, intent())
    assert len(writer.calls) == 1


def test_unknown_provider_outcome_blocks_next_authenticated_attempt(api, composed):
    app, store, writer = composed
    req = authenticated_request(api)
    def ambiguous(command):
        writer.calls.append(command)
        raise OrderCreateAmbiguousFailure("TEST_UNKNOWN")
    writer.create_order = ambiguous
    with pytest.raises(OrderCreateAmbiguousFailure): app.execute(req, intent())
    with pytest.raises(OrderCreateOperationUnknownOutcome): app.execute(req, intent())
    assert len(writer.calls) == 1


def test_same_customer_different_session_cannot_replay(api, composed):
    from test_shop_ai_001b3_session_api import SECOND_PAYLOAD, SECOND_SECRET
    app, store, writer = composed
    app.execute(authenticated_request(api), intent())
    api.client.cookies.clear()  # Independent browser session issuance.
    response = issue(api, payload=SECOND_PAYLOAD)
    other = request({**auth_headers(response), "Cookie": COOKIE_NAME + "=" + SECOND_SECRET})
    with pytest.raises(OrderCreateOperationConflict): app.execute(other, intent())
    assert len(writer.calls) == 1


def test_session_storage_unavailable_denies_before_claim(api, composed):
    from core.shopping.customer_session_service import SessionValidation, SessionValidationCode
    app, store, writer = composed
    req = authenticated_request(api)
    api.service.validate_session.return_value = SessionValidation(code=SessionValidationCode.STORAGE_UNAVAILABLE)
    with pytest.raises(SessionAPIDenied): app.execute(req, intent())
    assert store.inspect_operation("order-session-001") is None
    assert writer.calls == []


def test_missing_origin_or_missing_csrf_denied_before_claim(api, composed):
    app, store, writer = composed
    req = authenticated_request(api)
    for key in ("origin", "x-csrf-token"):
        headers = dict(req.headers)
        headers.pop(key)
        with pytest.raises(SessionAPIDenied): app.execute(request(headers), intent())
    assert store.inspect_operation("order-session-001") is None
    assert writer.calls == []


def test_writer_observes_durable_claim_before_call(api, composed):
    app, store, writer = composed
    req = authenticated_request(api)
    original = writer.create_order
    def check_claim(command):
        assert store.inspect_operation("order-session-001")["state"] == "CLAIMED"
        return original(command)
    writer.create_order = check_claim
    app.execute(req, intent())
    assert len(writer.calls) == 1
