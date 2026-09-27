"""Inquiry access regressions using isolated dependencies and synthetic data only."""
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
import sys
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
import requests


OPERATOR_TOKEN = "mock-only-operator-credential"
LEGACY_TOKEN = "mock-only-legacy-payload-copy"


@pytest.fixture(autouse=True)
def isolated_io(monkeypatch, tmp_path):
    attempts = []
    connect = sqlite3.connect

    def deny_external(*args, **kwargs):
        attempts.append("external_access")
        raise AssertionError("External access is prohibited in inquiry tests")

    def temporary_connect(database, *args, **kwargs):
        if kwargs.get("uri") or (database != ":memory:" and not
                                 Path(database).resolve().is_relative_to(tmp_path.resolve())):
            return deny_external()
        return connect(database, *args, **kwargs)

    for name in ("connect", "connect_ex", "sendto"):
        monkeypatch.setattr(socket.socket, name, deny_external)
    monkeypatch.setattr(socket, "create_connection", deny_external)
    monkeypatch.setattr(socket, "getaddrinfo", deny_external)
    monkeypatch.setattr(requests.sessions.Session, "request", deny_external)
    monkeypatch.setattr(sqlite3, "connect", temporary_connect)
    monkeypatch.setenv("AICC_OPERATOR_TOKEN", OPERATOR_TOKEN)
    monkeypatch.delenv("AICC_INSTAGRAM_CONTACT_URL", raising=False)
    from core.config.loader import ConfigLoader
    monkeypatch.setattr(ConfigLoader, "load", deny_external)
    assert "core.api.app" not in sys.modules
    yield
    assert not attempts
    assert "core.api.app" not in sys.modules


@pytest.fixture(params=["memory", "sqlite"])
def inquiry(request, isolated_io, tmp_path):
    from core.api.dependencies.inquiries import get_inquiry_repository
    from core.api.dependencies.shopping import get_shopping_service
    from core.api.routes.shopping import router
    from core.shopping.adapters.mock_commerce import MockCommerceCatalogAdapter
    from core.shopping.config import ShoppingSettings
    from core.shopping.inquiries import InMemoryInquiryRepository, SQLiteInquiryRepository
    from core.shopping.service import ShoppingService

    path = tmp_path / "inquiries.db"
    if request.param == "sqlite":
        from core.shopping.customer_persistence import initialize_schema
        repository = SQLiteInquiryRepository(str(path))
        # SQLite positive compatibility cases require the repository's
        # established compatible persistence contract.
        initialize_schema(path)
    else:
        repository = InMemoryInquiryRepository()
    service = ShoppingService(settings=ShoppingSettings(
        enabled=True, environment="test", runtime="virtual", deployment_target="mac-mini-m4",
        write_mode="read_only", approval_required=True, automation_enabled=False,
        ai_enabled=False, catalog_adapter="mock"), catalog=MockCommerceCatalogAdapter())
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_inquiry_repository] = lambda: repository
    app.dependency_overrides[get_shopping_service] = lambda: service
    with TestClient(app) as client:
        yield SimpleNamespace(client=client, repository=repository, path=path,
                              backend=request.param)


def create(inquiry):
    response = inquiry.client.post("/shopping/inquiries", json={
        "product_id": "mock-001", "message": "Synthetic product inquiry"})
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result["public_access_token"], str) and result["public_access_token"]
    return result


def headers(created):
    return {"X-Inquiry-Access-Token": created["public_access_token"]}


def request_content(client, inquiry_id, action, auth):
    path = f"/shopping/inquiries/{inquiry_id}"
    if action == "detail":
        return client.get(path, headers=auth)
    if action == "messages":
        return client.get(path + "/messages", headers=auth)
    return client.post(path + "/messages", headers=auth, json={"body": "Synthetic reply"})


@pytest.mark.parametrize("action", ["detail", "messages", "append"])
@pytest.mark.parametrize("credential", ["missing", "invalid", "cross_inquiry", "oversized"])
def test_unauthorized_access_precedes_content_reads(inquiry, monkeypatch, action, credential):
    first, second = create(inquiry), create(inquiry)
    supplied = {"missing": {}, "invalid": {"X-Inquiry-Access-Token": "mock-invalid"},
                "cross_inquiry": headers(second),
                "oversized": {"X-Inquiry-Access-Token": "x" * 257}}[credential]

    def forbidden_content_access(*args, **kwargs):
        pytest.fail("Unauthorized request reached inquiry content")

    monkeypatch.setattr(inquiry.repository, "get", forbidden_content_access)
    monkeypatch.setattr(inquiry.repository, "append_message", forbidden_content_access)
    response = request_content(inquiry.client, first["id"], action, supplied)
    required = credential in {"missing", "oversized"}
    assert response.status_code == (401 if required else 403)
    assert response.json() == {"detail": {"code": (
        "inquiry_access_required" if required else "inquiry_access_denied")}}


@pytest.mark.parametrize("action", ["detail", "messages", "append"])
@pytest.mark.parametrize("auth", [{}, {"X-Inquiry-Access-Token": "mock-invalid"}])
def test_unauthorized_responses_do_not_reveal_inquiry_existence(inquiry, action, auth):
    created = create(inquiry)
    responses = [request_content(inquiry.client, identifier, action, auth)
                 for identifier in (created["id"], "AG-INQ-999999", "malformed")]
    assert responses[0].status_code in {401, 403}
    assert all(response.status_code == responses[0].status_code
               and response.json() == responses[0].json() for response in responses)


def test_creation_token_is_once_only_and_authorized_customer_and_operator_work(inquiry):
    created = create(inquiry)
    token = created["public_access_token"]
    path = f"/shopping/inquiries/{created['id']}"
    operator_path = f"/shopping/operator/inquiries/{created['id']}"
    operator = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    detail = inquiry.client.get(path, headers=headers(created))
    assert detail.status_code == 200
    assert detail.json() == {**created, "public_access_token": None}
    customer_reply = inquiry.client.post(path + "/messages", headers=headers(created),
                                         json={"body": "Customer follow-up"})
    operator_reply = inquiry.client.post(operator_path + "/messages", headers=operator,
                                         json={"body": "Operator answer"})
    assert customer_reply.status_code == operator_reply.status_code == 200
    assert customer_reply.json()["sender_type"] == "customer"
    assert operator_reply.json()["sender_type"] == "operator"
    history = inquiry.client.get(path + "/messages", headers=headers(created))
    assert history.status_code == 200
    assert [message["body"] for message in history.json()["items"]] == [
        "Customer follow-up", "Operator answer"]
    responses = [detail, customer_reply, operator_reply, history,
                 inquiry.client.get(path, headers=headers(created)),
                 inquiry.client.get(operator_path, headers=operator),
                 inquiry.client.get("/shopping/operator/inquiries", headers=operator)]
    assert all(response.status_code == 200 and token not in response.text for response in responses)
    assert inquiry.repository.get(created["id"]).public_access_token is None
    assert all(item.public_access_token is None for item in inquiry.repository.list())


def test_new_payloads_never_store_plaintext_tokens_and_hash_authorization_survives(inquiry):
    created = create(inquiry)
    token = created["public_access_token"]
    assert inquiry.repository.authorize(created["id"], token)
    for append in (False, True):
        if append:
            inquiry.repository.append_message(created["id"], "Synthetic follow-up", "customer")
        assert token not in json.dumps([item.model_dump() for item in inquiry.repository._items.values()])
        if inquiry.backend == "sqlite":
            with sqlite3.connect(inquiry.path) as connection:
                payload, token_hash = connection.execute(
                    "SELECT payload, token_hash FROM inquiries WHERE id = ?", (created["id"],)).fetchone()
            assert token not in payload
            assert "public_access_token" not in json.loads(payload)
            assert token_hash == hashlib.sha256(token.encode()).hexdigest()
    if inquiry.backend == "sqlite":
        from core.shopping.inquiries import SQLiteInquiryRepository
        reopened = SQLiteInquiryRepository(str(inquiry.path))
        assert reopened.authorize(created["id"], token)
        assert reopened.get(created["id"]).public_access_token is None


def seed_legacy_copy(inquiry, created):
    if inquiry.backend == "sqlite":
        with sqlite3.connect(inquiry.path) as connection:
            payload = json.loads(connection.execute(
                "SELECT payload FROM inquiries WHERE id = ?", (created["id"],)).fetchone()[0])
            payload["public_access_token"] = LEGACY_TOKEN
            raw = json.dumps(payload)
            connection.execute("UPDATE inquiries SET payload = ? WHERE id = ?", (raw, created["id"]))
        return raw
    inquiry.repository._items[created["id"]].public_access_token = LEGACY_TOKEN
    return LEGACY_TOKEN


def test_legacy_payload_token_is_redacted_without_migration_or_authority(inquiry):
    created = create(inquiry)
    stored_before = seed_legacy_copy(inquiry, created)
    operator = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    responses = [inquiry.client.get(f"/shopping/inquiries/{created['id']}", headers=headers(created)),
                 inquiry.client.get(f"/shopping/operator/inquiries/{created['id']}", headers=operator),
                 inquiry.client.get("/shopping/operator/inquiries", headers=operator)]
    assert all(response.status_code == 200 and LEGACY_TOKEN not in response.text
               and created["public_access_token"] not in response.text for response in responses)
    assert inquiry.repository.get(created["id"]).public_access_token is None
    assert all(item.public_access_token is None for item in inquiry.repository.list())
    assert not inquiry.repository.authorize(created["id"], LEGACY_TOKEN)
    assert inquiry.client.get(f"/shopping/inquiries/{created['id']}", headers={
        "X-Inquiry-Access-Token": LEGACY_TOKEN}).status_code == 403
    if inquiry.backend == "sqlite":
        with sqlite3.connect(inquiry.path) as connection:
            stored_after = connection.execute(
                "SELECT payload FROM inquiries WHERE id = ?", (created["id"],)).fetchone()[0]
    else:
        stored_after = inquiry.repository._items[created["id"]].public_access_token
    assert stored_after == stored_before


def test_normal_message_update_does_not_reserialize_a_legacy_token(inquiry):
    created = create(inquiry)
    seed_legacy_copy(inquiry, created)
    response = inquiry.client.post(f"/shopping/inquiries/{created['id']}/messages",
                                   headers=headers(created), json={"body": "Synthetic update"})
    assert response.status_code == 200 and LEGACY_TOKEN not in response.text
    assert inquiry.repository.get(created["id"]).public_access_token is None
    if inquiry.backend == "sqlite":
        with sqlite3.connect(inquiry.path) as connection:
            payload = connection.execute(
                "SELECT payload FROM inquiries WHERE id = ?", (created["id"],)).fetchone()[0]
        assert LEGACY_TOKEN not in payload and "public_access_token" not in json.loads(payload)


def test_returned_projection_cannot_restore_a_stored_creation_token(inquiry):
    created = create(inquiry)
    projection = inquiry.repository.get(created["id"])
    projection.public_access_token = created["public_access_token"]
    assert inquiry.repository.get(created["id"]).public_access_token is None
    assert inquiry.repository.list()[0].public_access_token is None


def test_missing_token_hash_never_falls_back_to_legacy_payload_token(inquiry):
    created = create(inquiry)
    seed_legacy_copy(inquiry, created)
    if inquiry.backend == "sqlite":
        with sqlite3.connect(inquiry.path) as connection:
            connection.execute("UPDATE inquiries SET token_hash = '' WHERE id = ?", (created["id"],))
    else:
        inquiry.repository._tokens.pop(created["id"])
    for token in (created["public_access_token"], LEGACY_TOKEN):
        assert inquiry.client.get(f"/shopping/inquiries/{created['id']}", headers={
            "X-Inquiry-Access-Token": token}).status_code == 403


def test_customer_credentials_do_not_authorize_operator_routes(inquiry):
    created = create(inquiry)
    for auth in ({}, headers(created), {"Authorization": f"Bearer {created['public_access_token']}"}):
        for path in ("/shopping/operator/inquiries",
                     f"/shopping/operator/inquiries/{created['id']}"):
            response = inquiry.client.get(path, headers=auth)
            assert response.status_code == 401
            assert response.json() == {"detail": {"code": "operator_authorization_required"}}
        response = inquiry.client.post(f"/shopping/operator/inquiries/{created['id']}/messages",
                                        headers=auth, json={"body": "Denied operator reply"})
        assert response.status_code == 401
    assert inquiry.repository.get(created["id"]).messages == []


def test_catalog_and_product_reads_remain_public_and_unchanged(inquiry):
    paths = ["/shopping/products", "/shopping/products/mock-001", "/shopping/categories"]
    before = [inquiry.client.get(path) for path in paths]
    created = create(inquiry)
    assert inquiry.client.get(f"/shopping/inquiries/{created['id']}").status_code == 401
    for path, original in zip(paths, before):
        current = inquiry.client.get(path)
        assert current.status_code == original.status_code == 200
        assert current.content == original.content
    assert before[0].json()["total"] == 5
    assert before[1].json()["id"] == "mock-001"
    assert inquiry.client.get("/shopping/products/not-found").status_code == 404
