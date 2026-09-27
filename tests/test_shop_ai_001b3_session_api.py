"""SHOP_AI_001B-3C: isolated ASGI, synthetic trusted evidence, temporary SQLite."""
import ast
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from http.cookies import SimpleCookie
import json
from pathlib import Path
import socket
import sqlite3
import sys
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretBytes
import pytest
import requests

from core.api.dependencies.customer_session import (
    COOKIE_NAME, CSRF_HEADER, CustomerSessionBoundary, TrustedSessionEvidence,
    get_customer_session_boundary,
)
from core.api.routes.customer_sessions import router
from core.api.schemas.customer_auth import VerificationReceiptConsumeRequest
from core.shopping import customer_persistence as persistence
from core.shopping.customer_auth import (
    TrustedReceiptBinding, TrustedVerificationContext, TrustedVerificationReceipt,
)
from core.shopping.customer_identity import Customer, CustomerState, VerifiedContactBinding
from core.shopping.customer_session_service import (
    CustomerSessionService, IssuedSession, ReceiptPolicyDenied,
    RevocationResult, SessionValidation, SessionValidationCode,
)
from core.shopping.customer_sessions import ABSOLUTE_LIFETIME, IDLE_LIFETIME, SafeSessionProjection


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://shop.example.test"
SESSION = "/shopping/auth/session"
LOGOUT = "/shopping/auth/logout"
NOW = datetime(2026, 9, 1, 0, 2, tzinfo=timezone.utc)
SECRET = "s" * 43
SECOND_SECRET = "t" * 43
CSRF_KEY = SecretBytes(b"synthetic-test-key-not-production" * 2)
PRIVATE_MARKER = "synthetic-phone-otp-contact-receipt-database-secret"


def reference(kind, digit):
    return f"AG-{kind}-" + digit * 12 + "4" + digit * 3 + "8" + digit * 15


CUSTOMER = reference("CUS", "1")
OTHER_CUSTOMER = reference("CUS", "9")
CONTACT = reference("CON", "2")
SESSION_ID = reference("SES", "6")
SECOND_SESSION_ID = reference("SES", "7")
RECEIPT = reference("VRF", "3")
ISSUER = reference("ISS", "5")
CHALLENGE = reference("CHL", "4")
PAYLOAD = {"receipt_id": "VRF-CLIENT01", "browser_challenge": "CHL-CLIENT01"}
SECOND_PAYLOAD = {"receipt_id": "VRF-CLIENT02", "browser_challenge": "CHL-CLIENT02"}


@pytest.fixture(autouse=True)
def isolated_io(monkeypatch, tmp_path):
    attempts = []
    connect = sqlite3.connect

    def deny(*args, **kwargs):
        attempts.append("external_or_runtime_access")
        raise AssertionError("Only isolated Mock I/O is permitted")

    def temporary_connect(database, *args, **kwargs):
        if (kwargs.get("uri") or database == ":memory:"
                or not Path(database).resolve().is_relative_to(tmp_path.resolve())):
            return deny()
        return connect(database, *args, **kwargs)

    for name in ("connect", "connect_ex", "sendto"):
        monkeypatch.setattr(socket.socket, name, deny)
    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket, "getaddrinfo", deny)
    monkeypatch.setattr(requests.sessions.Session, "request", deny)
    monkeypatch.setattr(sqlite3, "connect", temporary_connect)
    from core.config.loader import ConfigLoader
    monkeypatch.setattr(ConfigLoader, "load", deny)
    assert "core.api.app" not in sys.modules
    yield
    assert not attempts
    assert "core.api.app" not in sys.modules


@pytest.fixture
def clients():
    with ExitStack() as stack:
        def make(boundary=None, *, inject=True):
            app = FastAPI()
            app.include_router(router)
            if inject:
                app.dependency_overrides[get_customer_session_boundary] = lambda: boundary
            client = stack.enter_context(TestClient(app, base_url=ORIGIN))

            def response_guard(response):
                assert response.headers["cache-control"] == "no-store"
                assert "access-control-allow-origin" not in response.headers
                assert "access-control-expose-headers" not in response.headers

            client.event_hooks["response"].append(response_guard)
            return client

        yield make


@pytest.fixture
def api(tmp_path, clients):
    path = tmp_path / "synthetic-sessions.sqlite3"
    persistence.initialize_schema(path)
    customer = Customer(
        id=CUSTOMER, state="ACTIVE", created_at=NOW - timedelta(minutes=2), updated_at=NOW,
        contact_binding=VerifiedContactBinding(
            customer_id=CUSTOMER, state="VERIFIED", created_at=NOW - timedelta(minutes=2),
            updated_at=NOW, verified_at=NOW, contact_ref=CONTACT,
        ),
    )
    persistence.SQLiteCustomerSessionStore(path).save_customer(customer)
    secrets = iter((SECRET, SECOND_SECRET))
    ids = iter((SESSION_ID, SECOND_SESSION_ID))
    real = CustomerSessionService(str(path), secret_factory=lambda: next(secrets),
                                  session_id_factory=lambda: next(ids))
    service = Mock(spec=CustomerSessionService, wraps=real)
    time = SimpleNamespace(now=NOW)
    evidence = {}
    for payload, receipt_id in ((PAYLOAD, RECEIPT), (SECOND_PAYLOAD, reference("VRF", "8"))):
        receipt = TrustedVerificationReceipt(
            receipt_id=receipt_id, purpose="SESSION_ISSUANCE", browser_challenge=CHALLENGE,
            issuer_ref=ISSUER, customer_id=CUSTOMER, issued_at=NOW,
            expires_at=NOW + timedelta(minutes=5),
        )
        evidence[payload["receipt_id"], payload["browser_challenge"]] = TrustedSessionEvidence(
            receipt, TrustedVerificationContext(accepted_bindings=frozenset({
                TrustedReceiptBinding(receipt_id, ISSUER, CUSTOMER),
            })), CHALLENGE,
        )

    def resolve(payload):
        # Explicit test-owned trust only, never supplied by the request model.
        found = evidence.get((payload.receipt_id, payload.browser_challenge))
        if found is None:
            raise ReceiptPolicyDenied(PRIVATE_MARKER)
        return found

    resolver = Mock(side_effect=resolve)
    boundary = CustomerSessionBoundary(service=service, trusted_origin=ORIGIN, csrf_key=CSRF_KEY,
                                       clock=lambda: time.now, resolve_evidence=resolver)
    yield SimpleNamespace(client=clients(boundary), boundary=boundary, service=service, real=real,
                          resolver=resolver, evidence=evidence, time=time, path=path, customer=customer)


def issue(api, *, payload=None, headers=None):
    response = api.client.post(SESSION, json=payload or PAYLOAD, headers=headers or {"Origin": ORIGIN})
    assert response.status_code == 201, response.text
    return response


def auth_headers(response):
    return {"Origin": ORIGIN, CSRF_HEADER: response.headers[CSRF_HEADER]}


def error(response, status, code):
    messages = {
        "denied": "Customer session denied.",
        "invalid_request": "Invalid session request.",
        "origin_denied": "Request origin denied.",
        "csrf_denied": "Request verification denied.",
        "unavailable": "Customer session unavailable.",
        "internal_error": "Customer session request failed.",
        "method_denied": "Request method denied.",
    }
    assert response.status_code == status
    assert response.json() == {"detail": {"code": "customer_session_" + code, "message": messages[code]}}
    assert CSRF_HEADER not in response.headers
    for forbidden in (SECRET, SECOND_SECRET, CUSTOMER, CONTACT, RECEIPT, ISSUER, CHALLENGE, PRIVATE_MARKER):
        assert forbidden not in response.text


def cleared(response):
    cookie = SimpleCookie(response.headers["set-cookie"])[COOKIE_NAME]
    assert cookie.value == ""
    assert cookie["max-age"] == "0"
    assert cookie["secure"] and cookie["httponly"]
    assert cookie["path"] == "/" and not cookie["domain"]
    assert cookie["samesite"].lower() == "strict"


def test_isolated_composition_and_trusted_creation(api):
    paths = api.client.app.openapi()["paths"]
    assert {path: set(operations) for path, operations in paths.items()} == {
        SESSION: {"get", "post"}, LOGOUT: {"post"},
    }
    response = issue(api)
    api.resolver.assert_called_once_with(VerificationReceiptConsumeRequest(**PAYLOAD))
    call = api.service.consume_receipt_and_create_session.call_args
    assert call.args[0] is api.evidence[PAYLOAD["receipt_id"], PAYLOAD["browser_challenge"]].receipt
    assert call.kwargs["trusted_context"].accepted_bindings
    assert call.kwargs["expected_challenge"] == CHALLENGE
    assert response.json()["customer_id"] == CUSTOMER
    assert api.service.validate_session.call_count == 1


def test_cookie_is_opaque_and_has_every_required_attribute(api):
    response = issue(api)
    assert len(response.headers.get_list("set-cookie")) == 1
    cookies = SimpleCookie(response.headers["set-cookie"])
    assert list(cookies) == [COOKIE_NAME]
    cookie = cookies[COOKIE_NAME]
    assert cookie.value == SECRET
    assert cookie["secure"] and cookie["httponly"] and cookie["path"] == "/"
    assert cookie["domain"] == "" and cookie["samesite"].lower() == "strict"
    assert int(cookie["max-age"]) == 1800
    assert parsedate_to_datetime(cookie["expires"]) == NOW + IDLE_LIFETIME
    assert parsedate_to_datetime(cookie["expires"]) <= NOW + ABSOLUTE_LIFETIME
    assert all(value not in cookie.value for value in (CUSTOMER, SESSION_ID, RECEIPT, CONTACT, ISSUER))


def test_projection_is_the_existing_explicit_allowlist_and_no_secret_logs(api, caplog):
    created = issue(api)
    current = api.client.get(SESSION)
    assert current.status_code == 200
    assert current.json() == created.json()
    assert set(current.json()) == set(SafeSessionProjection.model_fields)
    for response in (created, current):
        for forbidden in (SECRET, CONTACT, RECEIPT, ISSUER, CHALLENGE, "session_secret_hash", "otp", "phone"):
            assert forbidden not in response.text
        assert response.headers[CSRF_HEADER] not in response.text
    assert "set-cookie" not in current.headers  # No idle or absolute lifetime renewal.
    assert SECRET not in repr(api.boundary._bindings)
    assert created.headers[CSRF_HEADER] not in repr(api.boundary._bindings)
    assert all(value not in caplog.text for value in (SECRET, CONTACT, RECEIPT, created.headers[CSRF_HEADER]))


@pytest.mark.parametrize("field", ["customer_id", "identity", "verified_phone_number", "phone_number",
                                  "issuer_ref", "issuer_name", "verified", "verification", "otp",
                                  "trusted_context", "session_secret"])
def test_client_authentication_claims_are_rejected(api, field):
    response = api.client.post(SESSION, json={**PAYLOAD, field: True}, headers={"Origin": ORIGIN})
    error(response, 422, "invalid_request")
    api.resolver.assert_not_called()
    api.service.consume_receipt_and_create_session.assert_not_called()


@pytest.mark.parametrize("change", [{"receipt_id": "VRF-FORGED01"}, {"browser_challenge": "CHL-FORGED01"}])
def test_syntactically_valid_references_do_not_prove_trust(api, change):
    response = api.client.post(SESSION, json={**PAYLOAD, **change}, headers={"Origin": ORIGIN})
    error(response, 401, "denied")
    api.service.consume_receipt_and_create_session.assert_not_called()


def test_real_service_still_requires_trusted_verifier_evidence(api):
    key = PAYLOAD["receipt_id"], PAYLOAD["browser_challenge"]
    original = api.evidence[key]
    api.evidence[key] = TrustedSessionEvidence(original.receipt, TrustedVerificationContext(), CHALLENGE)
    error(api.client.post(SESSION, json=PAYLOAD, headers={"Origin": ORIGIN}), 401, "denied")
    with sqlite3.connect(api.path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM shopping_sessions").fetchone()[0] == 0


def test_receipt_replay_fails_closed(api):
    issue(api)
    api.client.cookies.clear()
    error(api.client.post(SESSION, json=PAYLOAD, headers={"Origin": ORIGIN}), 401, "denied")


@pytest.mark.parametrize("method,path", [("GET", SESSION), ("POST", SESSION), ("POST", LOGOUT)])
def test_missing_injection_is_unavailable(clients, method, path):
    client = clients(inject=False)
    error(client.request(method, path, json=PAYLOAD if path == SESSION and method == "POST" else None,
                         headers={"Origin": ORIGIN}), 503, "unavailable")


def test_no_resolver_does_not_provision_storage_or_issue(clients, tmp_path):
    path = tmp_path / "must-not-be-created.sqlite3"
    service = CustomerSessionService(str(path))
    boundary = CustomerSessionBoundary(service=service, trusted_origin=ORIGIN, csrf_key=CSRF_KEY,
                                       clock=lambda: NOW)
    client = clients(boundary)
    error(client.post(SESSION, json=PAYLOAD, headers={"Origin": ORIGIN}), 503, "unavailable")
    error(client.get(SESSION), 401, "denied")
    assert not path.exists()


@pytest.mark.parametrize("cookie", [None, "invalid", "z" * 43, "x" * 257, "legacy-inquiry-token"])
def test_missing_unknown_invalid_or_legacy_cookie_denied(api, cookie):
    headers = {} if cookie is None else {"Cookie": f"{COOKIE_NAME}={cookie}"}
    response = api.client.get(SESSION, headers=headers)
    error(response, 401, "denied")
    cleared(response)
    api.service.validate_session.assert_not_called()


def test_duplicate_cookie_denied(api):
    issue(api)
    response = api.client.get(SESSION, headers={"Cookie": f"{COOKIE_NAME}={SECRET}; {COOKIE_NAME}={SECOND_SECRET}"})
    error(response, 401, "denied")
    cleared(response)


@pytest.mark.parametrize("elapsed", [IDLE_LIFETIME, ABSOLUTE_LIFETIME])
def test_expired_session_uses_service_validation_and_denies(api, elapsed):
    issue(api)
    api.time.now += elapsed
    error(api.client.get(SESSION), 401, "denied")
    assert api.service.validate_session.call_args.kwargs["now"] == NOW + elapsed
    assert api.service.validate_session.call_count == 2


@pytest.mark.parametrize("change", ["revoked", "customer_mismatch", "secret_mismatch", "suspended", "contact_changed"])
def test_status_uses_current_durable_service_state(api, change):
    issue(api)
    if change == "revoked":
        api.real.revoke_session(SESSION_ID, now=NOW, actor_ref=CUSTOMER, correlation_id="test-revoke")
    elif change in {"suspended", "contact_changed"}:
        updates = ({"state": CustomerState.SUSPENDED} if change == "suspended" else {
            "contact_binding": api.customer.contact_binding.model_copy(update={"contact_ref": reference("CON", "8")})})
        persistence.SQLiteCustomerSessionStore(api.path).save_customer(api.customer.model_copy(update=updates))
    else:
        with sqlite3.connect(api.path) as connection:
            if change == "secret_mismatch":
                connection.execute("UPDATE shopping_sessions SET secret_hash=?", ("sha256:" + "0" * 64,))
            else:
                payload = json.loads(connection.execute("SELECT session_json FROM shopping_sessions").fetchone()[0])
                payload["customer_id"] = OTHER_CUSTOMER
                connection.execute("UPDATE shopping_sessions SET session_json=?", (json.dumps(payload),))
    response = api.client.get(SESSION)
    error(response, 401, "denied")
    cleared(response)
    assert api.service.validate_session.call_count == 2


@pytest.mark.parametrize("field,value", [("customer_id", OTHER_CUSTOMER), ("id", SECOND_SESSION_ID)])
def test_mismatched_service_projection_is_denied(api, field, value):
    created = issue(api)
    projection = SafeSessionProjection.model_validate({**created.json(), field: value})
    api.service.validate_session.return_value = SessionValidation("VALID", projection)
    error(api.client.get(SESSION), 401, "denied")


def test_logout_durable_revocation_and_cookie_deletion(api):
    created = issue(api)
    response = api.client.post(LOGOUT, headers=auth_headers(created))
    assert response.status_code == 200 and response.json() == {"schema_version": "1.0.0", "outcome": "REVOKED"}
    assert CSRF_HEADER not in response.headers
    cleared(response)
    api.service.revoke_session.assert_called_once()
    call = api.service.revoke_session.call_args
    assert call.args == (SESSION_ID,) and call.kwargs["actor_ref"] == CUSTOMER
    assert call.kwargs["correlation_id"] and call.kwargs["now"] == NOW
    reopened = CustomerSessionService(str(api.path))
    assert reopened.validate_session(SESSION_ID, SECRET, CUSTOMER, now=NOW).code == SessionValidationCode.INELIGIBLE
    with sqlite3.connect(api.path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM shopping_session_revocations").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM shopping_auth_audit WHERE action='SESSION_REVOKE'").fetchone()[0] == 1
    error(api.client.get(SESSION, headers={"Cookie": f"{COOKIE_NAME}={SECRET}"}), 401, "denied")


def test_revocation_audit_failure_is_not_success_and_can_be_retried(api, caplog):
    created = issue(api)

    def fail(_action):
        raise RuntimeError(PRIVATE_MARKER)

    api.real._audit_failure_hook = fail
    response = api.client.post(LOGOUT, headers=auth_headers(created))
    error(response, 503, "unavailable")
    assert "set-cookie" not in response.headers
    assert api.real.validate_session(SESSION_ID, SECRET, CUSTOMER, now=NOW).code == SessionValidationCode.VALID
    with sqlite3.connect(api.path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM shopping_session_revocations").fetchone()[0] == 0
    assert PRIVATE_MARKER not in caplog.text
    api.real._audit_failure_hook = None
    assert api.client.post(LOGOUT, headers=auth_headers(created)).status_code == 200


def test_unknown_revocation_result_is_not_success(api):
    created = issue(api)
    api.service.revoke_session.return_value = RevocationResult("PENDING")
    error(api.client.post(LOGOUT, headers=auth_headers(created)), 503, "unavailable")


@pytest.mark.parametrize("path", [SESSION, LOGOUT])
@pytest.mark.parametrize("origin", [None, "null", "https://evil.example.test", "http://shop.example.test",
                                    ORIGIN + ".evil.test", ORIGIN + "/", ORIGIN + ":443"])
def test_state_changes_require_exact_explicit_origin(api, path, origin):
    created = issue(api)
    headers = {CSRF_HEADER: created.headers[CSRF_HEADER], "Host": "evil.example.test",
               "X-Forwarded-Host": "shop.example.test", "X-Forwarded-Proto": "https",
               "Forwarded": "host=shop.example.test;proto=https", "Referer": ORIGIN + "/"}
    if origin is not None:
        headers["Origin"] = origin
    response = api.client.post(path, json=SECOND_PAYLOAD if path == SESSION else None, headers=headers)
    error(response, 403, "origin_denied")
    assert api.service.consume_receipt_and_create_session.call_count == 1
    api.service.revoke_session.assert_not_called()


@pytest.mark.parametrize("path", [SESSION, LOGOUT])
@pytest.mark.parametrize("site", ["cross-site", "same-site", "none"])
def test_contradictory_fetch_provenance_is_denied(api, path, site):
    created = issue(api)
    headers = {**auth_headers(created), "Sec-Fetch-Site": site}
    error(api.client.post(path, json=SECOND_PAYLOAD if path == SESSION else None, headers=headers), 403, "origin_denied")


@pytest.mark.parametrize("path", [SESSION, LOGOUT])
@pytest.mark.parametrize("token", [None, "chosen-by-caller", "0" * 64])
def test_cookie_authenticated_posts_require_verified_csrf(api, path, token):
    created = issue(api)
    headers = {"Origin": ORIGIN}
    if token is not None:
        headers[CSRF_HEADER] = token
    response = api.client.post(path, json=SECOND_PAYLOAD if path == SESSION else None, headers=headers)
    error(response, 403, "csrf_denied")
    assert api.service.consume_receipt_and_create_session.call_count == 1
    api.service.revoke_session.assert_not_called()
    assert created.headers[CSRF_HEADER] != token


def test_csrf_is_bound_to_session_and_server_key(api):
    first = issue(api)
    api.client.cookies.clear()
    second = issue(api, payload=SECOND_PAYLOAD)
    assert first.headers[CSRF_HEADER] != second.headers[CSRF_HEADER]
    error(api.client.post(LOGOUT, headers=auth_headers(first)), 403, "csrf_denied")
    api.boundary._csrf_key = SecretBytes(b"another-synthetic-server-key-value")
    error(api.client.post(LOGOUT, headers=auth_headers(second)), 403, "csrf_denied")
    current = api.client.get(SESSION)
    assert api.client.post(LOGOUT, headers=auth_headers(current)).status_code == 200


def test_same_origin_csrf_allows_authenticated_creation(api):
    first = issue(api)
    headers = {**auth_headers(first), "Sec-Fetch-Site": "same-origin"}
    second = issue(api, payload=SECOND_PAYLOAD, headers=headers)
    assert second.json()["id"] == SECOND_SESSION_ID
    assert api.client.cookies.get(COOKIE_NAME) == SECOND_SECRET


@pytest.mark.parametrize("header", ["Origin", CSRF_HEADER])
def test_duplicate_security_headers_deny(api, header):
    created = issue(api)
    headers = list(auth_headers(created).items()) + [(header, auth_headers(created)[header])]
    error(api.client.post(LOGOUT, headers=headers), 403, "origin_denied" if header == "Origin" else "csrf_denied")


def test_get_cannot_release_csrf_to_cross_origin_request(api):
    issue(api)
    error(api.client.get(SESSION, headers={"Origin": "https://evil.example.test"}), 403, "origin_denied")
    error(api.client.get(SESSION, headers={"Sec-Fetch-Site": "cross-site"}), 403, "origin_denied")


def test_legacy_tokens_and_client_ids_never_authorize(api):
    for headers in ({"X-Inquiry-Access-Token": "legacy-secret"}, {"Authorization": "Bearer operator-token"},
                    {"X-Customer-Id": CUSTOMER, "X-Session-Id": SESSION_ID}):
        error(api.client.get(SESSION + "?customer_id=" + CUSTOMER, headers=headers), 401, "denied")
    issue(api)
    response = api.client.get(SESSION + "?customer_id=" + OTHER_CUSTOMER)
    assert response.status_code == 200 and response.json()["customer_id"] == CUSTOMER
    assert api.service.validate_session.call_args.args == (SESSION_ID, SECRET, CUSTOMER)


@pytest.mark.parametrize("method_name,path,method,status,code", [
    ("consume_receipt_and_create_session", SESSION, "POST", 500, "internal_error"),
    ("validate_session", SESSION, "GET", 500, "internal_error"),
    ("revoke_session", LOGOUT, "POST", 500, "internal_error"),
])
def test_unexpected_secret_bearing_errors_are_fixed_and_no_store(api, caplog, method_name, path, method, status, code):
    created = issue(api)
    getattr(api.service, method_name).side_effect = RuntimeError(PRIVATE_MARKER + SECRET)
    response = api.client.request(method, path, json=SECOND_PAYLOAD if path == SESSION and method == "POST" else None,
                                  headers=auth_headers(created))
    error(response, status, code)
    assert PRIVATE_MARKER not in caplog.text and SECRET not in caplog.text


def test_dependency_exception_is_sanitized(clients):
    client = clients(inject=False)

    def fail():
        raise RuntimeError(PRIVATE_MARKER)

    client.app.dependency_overrides[get_customer_session_boundary] = fail
    error(client.get(SESSION), 500, "internal_error")


def test_validation_storage_unavailable_is_fixed(api):
    issue(api)
    api.service.validate_session.return_value = SessionValidation(SessionValidationCode.STORAGE_UNAVAILABLE)
    error(api.client.get(SESSION), 503, "unavailable")


@pytest.mark.parametrize("body", ["{", "[]", '{"receipt_id":"' + PRIVATE_MARKER + '"}'])
def test_invalid_json_and_schema_errors_are_secret_free(api, body):
    response = api.client.post(SESSION, content=body, headers={"Origin": ORIGIN, "Content-Type": "application/json"})
    error(response, 422, "invalid_request")


@pytest.mark.parametrize("method,path", [("DELETE", SESSION), ("OPTIONS", SESSION), ("HEAD", SESSION), ("GET", LOGOUT)])
def test_method_denial_is_fixed_no_store_without_cors(api, method, path):
    response = api.client.request(method, path)
    if method == "HEAD":
        assert response.status_code == 405 and response.content == b""
    else:
        error(response, 405, "method_denied")


@pytest.mark.parametrize("suffix", ["/", "//"])
def test_slash_variants_stay_inside_auth_response_boundary(api, suffix):
    created = api.client.post(SESSION + suffix, json=PAYLOAD, headers={"Origin": ORIGIN}, follow_redirects=False)
    assert created.status_code == 201 and "location" not in created.headers
    current = api.client.get(SESSION + suffix, follow_redirects=False)
    assert current.status_code == 200 and "location" not in current.headers
    error(api.client.post(LOGOUT + suffix, headers=auth_headers(created) | {"Origin": "null"},
                          follow_redirects=False), 403, "origin_denied")
    revoked = api.client.post(LOGOUT + suffix, headers=auth_headers(created), follow_redirects=False)
    assert revoked.status_code == 200 and "location" not in revoked.headers
    cleared(revoked)


@pytest.mark.parametrize("cookie", [None, "z" * 43])
def test_logout_requires_a_current_authenticated_cookie(api, cookie):
    headers = {"Origin": ORIGIN, CSRF_HEADER: "0" * 64}
    if cookie:
        headers["Cookie"] = f"{COOKIE_NAME}={cookie}"
    error(api.client.post(LOGOUT, headers=headers), 401, "denied")
    api.service.revoke_session.assert_not_called()


def test_cookie_lifetime_deducts_issuance_elapsed_time(api):
    api.boundary.clock = Mock(side_effect=[NOW, NOW + timedelta(seconds=2)])
    cookie = SimpleCookie(issue(api).headers["set-cookie"])[COOKIE_NAME]
    assert int(cookie["max-age"]) == 1798
    assert parsedate_to_datetime(cookie["expires"]) == NOW + IDLE_LIFETIME


@pytest.mark.parametrize("origin", ["*", "null", "http://shop.example.test", ORIGIN + "/path",
                                    ORIGIN + "?q=x", "https://user@shop.example.test", ORIGIN + ":65536"])
def test_unsafe_origin_configuration_is_rejected(origin):
    with pytest.raises(ValueError):
        CustomerSessionBoundary(service=Mock(), trusted_origin=origin, csrf_key=CSRF_KEY, clock=lambda: NOW)


def test_key_and_binding_capacity_configuration_fail_closed():
    with pytest.raises(ValueError):
        CustomerSessionBoundary(service=Mock(), trusted_origin=ORIGIN, csrf_key=SecretBytes(b"short"), clock=lambda: NOW)
    with pytest.raises(ValueError):
        CustomerSessionBoundary(service=Mock(), trusted_origin=ORIGIN, csrf_key=CSRF_KEY, clock=lambda: NOW, max_bindings=0)


def test_index_is_bounded_and_restart_fails_closed(api, clients):
    issue(api)
    api.boundary._max_bindings = 1
    api.client.cookies.clear()
    error(api.client.post(SESSION, json=SECOND_PAYLOAD, headers={"Origin": ORIGIN}), 503, "unavailable")
    assert api.service.consume_receipt_and_create_session.call_count == 1
    restarted = CustomerSessionBoundary(service=api.real, trusted_origin=ORIGIN, csrf_key=CSRF_KEY, clock=lambda: NOW)
    error(clients(restarted).get(SESSION, headers={"Cookie": f"{COOKIE_NAME}={SECRET}"}), 401, "denied")


def test_cookie_cap_respects_absolute_expiry_with_late_activity(api):
    # Synthetic trusted service result near the absolute limit: the HTTP layer
    # must choose the earlier deadline even when the idle deadline is later.
    created_at = NOW - ABSOLUTE_LIFETIME + timedelta(minutes=1)
    projection = SafeSessionProjection(id=SESSION_ID, customer_id=CUSTOMER, created_at=created_at,
        last_activity_at=NOW, idle_expires_at=NOW + IDLE_LIFETIME,
        absolute_expires_at=created_at + ABSOLUTE_LIFETIME)
    from pydantic import SecretStr
    api.service.consume_receipt_and_create_session.return_value = IssuedSession(SESSION_ID, SecretStr(SECRET), projection, RECEIPT)
    api.service.validate_session.return_value = SessionValidation("VALID", projection)
    response = issue(api)
    cookie = SimpleCookie(response.headers["set-cookie"])[COOKIE_NAME]
    assert int(cookie["max-age"]) == 60
    assert parsedate_to_datetime(cookie["expires"]) == NOW + timedelta(minutes=1)
    assert "set-cookie" not in api.client.get(SESSION).headers
    api.time.now += timedelta(minutes=1)
    error(api.client.get(SESSION), 401, "denied")


def test_no_default_registration_mock_verifier_or_schema_provisioning():
    app_source = (ROOT / "core/api/app.py").read_text()
    app_tree = ast.parse(app_source)
    imports = [ast.unparse(node) for node in ast.walk(app_tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert not any("customer_session" in node for node in imports)
    for path in ("core/api/routes/customer_sessions.py", "core/api/dependencies/customer_session.py"):
        source = (ROOT / path).read_text()
        tree = ast.parse(source)
        import_names = [ast.unparse(node) for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        assert not any("mock" in node.lower() or "core.api.app" in node or "sqlite3" in node for node in import_names)
        calls = [ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
        assert not any(name.endswith(("initialize_schema", "connect", "create_app")) for name in calls)
        assert "TrustedReceiptBinding(" not in source and "TrustedVerificationContext(" not in source
    assert "customer_session" not in (ROOT / "core/api/routes/shopping.py").read_text()


def test_b3a_b3b_contract_compatibility(api):
    assert set(VerificationReceiptConsumeRequest.model_fields) == {"schema_version", "receipt_id", "browser_challenge"}
    assert IDLE_LIFETIME == timedelta(minutes=30) and ABSOLUTE_LIFETIME == timedelta(hours=24)
    created = issue(api)
    assert SafeSessionProjection.model_validate(created.json()).id == SESSION_ID
    assert api.real.validate_session(SESSION_ID, SECRET, CUSTOMER, now=NOW).code == SessionValidationCode.VALID
