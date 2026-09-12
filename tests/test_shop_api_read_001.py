"""SHOP_API_READ_001: fixture-only WooCommerce -> catalog -> public JSON."""
from copy import deepcopy
from dataclasses import replace
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
import requests

from core.api.dependencies.shopping import get_shopping_service
from core.api.routes.shopping import router
from core.shopping.adapters.woocommerce_rest import WooCommerceRESTAdapter
from core.shopping.config import ShoppingSettings
from core.shopping.ports import CatalogReadQueryError
from core.shopping.service import ShoppingService


SETTINGS = ShoppingSettings(
    enabled=True, environment="test", runtime="virtual", deployment_target="mac-mini-m4",
    write_mode="read_only", approval_required=True, automation_enabled=False,
    ai_enabled=False, catalog_adapter="woocommerce",
)
PRODUCT = {
    "id": 42, "name": "코튼 셔츠", "slug": "cotton-shirt", "description": "<p>Cotton</p>",
    "price": "25000.00", "stock_status": "instock", "status": "publish",
    "categories": [{"id": 7, "name": "Shirts"}],
    "images": [{"id": 8, "src": "https://images.example.test/shirt.jpg"}],
    "meta_data": [{"key": "internal_vendor_field", "value": "VENDOR_ONLY"}],
    "_links": {"self": [{"href": "https://commerce.example.test/private"}]},
}
CANONICAL = {
    "id": "42", "name": "코튼 셔츠", "slug": "cotton-shirt", "description": "<p>Cotton</p>",
    "price": "25000", "currency": "KRW", "category": "Shirts", "in_stock": True,
    "source": "woocommerce", "image_url": "https://images.example.test/shirt.jpg",
}


class FakeResponse:
    def __init__(self, payload=None, *, status=200, total="1"):
        self.payload = deepcopy(payload)
        self.status_code = status
        self.headers = {} if total is None else {"X-WP-Total": total}

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return deepcopy(self.payload)


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, *, params, auth, headers, timeout, allow_redirects):
        self.calls.append({"url": url, "params": dict(params), "timeout": timeout,
                           "allow_redirects": allow_redirects})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def make_client(*responses, enabled=True):
    session = FakeSession(responses)
    adapter = WooCommerceRESTAdapter(
        "https://commerce.example.test", "fixture-key", "fixture-value", session=session,
    )
    service = ShoppingService(settings=replace(SETTINGS, enabled=enabled), catalog=adapter)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_shopping_service] = lambda: service
    return TestClient(app), session, service


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      allow_nan=False, separators=(",", ":")).encode("utf-8")


def test_list_and_detail_share_exact_canonical_product_contract():
    client, session, service = make_client(FakeResponse([PRODUCT]), FakeResponse(PRODUCT))
    listing = client.get("/shopping/products")
    detail = client.get("/shopping/products/42")
    expected = {"items": [CANONICAL], "total": 1, "page": 1, "page_size": 20}
    assert listing.status_code == detail.status_code == 200
    assert listing.content == canonical_bytes(expected)
    assert detail.content == canonical_bytes(CANONICAL)
    assert listing.json()["items"][0] == detail.json()
    assert b"VENDOR_ONLY" not in listing.content
    assert b"_links" not in detail.content
    assert listing.headers["content-type"] == "application/json"
    for call in session.calls:
        connect_timeout, read_timeout = call.pop("timeout")
        assert 0 < connect_timeout <= 5.0
        assert 0 < read_timeout <= 10.0
    assert session.calls == [
        {"url": "https://commerce.example.test/wp-json/wc/v3/products",
         "params": {"context": "view", "status": "publish", "page": 1,
                    "per_page": 20, "orderby": "id", "order": "asc"},
         "allow_redirects": False},
        {"url": "https://commerce.example.test/wp-json/wc/v3/products/42",
         "params": {"context": "view"}, "allow_redirects": False},
    ]
    assert service.capabilities()["write_catalog"] is False


def test_equivalent_vendor_objects_produce_identical_bytes_and_do_not_mutate_fixtures():
    original = deepcopy(PRODUCT)
    reordered = dict(reversed(list(PRODUCT.items())))
    reordered["price"] = "25000"
    client, _, service = make_client(FakeResponse(PRODUCT), FakeResponse(reordered), FakeResponse(PRODUCT))
    assert client.get("/shopping/products/42").content == client.get("/shopping/products/42").content
    assert json.loads(json.dumps(service.get_product("42"), allow_nan=False)) == CANONICAL
    assert PRODUCT == original


@pytest.mark.parametrize("page,total,items", [(1, "0", []), (3, "1", []), (2, "2", [PRODUCT])])
def test_pagination_and_empty_catalog_are_successful_observations(page, total, items):
    client, session, _ = make_client(FakeResponse(items, total=total))
    response = client.get("/shopping/products", params={"page": page, "page_size": 1})
    assert response.status_code == 200
    assert response.json() == {"items": [CANONICAL] if items else [], "total": int(total),
                               "page": page, "page_size": 1}
    assert len(session.calls) == 1


@pytest.mark.parametrize("path", ["/shopping/products", "/shopping/products/42"])
@pytest.mark.parametrize("status", [204, 301, 302, 401, 403, 429, 500, 503])
def test_upstream_failures_are_sanitized_unavailable_without_retry(path, status):
    client, session, _ = make_client(FakeResponse({"message": "VENDOR_ONLY"}, status=status))
    response = client.get(path)
    assert response.status_code == 503
    assert response.json() == {"detail": {"code": "shopping_catalog_unavailable"}}
    assert len(session.calls) == 1


@pytest.mark.parametrize("path", ["/shopping/products", "/shopping/products/42"])
@pytest.mark.parametrize("error", [requests.Timeout("VENDOR_ONLY"), requests.ConnectionError("VENDOR_ONLY")])
def test_transport_failures_are_sanitized_without_retry(path, error):
    client, session, _ = make_client(error)
    response = client.get(path)
    assert response.status_code == 503
    assert "VENDOR_ONLY" not in response.text
    assert len(session.calls) == 1


def test_only_detail_404_means_product_not_found():
    client, session, _ = make_client(FakeResponse(status=404), FakeResponse(status=404))
    response = client.get("/shopping/products/42")
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "shopping_product_not_found", "product_id": "42"}}
    assert client.get("/shopping/products").status_code == 503
    assert len(session.calls) == 2


@pytest.mark.parametrize("identifier", ["0", "01", "-1", "abc", "1.5", "１２", "1?x=2", "../orders/1", "1" * 21])
def test_invalid_woocommerce_ids_are_rejected_before_transport(identifier):
    _, session, service = make_client()
    with pytest.raises(CatalogReadQueryError):
        service.get_product(identifier)
    assert session.calls == []


@pytest.mark.parametrize("path", ["/shopping/products/abc", "/shopping/products/0",
                                  "/shopping/products/01", "/shopping/products?page=0",
                                  "/shopping/products?page_size=101", "/shopping/products?page_size=0"])
def test_invalid_api_queries_do_not_call_vendor(path):
    client, session, _ = make_client()
    assert client.get(path).status_code == 422
    assert session.calls == []


@pytest.mark.parametrize("page,page_size", [(True, 20), (0, 20), (1, False), (1, 101)])
def test_direct_service_pagination_is_validated(page, page_size):
    _, session, service = make_client()
    with pytest.raises(CatalogReadQueryError):
        service.list_products(page, page_size)
    assert session.calls == []


@pytest.mark.parametrize("path", ["/shopping/products", "/shopping/products/42"])
def test_disabled_catalog_fails_closed_without_external_read(path):
    client, session, _ = make_client(enabled=False)
    assert client.get(path).status_code == 503
    assert session.calls == []


@pytest.mark.parametrize("field,value", [
    ("id", 43), ("id", True), ("name", None), ("name", ""), ("price", None),
    ("price", ""), ("price", "NaN"), ("price", "Infinity"), ("price", "-1"),
    ("price", "1e99999"), ("price", 1.5), ("stock_status", "unknown"),
    ("categories", "invalid"), ("images", [None]), ("description", {}), ("currency", "USD"),
    ("status", None), ("status", "unknown"), ("status", {}),
])
def test_malformed_product_is_unavailable_without_vendor_payload_leak(field, value):
    payload = {**PRODUCT, field: value}
    client, session, _ = make_client(FakeResponse(payload))
    response = client.get("/shopping/products/42")
    assert response.status_code == 503
    assert response.json() == {"detail": {"code": "shopping_catalog_unavailable"}}
    assert len(session.calls) == 1


@pytest.mark.parametrize("payload,total", [
    ({"error": "VENDOR_ONLY"}, "0"), ([None], "1"), ([PRODUCT], None),
    ([PRODUCT], "invalid"), ([PRODUCT], "-1"), ([PRODUCT], "0"),
    ([PRODUCT], "2"), ([PRODUCT, PRODUCT], "2"),
    ([{**PRODUCT, "id": 43}, PRODUCT], "2"),
    ([{**PRODUCT, "price": "NaN"}], "1"),
])
def test_invalid_pages_are_not_partial_or_empty_successes(payload, total):
    client, session, _ = make_client(FakeResponse(payload, total=total))
    response = client.get("/shopping/products")
    assert response.status_code == 503
    assert response.json() == {"detail": {"code": "shopping_catalog_unavailable"}}
    assert len(session.calls) == 1


@pytest.mark.parametrize("path", ["/shopping/products", "/shopping/products/42"])
def test_invalid_upstream_json_is_sanitized(path):
    client, _, _ = make_client(FakeResponse(ValueError("VENDOR_ONLY")))
    response = client.get(path)
    assert response.status_code == 503
    assert "VENDOR_ONLY" not in response.text


def test_nonpublic_product_is_not_exposed_and_unexpected_list_visibility_fails_closed():
    draft = {**PRODUCT, "status": "draft"}
    client, _, _ = make_client(FakeResponse(draft), FakeResponse([draft]))
    assert client.get("/shopping/products/42").status_code == 404
    assert client.get("/shopping/products").status_code == 503


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
@pytest.mark.parametrize("path", ["/shopping/products", "/shopping/products/42"])
def test_product_api_has_no_mutation_surface(method, path):
    client, session, _ = make_client()
    assert client.request(method, path).status_code == 405
    assert session.calls == []


def test_replacement_catalog_uses_same_public_contract_without_woocommerce_mapping():
    from core.shopping.adapters.mock_commerce import MockCommerceCatalogAdapter

    client, session, service = make_client()
    service.catalog = MockCommerceCatalogAdapter()
    response = client.get("/shopping/products/mock-001")
    assert response.status_code == 200
    assert set(response.json()) == set(CANONICAL)
    assert response.json()["source"] == "mock"
    assert response.json()["price"] == "29.90"
    assert session.calls == []


def test_product_policy_denial_precedes_any_vendor_read(monkeypatch):
    from core.shopping.adapters import woocommerce_rest
    from core.shopping.governance.external_read_policy import evaluate_external_read

    denial = evaluate_external_read(provider="woocommerce", method="POST", path="/wp-json/wc/v3/products")
    monkeypatch.setattr(woocommerce_rest, "evaluate_external_read", lambda **kwargs: denial)
    client, session, _ = make_client()
    assert client.get("/shopping/products").status_code == 503
    assert client.get("/shopping/products/42").status_code == 503
    assert session.calls == []


@pytest.mark.parametrize("stock_status,expected", [("instock", True), ("outofstock", False), ("onbackorder", False)])
def test_optional_presentation_fields_and_stock_mapping(stock_status, expected):
    payload = {"id": 42, "status": "publish", "name": "Basic", "price": "0.00",
               "stock_status": stock_status}
    client, _, _ = make_client(FakeResponse(payload))
    response = client.get("/shopping/products/42")
    assert response.status_code == 200
    assert response.json() == {**CANONICAL, "name": "Basic", "slug": "", "description": "",
                               "price": "0", "category": "Uncategorized", "image_url": None,
                               "in_stock": expected}
