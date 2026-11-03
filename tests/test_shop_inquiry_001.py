from core.homepage.preview import create_app as create_preview
from fastapi import FastAPI
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def inquiry_app(monkeypatch):
    """Exercise inquiry contracts in explicit test composition, never public preview."""
    import socket
    import sqlite3
    from core.config.loader import ConfigLoader
    from core.api.dependencies.inquiries import get_inquiry_repository
    from core.api.dependencies.shopping import get_shopping_service
    from core.api.routes.shopping import router
    from core.shopping.adapters.demo_commerce import DemoCommerceCatalogAdapter
    from core.shopping.config import ShoppingSettings
    from core.shopping.inquiries import InMemoryInquiryRepository
    from core.shopping.service import ShoppingService
    def blocked(*args, **kwargs):
        raise AssertionError("inquiry contract test attempted external access")
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(sqlite3, "connect", blocked)
    monkeypatch.setattr(ConfigLoader, "load", blocked)
    monkeypatch.delenv("AICC_INSTAGRAM_CONTACT_URL", raising=False)
    service = ShoppingService(settings=ShoppingSettings(
        enabled=True, environment="test", runtime="virtual", deployment_target="mac-mini-m4",
        write_mode="read_only", approval_required=True, automation_enabled=False,
        ai_enabled=False, catalog_adapter="demo"), catalog=DemoCommerceCatalogAdapter())
    repo = InMemoryInquiryRepository()
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_shopping_service] = lambda: service
    app.dependency_overrides[get_inquiry_repository] = lambda: repo
    return app


def test_public_preview_keeps_inquiry_mutations_disabled():
    with TestClient(create_preview()) as client:
        assert client.post("/shopping/inquiries", json={"product_id":"oc-demo-top-0001"}).status_code == 404
        assert client.get("/shopping/inquiries/AG-INQ-000001").status_code == 404


def test_inquiry_contract_resolves_canonical_product_variant_and_kakao(inquiry_app):
    with TestClient(inquiry_app) as client:
        channels = client.get("/shopping/contact-channels")
        assert channels.status_code == 200
        assert channels.json()["items"] == [{"type": "kakao_openchat", "label": "카카오 오픈채팅", "url": "https://open.kakao.com/o/sV26tFNi", "enabled": True}]
        missing = client.post("/shopping/inquiries", json={"product_id": "oc-demo-top-0001"})
        assert missing.status_code == 422 and missing.json()["detail"]["code"] == "shopping_variant_required"
        created = client.post("/shopping/inquiries", json={"product_id": "oc-demo-top-0001", "variant_id": "oc-demo-top-0001-m", "message": "<script>alert(1)</script>"})
        assert created.status_code == 200
        payload = created.json()
        assert payload["id"].startswith("AG-INQ-") and payload["product"] == {"id": "oc-demo-top-0001", "name": "소프트 린넨 블라우스"}
        assert payload["variant"] == {"id": "oc-demo-top-0001-m", "label": "M"}
        assert "<script>" not in payload["formatted_message"] and payload["id"] in payload["formatted_message"] and "선택 사이즈: M" in payload["formatted_message"]
        assert client.get(f"/shopping/inquiries/{payload['id']}").status_code == 401
        fetched = client.get(f"/shopping/inquiries/{payload['id']}", headers={"X-Inquiry-Access-Token": payload["public_access_token"]}).json()
        assert fetched == {**payload, "public_access_token": None}
        assert payload["public_access_token"] and client.post(f"/shopping/inquiries/{payload['id']}/messages", headers={"X-Inquiry-Access-Token": payload["public_access_token"]}, json={"body": "추가 문의"}).status_code == 200


def test_inquiry_rejects_fabricated_or_cross_product_variants_and_uses_empty_variant_state(inquiry_app):
    with TestClient(inquiry_app) as client:
        assert client.post("/shopping/inquiries", json={"product_id": "oc-demo-top-0001", "variant_id": "fake", "name": "fake"}).status_code == 422
        assert client.post("/shopping/inquiries", json={"product_id": "oc-demo-top-0001", "variant_id": "oc-demo-top-0002-free"}).status_code == 422
        no_variant = client.post("/shopping/inquiries", json={"product_id": "oc-demo-top-0003"})
        assert no_variant.status_code == 200 and no_variant.json()["variant"] is None and "선택 사이즈:" not in no_variant.json()["formatted_message"]
        assert client.post("/shopping/inquiries", json={"product_id": "no-such-product"}).status_code == 404
