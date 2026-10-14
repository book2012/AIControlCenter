from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.api.routes.account_recovery import mount_account_recovery
from core.shopping.account_recovery import RecoveryReply


class FakeService:
    def __init__(self):
        self.calls = []

    def start_id_lookup(self, name, phone, client):
        self.calls.append(("start", name, phone, client))
        return RecoveryReply("ACKNOWLEDGED", challenge="c" * 43)

    def confirm_id_lookup(self, challenge, phone, code, client):
        self.calls.append(("confirm", challenge, phone, code, client))
        return RecoveryReply("FOUND", login_id="hong123")

    def request_password_reset(self, login, name, phone, client):
        self.calls.append(("reset", login, name, phone, client))
        return RecoveryReply("ACKNOWLEDGED")

    def complete_password_reset(self, token, password):
        self.calls.append(("complete", token, password))
        return RecoveryReply("COMPLETED")


def client():
    app = FastAPI()
    svc = FakeService()
    mount_account_recovery(app, svc, trusted_origin="https://dev.bokstory.duckdns.org")
    return TestClient(app), svc


def headers(**override):
    return {"Origin": "https://dev.bokstory.duckdns.org", **override}


def test_id_recovery_routes_are_same_origin_nostore_and_do_not_cache_identity():
    http, service = client()
    start = http.post("/v1/shop/account-recovery/id-challenge",
        headers=headers(), json={"name": "홍길동", "phone": "+821012345678"})
    assert start.status_code == 200
    assert start.json() == {"state": "ACKNOWLEDGED", "challenge": "c" * 43}
    assert start.headers["cache-control"] == "no-store, private, max-age=0"
    assert start.headers["referrer-policy"] == "no-referrer"
    confirm = http.post("/v1/shop/account-recovery/id-confirm",
        headers=headers(), json={"challenge": "c" * 43, "phone": "+821012345678", "code": "123456"})
    assert confirm.json() == {"state": "FOUND", "login_id": "hong123"}
    assert service.calls[-1][-1] == "127.0.0.1"


def test_reset_request_has_only_generic_public_response_and_origin_is_required():
    http, service = client()
    response = http.post("/v1/shop/account-recovery/password-reset",
        headers=headers(), json={"login_id": "hong123", "name": "홍길동", "phone": "+821012345678"})
    assert response.json() == {"state": "ACKNOWLEDGED"}
    denied = http.post("/v1/shop/account-recovery/password-reset",
        json={"login_id": "hong123", "name": "홍길동", "phone": "+821012345678"})
    assert denied.status_code == 403
    assert denied.json() == {"state": "ACKNOWLEDGED"}


def test_large_or_invalid_bodies_fail_closed_without_echoing_fields():
    http, _ = client()
    large = http.post("/v1/shop/account-recovery/password-reset/complete",
        headers=headers(), content=b"x" * 5000)
    assert large.status_code == 413
    invalid = http.post("/v1/shop/account-recovery/id-confirm",
        headers=headers(), json={"challenge": "short", "phone": "+821012345678", "code": "123456"})
    assert invalid.status_code == 422
    assert "short" not in invalid.text
