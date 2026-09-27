"""B3-D isolated API security, transaction and legacy compatibility tests."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
import sys
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretBytes, SecretStr
import pytest
import requests


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://shop.example.test"
OWNED = "/shopping/owned-inquiries"
LEGACY = "/shopping/inquiries"
NOW = datetime(2026, 9, 1, 0, 2, tzinfo=timezone.utc)
SECRET = "s" * 43
OTHER_SECRET = "t" * 43
OPERATOR = "synthetic-operator-only"
PRIVATE = "synthetic-private-phone-otp-receipt-error"
BODY = "Synthetic inquiry message"


def ref(kind, number):
    digit = str(number)
    return f"AG-{kind}-" + digit * 12 + "4" + digit * 3 + "8" + digit * 15


@pytest.fixture(autouse=True)
def isolated_io(monkeypatch, tmp_path):
    attempts = []
    connect = sqlite3.connect

    def deny(*args, **kwargs):
        attempts.append("external_or_operational_access")
        raise AssertionError("Only isolated Mock I/O is allowed")

    def temporary_connect(database, *args, **kwargs):
        if kwargs.get("uri") or (database != ":memory:" and not
                                 Path(database).resolve().is_relative_to(tmp_path.resolve())):
            return deny()
        return connect(database, *args, **kwargs)

    for name in ("connect", "connect_ex", "sendto"):
        monkeypatch.setattr(socket.socket, name, deny)
    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket, "getaddrinfo", deny)
    monkeypatch.setattr(requests.sessions.Session, "request", deny)
    monkeypatch.setattr(sqlite3, "connect", temporary_connect)
    monkeypatch.setenv("AICC_OPERATOR_TOKEN", OPERATOR)
    monkeypatch.delenv("AICC_INSTAGRAM_CONTACT_URL", raising=False)
    from core.config.loader import ConfigLoader
    monkeypatch.setattr(ConfigLoader, "load", deny)
    assert "core.api.app" not in sys.modules
    yield
    assert not attempts
    assert "core.api.app" not in sys.modules


@pytest.fixture
def api(tmp_path, monkeypatch):
    from core.api.dependencies.customer_session import CustomerSessionBoundary, TrustedSessionEvidence, get_customer_session_boundary
    from core.api.dependencies.inquiries import get_inquiry_repository, get_owned_inquiry_repository
    from core.api.dependencies.shopping import get_shopping_service
    from core.api.routes.customer_sessions import router as session_router
    from core.api.routes.shopping import router, owned_inquiry_router
    from core.shopping import customer_persistence as persistence
    from core.shopping.customer_auth import TrustedReceiptBinding, TrustedVerificationContext, TrustedVerificationReceipt
    from core.shopping.customer_identity import Customer, VerifiedContactBinding
    from core.shopping.customer_session_service import CustomerSessionService
    from core.shopping.inquiries import SQLiteInquiryRepository, InquirySessionAuthority
    from core.shopping.adapters.mock_commerce import MockCommerceCatalogAdapter
    from core.shopping.config import ShoppingSettings
    from core.shopping.service import ShoppingService

    path = tmp_path / "owned-inquiries.sqlite3"
    repository = SQLiteInquiryRepository(str(path))
    persistence.initialize_schema(path)
    store = persistence.SQLiteCustomerSessionStore(path)
    customers = []
    evidence = {}
    for number in (1, 2):
        customer = Customer(id=ref("CUS", number), state="ACTIVE", created_at=NOW - timedelta(minutes=1),
            updated_at=NOW, contact_binding=VerifiedContactBinding(customer_id=ref("CUS", number), state="VERIFIED",
                contact_ref=ref("CON", number), created_at=NOW - timedelta(minutes=1), updated_at=NOW, verified_at=NOW))
        customers.append(customer)
        store.save_customer(customer)
        receipt = TrustedVerificationReceipt(receipt_id=ref("VRF", number), purpose="SESSION_ISSUANCE",
            browser_challenge=ref("CHL", number), issuer_ref=ref("ISS", number), customer_id=customer.id,
            issued_at=NOW, expires_at=NOW + timedelta(minutes=5))
        evidence[f"VRF-CLIENT0{number}"] = TrustedSessionEvidence(receipt, TrustedVerificationContext(
            accepted_bindings=frozenset({TrustedReceiptBinding(receipt.receipt_id, receipt.issuer_ref, customer.id)})),
            receipt.browser_challenge)
    secrets = iter((SECRET, OTHER_SECRET))
    session_ids = iter((ref("SES", 1), ref("SES", 2)))
    service = CustomerSessionService(str(path), secret_factory=lambda: next(secrets), session_id_factory=lambda: next(session_ids))
    monkeypatch.setattr(service, "validate_session", Mock(wraps=service.validate_session))
    time = SimpleNamespace(now=NOW)
    boundary = CustomerSessionBoundary(service=service, trusted_origin=ORIGIN, csrf_key=SecretBytes(b"synthetic-csrf-key" * 3),
        clock=lambda: time.now, resolve_evidence=lambda payload: evidence[payload.receipt_id])
    catalog = ShoppingService(settings=ShoppingSettings(enabled=True, environment="test", runtime="virtual",
        deployment_target="mac-mini-m4", write_mode="read_only", approval_required=True, automation_enabled=False,
        ai_enabled=False, catalog_adapter="mock"), catalog=MockCommerceCatalogAdapter())
    monkeypatch.setattr(catalog, "get_product", Mock(wraps=catalog.get_product))

    with ExitStack() as stack:
        def client(*, owned=True, inject=True):
            app = FastAPI()
            app.include_router(router)
            app.include_router(session_router)
            if owned:
                app.include_router(owned_inquiry_router)
            app.dependency_overrides[get_inquiry_repository] = lambda: repository
            app.dependency_overrides[get_shopping_service] = lambda: catalog
            if inject:
                app.dependency_overrides[get_owned_inquiry_repository] = lambda: repository
                app.dependency_overrides[get_customer_session_boundary] = lambda: boundary
            result = stack.enter_context(TestClient(app, base_url=ORIGIN))

            def guard(response):
                if owned and response.request.url.path.startswith(OWNED):
                    assert response.headers["cache-control"] == "no-store"
                    assert "access-control-allow-origin" not in response.headers

            result.event_hooks["response"].append(guard)
            return result

        owner, other, anonymous = client(), client(), client()
        headers = []
        for number, current in enumerate((owner, other), 1):
            response = current.post("/shopping/auth/session", json={"receipt_id": f"VRF-CLIENT0{number}",
                "browser_challenge": f"CHL-CLIENT0{number}"}, headers={"Origin": ORIGIN})
            assert response.status_code == 201
            headers.append({"Origin": ORIGIN, "X-CSRF-Token": response.headers["X-CSRF-Token"]})
        authority = InquirySessionAuthority(service, SecretStr(SECRET), customers[0].id, ref("SES", 1), boundary.now)
        yield SimpleNamespace(owner=owner, other=other, anonymous=anonymous, headers=headers[0], other_headers=headers[1],
            client=client, repository=repository, path=path, service=service, boundary=boundary, time=time,
            catalog=catalog, customers=customers, store=store, authority=authority)


def create(api):
    response = api.owner.post(OWNED, json={"product_id": "mock-001", "message": BODY}, headers=api.headers)
    assert response.status_code == 201, response.text
    return response.json()


def append(api, inquiry_id, *, client=None, headers=None, **updates):
    payload = {"body": "Synthetic reply", "expected_version": 0, "idempotency_key": "request-1"}
    payload.update(updates)
    return (client or api.owner).post(OWNED + f"/{inquiry_id}/messages", json=payload, headers=headers or api.headers)


def denial(response, status=403, code="owned_inquiry_access_denied"):
    assert response.status_code == status, response.text
    assert response.json() == {"detail": {"code": code}}
    assert all(value not in response.text for value in (SECRET, OTHER_SECRET, PRIVATE, ref("CON", 1), ref("VRF", 1)))


def counts(api):
    with sqlite3.connect(api.path) as connection:
        return tuple(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in (
            "inquiries", "shopping_inquiry_ownership", "shopping_inquiry_audit", "shopping_inquiry_idempotency"))


def test_atomic_creation_commits_inquiry_ownership_and_audit_once(api, monkeypatch):
    traces = []
    import core.shopping.inquiries as module
    open_connection = module.open_connection

    def traced(path):
        connection = open_connection(path)
        connection.set_trace_callback(traces.append)
        return connection

    monkeypatch.setattr(module, "open_connection", traced)
    monkeypatch.setattr(api.repository, "create", Mock(side_effect=AssertionError("separate create is forbidden")))
    monkeypatch.setattr(api.repository, "bind_customer_ownership", Mock(side_effect=AssertionError("separate bind is forbidden")))
    created = create(api)
    assert created["version"] == 0 and counts(api) == (1, 1, 1, 0)
    assert traces.count("BEGIN IMMEDIATE") == traces.count("COMMIT") == 1
    with sqlite3.connect(api.path) as connection:
        owner = connection.execute("SELECT customer_id,session_id,version FROM shopping_inquiry_ownership").fetchone()
        assert owner == (ref("CUS", 1), ref("SES", 1), 0)
        payload, token = connection.execute("SELECT payload,token_hash FROM inquiries").fetchone()
        assert token == "" and "public_access_token" not in payload and "_ownership" not in payload
    assert "public_access_token" not in json.dumps(created)
    assert created["inquiry"]["id"] not in api.repository._tokens
    assert api.service.validate_session.call_args.args == (ref("SES", 1), SECRET, ref("CUS", 1))


@pytest.mark.parametrize("table", ["shopping_inquiry_ownership", "shopping_inquiry_audit"])
def test_creation_ownership_or_audit_failure_rolls_back_everything(api, table):
    with sqlite3.connect(api.path) as connection:
        connection.execute(f"CREATE TRIGGER fail_create BEFORE INSERT ON {table} BEGIN SELECT RAISE(ABORT,'{PRIVATE}'); END")
    response = api.owner.post(OWNED, json={"product_id": "mock-001"}, headers=api.headers)
    denial(response, 503, "owned_inquiry_unavailable")
    assert counts(api) == (0, 0, 0, 0)


def test_concurrent_creation_uses_database_allocation(api):
    from core.shopping.inquiries import InquiryCreateRequest, SQLiteInquiryRepository
    repositories = [SQLiteInquiryRepository(str(api.path)) for _ in range(4)]
    product = api.catalog.get_product("mock-001")

    def attempt(repository):
        return repository.create_owned(InquiryCreateRequest(product_id="mock-001"), authority=api.authority,
                                        product_loader=lambda _: product)[0].id

    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(attempt, repositories))
    assert len(set(ids)) == 4 and counts(api) == (4, 4, 4, 0)


def test_owner_detail_history_append_and_current_validation(api):
    created = create(api)
    inquiry_id = created["inquiry"]["id"]
    before = api.service.validate_session.call_count
    assert api.owner.get(OWNED + "/" + inquiry_id).json() == created
    assert api.owner.get(OWNED + f"/{inquiry_id}/messages").json() == {"items": [], "version": 0}
    message = append(api, inquiry_id)
    assert message.status_code == 200 and message.json()["version"] == 1
    history = api.owner.get(OWNED + f"/{inquiry_id}/messages")
    assert history.json() == {"items": [message.json()["message"]], "version": 1}
    assert api.service.validate_session.call_count == before + 8
    assert counts(api) == (1, 1, 2, 1)


@pytest.mark.parametrize("operation", ["detail", "history", "append"])
def test_wrong_owner_and_nonexistent_have_identical_denial(api, operation):
    inquiry_id = create(api)["inquiry"]["id"]
    responses = []
    for value in (inquiry_id, "AG-INQ-999999", "malformed"):
        if operation == "append":
            response = append(api, value, client=api.other, headers=api.other_headers)
        else:
            response = api.other.get(OWNED + "/" + value + ("/messages" if operation == "history" else ""))
        denial(response)
        responses.append(response.json())
    assert responses[0] == responses[1] == responses[2]
    assert counts(api) == (1, 1, 1, 0)


def invalidate(api, reason):
    from core.shopping.customer_identity import CustomerState, VerificationState
    if reason == "expired":
        api.time.now += timedelta(minutes=30)
    elif reason == "revoked":
        api.service.revoke_session(ref("SES", 1), now=NOW, actor_ref=ref("CUS", 1), correlation_id="test-revoke")
    elif reason in {"suspended", "closed"}:
        customer = api.customers[0].model_copy(update={"state": CustomerState(reason.upper())})
        if reason == "closed":
            customer = customer.model_copy(update={"contact_binding": customer.contact_binding.model_copy(update={
                "state": VerificationState.REVOKED, "revoked_at": NOW})})
        api.store.save_customer(customer)
    elif reason == "mismatched":
        with sqlite3.connect(api.path) as connection:
            payload = json.loads(connection.execute("SELECT session_json FROM shopping_sessions WHERE session_id=?", (ref("SES", 1),)).fetchone()[0])
            payload["customer_id"] = ref("CUS", 2)
            connection.execute("UPDATE shopping_sessions SET session_json=? WHERE session_id=?", (json.dumps(payload), ref("SES", 1)))
    else:
        api.owner.cookies.clear()


@pytest.mark.parametrize("reason", ["expired", "revoked", "missing", "mismatched", "suspended", "closed"])
@pytest.mark.parametrize("operation", ["detail", "history", "append"])
def test_ineligible_session_denies_all_owned_operations(api, reason, operation):
    inquiry_id = create(api)["inquiry"]["id"]
    invalidate(api, reason)
    response = (append(api, inquiry_id) if operation == "append" else
        api.owner.get(OWNED + "/" + inquiry_id + ("/messages" if operation == "history" else "")))
    denial(response, 401, "owned_inquiry_session_denied")
    assert counts(api) == (1, 1, 1, 0)


def test_revalidation_under_transaction_rejects_post_boundary_revocation(api, monkeypatch):
    original = api.repository.create_owned

    def revoke_first(*args, **kwargs):
        invalidate(api, "revoked")
        return original(*args, **kwargs)

    monkeypatch.setattr(api.repository, "create_owned", revoke_first)
    denial(api.owner.post(OWNED, json={"product_id": "mock-001"}, headers=api.headers))
    assert counts(api) == (0, 0, 0, 0)
    api.catalog.get_product.assert_not_called()


@pytest.mark.parametrize("field", ["customer_id", "session_id", "verified", "session_secret", "ownership"])
def test_body_claims_cannot_authorize_or_set_ownership(api, field):
    denial(api.owner.post(OWNED, json={"product_id": "mock-001", field: PRIVATE}, headers=api.headers),
           422, "owned_inquiry_invalid_request")
    assert counts(api) == (0, 0, 0, 0)


def test_query_header_and_cookie_identity_claims_have_no_authority(api):
    inquiry_id = create(api)["inquiry"]["id"]
    headers = {"X-Customer-ID": ref("CUS", 1), "X-Session-ID": ref("SES", 1), "Verified": "true",
               "Cookie": "customer_id=" + ref("CUS", 1), "X-Inquiry-Access-Token": SECRET}
    denial(api.anonymous.get(OWNED + "/" + inquiry_id + "?customer_id=" + ref("CUS", 1), headers=headers),
           401, "owned_inquiry_session_denied")
    denial(api.other.get(OWNED + "/" + inquiry_id + "?customer_id=" + ref("CUS", 1),
                         headers={"X-Customer-ID": ref("CUS", 1)}))


def test_persisted_records_or_fabricated_authority_do_not_authenticate(api):
    from core.shopping.inquiries import InquiryCreateRequest
    from core.shopping.customer_persistence import AuthorizationConflict
    forged = replace(api.authority, session_secret=SecretStr("z" * 43))
    with pytest.raises(AuthorizationConflict):
        api.repository.create_owned(InquiryCreateRequest(product_id="mock-001"), authority=forged,
                                    product_loader=api.catalog.get_product)
    assert counts(api) == (0, 0, 0, 0)
    # Even the real secret cannot bypass B3-C's explicit server binding index.
    api.boundary._bindings.clear()
    denial(api.owner.post(OWNED, json={"product_id": "mock-001"}, headers=api.headers),
           401, "owned_inquiry_session_denied")


def test_authority_cannot_use_a_different_database(api, tmp_path):
    from core.shopping.inquiries import SQLiteInquiryRepository, InquiryCreateRequest
    from core.shopping.customer_persistence import AuthorizationConflict, initialize_schema
    path = tmp_path / "different.sqlite3"
    repository = SQLiteInquiryRepository(str(path))
    initialize_schema(path)
    with pytest.raises(AuthorizationConflict):
        repository.create_owned(InquiryCreateRequest(product_id="mock-001"), authority=api.authority,
                                 product_loader=api.catalog.get_product)


@pytest.mark.parametrize("state", ["valid", "expired", "revoked"])
@pytest.mark.parametrize("operation", ["detail", "history", "append"])
def test_owned_record_rejects_even_valid_historical_token(api, state, operation):
    created = api.owner.post(LEGACY, json={"product_id": "mock-001"}).json()
    inquiry_id, token = created["id"], created["public_access_token"]
    api.repository.bind_customer_ownership(inquiry_id, ref("CUS", 1), ref("SES", 1))
    # Simulate a retained historical hash. Ownership, not hash availability,
    # must decide whether the legacy path is permitted.
    with sqlite3.connect(api.path) as connection:
        connection.execute("UPDATE inquiries SET token_hash=? WHERE id=?", (hashlib.sha256(token.encode()).hexdigest(), inquiry_id))
    if state != "valid":
        invalidate(api, state)
    headers = {"X-Inquiry-Access-Token": token}
    path = LEGACY + "/" + inquiry_id + ("/messages" if operation != "detail" else "")
    response = (api.owner.post(path, headers=headers, json={"body": "Denied"}) if operation == "append" else
                api.owner.get(path, headers=headers))
    assert response.status_code == 403 and response.json() == {"detail": {"code": "inquiry_access_denied"}}
    assert not api.repository.authorize(inquiry_id, token)
    assert api.repository.get(inquiry_id).messages == []


def test_legacy_unowned_compatibility_and_no_automatic_claiming(api):
    created = api.anonymous.post(LEGACY, json={"product_id": "mock-001", "message": BODY}).json()
    inquiry_id, token = created["id"], created["public_access_token"]
    headers = {"X-Inquiry-Access-Token": token}
    assert api.anonymous.get(LEGACY + "/" + inquiry_id, headers=headers).json() == {**created, "public_access_token": None}
    assert api.anonymous.post(LEGACY + f"/{inquiry_id}/messages", headers=headers, json={"body": "Legacy reply"}).status_code == 200
    denial(api.owner.get(OWNED + "/" + inquiry_id))
    denial(append(api, inquiry_id))
    assert counts(api) == (1, 0, 0, 0)
    assert api.anonymous.get(LEGACY + f"/{inquiry_id}/messages", headers=headers).json()["items"][0]["body"] == "Legacy reply"


@pytest.mark.parametrize("damage", ["missing_table", "missing_all", "incompatible_version", "incompatible_columns"])
def test_ambiguous_ownership_schema_never_allows_legacy_fallback(api, damage):
    created = api.anonymous.post(LEGACY, json={"product_id": "mock-001"}).json()
    inquiry_id, token = created["id"], created["public_access_token"]
    api.repository.bind_customer_ownership(inquiry_id, ref("CUS", 1), ref("SES", 1))
    with sqlite3.connect(api.path) as connection:
        connection.execute("UPDATE inquiries SET token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))
        if damage.startswith("missing"):
            connection.execute("DROP TABLE shopping_inquiry_ownership")
            if damage == "missing_all":
                connection.execute("DROP TABLE shopping_customer_persistence_meta")
        elif damage == "incompatible_version":
            connection.execute("UPDATE shopping_customer_persistence_meta SET version='future'")
        else:
            connection.execute("ALTER TABLE shopping_inquiry_ownership RENAME COLUMN session_id TO changed")
    response = api.anonymous.get(LEGACY + "/" + inquiry_id, headers={"X-Inquiry-Access-Token": token})
    assert response.status_code == 403


def test_unmarked_historical_record_without_schema_is_ambiguous(api):
    created = api.anonymous.post(LEGACY, json={"product_id": "mock-001"}).json()
    with sqlite3.connect(api.path) as connection:
        payload = json.loads(connection.execute("SELECT payload FROM inquiries").fetchone()[0])
        payload.pop("_ownership")
        connection.execute("UPDATE inquiries SET payload=?", (json.dumps(payload),))
        connection.execute("DROP TABLE shopping_inquiry_ownership")
        connection.execute("DROP TABLE shopping_customer_persistence_meta")
    assert api.anonymous.get(LEGACY + "/" + created["id"], headers={"X-Inquiry-Access-Token": created["public_access_token"]}).status_code == 403


def test_operator_authorization_is_independent_and_no_unversioned_owned_write(api):
    inquiry_id = create(api)["inquiry"]["id"]
    operator_path = "/shopping/operator/inquiries/" + inquiry_id
    for headers in ({}, {"X-Inquiry-Access-Token": SECRET}, {"Authorization": "Bearer " + SECRET}):
        assert api.owner.get(operator_path, headers=headers).status_code == 401
        assert api.owner.post(operator_path + "/messages", headers=headers, json={"body": "Denied"}).status_code == 401
    operator_headers = {"Authorization": "Bearer " + OPERATOR}
    assert api.anonymous.get(operator_path, headers=operator_headers).status_code == 200
    denied = api.anonymous.post(operator_path + "/messages", headers=operator_headers, json={"body": "Unversioned"})
    assert denied.status_code == 409
    assert counts(api) == (1, 1, 1, 0)
    invalidate(api, "revoked")
    assert api.anonymous.get(operator_path, headers=operator_headers).status_code == 200
    denial(api.anonymous.get(OWNED + "/" + inquiry_id, headers=operator_headers), 401, "owned_inquiry_session_denied")
    legacy = api.anonymous.post(LEGACY, json={"product_id": "mock-001"}).json()
    assert api.anonymous.post("/shopping/operator/inquiries/" + legacy["id"] + "/messages",
                              headers=operator_headers, json={"body": "Legacy operator reply"}).status_code == 200


def test_version_and_idempotency_conflicts_and_authorized_replay(api):
    inquiry_id = create(api)["inquiry"]["id"]
    first = append(api, inquiry_id)
    assert first.status_code == 200
    replay = append(api, inquiry_id)
    assert replay.json() == first.json() and counts(api) == (1, 1, 2, 1)
    denial(append(api, inquiry_id, idempotency_key="request-2"), 409, "owned_inquiry_version_conflict")
    denial(append(api, inquiry_id, body="Changed"), 409, "owned_inquiry_idempotency_conflict")
    assert counts(api) == (1, 1, 2, 1)


@pytest.mark.parametrize("reason", ["wrong_owner", "revoked", "expired"])
def test_unauthorized_replay_is_never_disclosed(api, reason):
    inquiry_id = create(api)["inquiry"]["id"]
    first = append(api, inquiry_id)
    if reason == "wrong_owner":
        response = append(api, inquiry_id, client=api.other, headers=api.other_headers)
        denial(response)
    else:
        invalidate(api, reason)
        response = append(api, inquiry_id)
        denial(response, 401, "owned_inquiry_session_denied")
    assert first.json()["message"]["id"] not in response.text


def test_mutation_revalidates_before_replay_inside_transaction(api, monkeypatch):
    inquiry_id = create(api)["inquiry"]["id"]
    append(api, inquiry_id)
    original = api.repository.append_owned_message

    def revoke_first(*args, **kwargs):
        invalidate(api, "revoked")
        return original(*args, **kwargs)

    monkeypatch.setattr(api.repository, "append_owned_message", revoke_first)
    denial(append(api, inquiry_id))
    assert counts(api) == (1, 1, 2, 1)


def test_mutation_audit_failure_rolls_back_payload_version_and_idempotency(api):
    inquiry_id = create(api)["inquiry"]["id"]
    with sqlite3.connect(api.path) as connection:
        connection.execute(f"CREATE TRIGGER fail_message BEFORE INSERT ON shopping_inquiry_audit BEGIN SELECT RAISE(ABORT,'{PRIVATE}'); END")
        before = connection.execute("SELECT payload FROM inquiries").fetchone()[0]
    denial(append(api, inquiry_id), 503, "owned_inquiry_unavailable")
    with sqlite3.connect(api.path) as connection:
        assert connection.execute("SELECT payload FROM inquiries").fetchone()[0] == before
        assert connection.execute("SELECT version FROM shopping_inquiry_ownership").fetchone()[0] == 0
    assert counts(api) == (1, 1, 1, 0)


def test_storage_lock_failure_is_bounded_and_secret_free(api):
    inquiry_id = create(api)["inquiry"]["id"]
    with sqlite3.connect(api.path, isolation_level=None) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            denial(append(api, inquiry_id), 503, "owned_inquiry_unavailable")
        finally:
            connection.rollback()
    assert counts(api) == (1, 1, 1, 0)


@pytest.mark.parametrize("payload", [{"product_id": "absent"}, {"product_id": "mock-001", "variant_id": "forged"}])
def test_invalid_product_or_variant_has_no_partial_creation(api, payload):
    response = api.owner.post(OWNED, json=payload, headers=api.headers)
    assert response.status_code in {404, 422}
    assert counts(api) == (0, 0, 0, 0)


@pytest.mark.parametrize("headers,code", [({}, "origin_denied"), ({"Origin": "https://evil.test"}, "origin_denied"),
                                       ({"Origin": ORIGIN}, "csrf_denied"),
                                       ({"Origin": ORIGIN, "X-CSRF-Token": "0" * 64}, "csrf_denied")])
def test_owned_mutations_reuse_b3c_origin_and_csrf(api, headers, code):
    denial(api.owner.post(OWNED, json={"product_id": "mock-001"}, headers=headers), 403, "owned_inquiry_" + code)
    inquiry_id = create(api)["inquiry"]["id"]
    denial(api.owner.post(OWNED + f"/{inquiry_id}/messages", json={"body": BODY, "expected_version": 0,
        "idempotency_key": "blocked"}, headers=headers), 403, "owned_inquiry_" + code)


def test_secret_free_responses_errors_audit_and_no_schema_changes(api, monkeypatch, caplog):
    with sqlite3.connect(api.path) as connection:
        schema = list(connection.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"))
    created = create(api)
    inquiry_id = created["inquiry"]["id"]
    message = append(api, inquiry_id)
    public = json.dumps(created) + message.text
    with sqlite3.connect(api.path) as connection:
        assert list(connection.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name")) == schema
        audit = json.dumps(list(connection.execute("SELECT * FROM shopping_inquiry_audit")))
    assert BODY not in audit and "Synthetic reply" not in audit
    for forbidden in (SECRET, OTHER_SECRET, ref("CON", 1), ref("VRF", 1), PRIVATE, "session_secret_hash", "sha256:"):
        assert forbidden not in public + audit + caplog.text
    monkeypatch.setattr(api.repository, "get_owned", Mock(side_effect=RuntimeError(PRIVATE + SECRET)))
    denial(api.owner.get(OWNED + "/" + inquiry_id), 500, "owned_inquiry_request_failed")
    assert PRIVATE not in caplog.text and SECRET not in caplog.text


def test_router_requires_opt_in_and_dependencies_have_no_operational_fallback(api):
    default = api.client(owned=False)
    assert OWNED not in default.app.openapi()["paths"]
    assert default.post(OWNED, json={"product_id": "mock-001"}).status_code == 404
    unconfigured = api.client(inject=False)
    denial(unconfigured.post(OWNED, json={"product_id": "mock-001"}, headers={"Origin": ORIGIN}),
           503, "owned_inquiry_unavailable")
    assert "owned_inquiry_router" not in (ROOT / "core/api/app.py").read_text()
    assert "core.api.app" not in sys.modules


def test_b3c_session_status_and_logout_still_control_owned_access(api):
    inquiry_id = create(api)["inquiry"]["id"]
    status = api.owner.get("/shopping/auth/session")
    assert status.status_code == 200 and status.json()["customer_id"] == ref("CUS", 1)
    assert api.owner.post("/shopping/auth/logout", headers=api.headers).status_code == 200
    denial(api.owner.get(OWNED + "/" + inquiry_id), 401, "owned_inquiry_session_denied")


def test_same_customer_different_session_cannot_replace_immutable_owner(api):
    from core.shopping.customer_persistence import AuthorizationConflict
    inquiry_id = create(api)["inquiry"]["id"]
    with pytest.raises(AuthorizationConflict):
        api.repository.get_owned(inquiry_id, authority=replace(api.authority, session_id=ref("SES", 2)))
    assert counts(api) == (1, 1, 1, 0)
