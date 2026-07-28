from __future__ import annotations

import asyncio

import pytest

from core.shopping.adapters.woocommerce_commerce_read import WooCommerceCommerceReadError
from core.shopping.adapters.woocommerce_normalization import build_woocommerce_commerce_read_adapter
from core.shopping.adapters.woocommerce_rest import WooCommerceRESTAdapter

def product_payload(product_id=42):
    return {
        "id": product_id,
        "name": "Canonical Product",
        "price": "15000",
        "stock_quantity": 3,
        "stock_status": "instock",
        "date_modified_gmt": "2026-07-27T01:02:03",
    }

def order_payload():
    return {
        "id": 7,
        "status": "processing",
        "currency": "KRW",
        "total": "25000",
        "customer_id": 999,
        "date_created_gmt": "2026-07-27T02:00:00",
        "date_modified_gmt": "2026-07-27T03:00:00",
        "line_items": [{"quantity": 2}, {"quantity": 1}],
    }

class FakeVendor:
    def __init__(self):
        self.calls = []
        self.error = None
        self.malformed = False

    def get_product_raw(self, product_id):
        self.calls.append(("get_product_raw", product_id))
        if self.error is not None:
            raise self.error
        value = product_payload(int(product_id))
        if self.malformed:
            value["name"] = ""
        return value

    def list_products_raw(self, page, page_size):
        self.calls.append(("list_products_raw", page, page_size))
        return [product_payload(1), product_payload(2)], 3

    def get_order_summary_raw(self, order_id):
        self.calls.append(("get_order_summary_raw", order_id))
        return order_payload()

def adapter(vendor):
    return build_woocommerce_commerce_read_adapter(
        vendor=vendor,
        currency_code="KRW",
        currency_minor_unit=0,
    )

def test_product_snapshot_normalization():
    vendor = FakeVendor()
    value = asyncio.run(adapter(vendor).get_product(context={}, product_id="42"))
    assert value["product_id"] == "42"
    assert value["price"] == {"amount_minor": 15000, "currency": "KRW"}
    assert value["inventory_quantity"] == 3
    assert value["updated_at"] == "2026-07-27T01:02:03Z"

def test_page_cursor_normalization():
    vendor = FakeVendor()
    value = asyncio.run(adapter(vendor).list_products(context={}, page={"cursor": None, "limit": 2}))
    assert value["has_more"] is True
    assert value["next_cursor"] == "wc-page:2"
    assert vendor.calls == [("list_products_raw", 1, 2)]

def test_order_summary_minimizes_customer_data():
    vendor = FakeVendor()
    value = asyncio.run(adapter(vendor).get_order_summary(context={}, order_id="7"))
    assert value["item_count"] == 3
    assert value["total"] == {"amount_minor": 25000, "currency": "KRW"}
    assert "customer_id" not in value

def test_schema_rejection_fails_closed():
    vendor = FakeVendor()
    vendor.malformed = True
    with pytest.raises(WooCommerceCommerceReadError) as captured:
        asyncio.run(adapter(vendor).get_product(context={}, product_id="42"))
    assert captured.value.reason_code == "normalization_error"

def test_transport_error_is_sanitized():
    vendor = FakeVendor()
    vendor.error = RuntimeError("RAW_VENDOR_SECRET_MUST_NOT_ESCAPE")
    with pytest.raises(WooCommerceCommerceReadError) as captured:
        asyncio.run(adapter(vendor).get_product(context={}, product_id="42"))
    assert captured.value.reason_code == "transport_error"
    assert "RAW_VENDOR_SECRET_MUST_NOT_ESCAPE" not in str(captured.value)

class FakeResponse:
    def __init__(self, payload, headers=None):
        self._payload = payload
        self.headers = headers or {}
        self.status_code = 200
        self.text = ""

    def json(self):
        return self._payload

class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, *, params, auth, headers, timeout, allow_redirects):
        self.calls.append({"url": url, "params": dict(params), "allow_redirects": allow_redirects})
        return self.responses.pop(0)

def test_raw_vendor_reads_are_get_only():
    session = FakeSession([
        FakeResponse(product_payload()),
        FakeResponse([product_payload(1)], {"X-WP-Total": "1"}),
        FakeResponse(order_payload()),
    ])
    client = WooCommerceRESTAdapter("https://shop.example", "key", "secret", session=session)
    assert client.get_product_raw("42")["id"] == 42
    items, total = client.list_products_raw(1, 2)
    assert len(items) == 1
    assert total == 1
    assert client.get_order_summary_raw("7")["id"] == 7
    assert session.calls[0]["params"] == {"context": "view"}
    assert session.calls[1]["params"] == {"context": "view", "status": "publish", "page": 1, "per_page": 2}
    assert session.calls[2]["params"] == {"context": "view"}
    assert all(call["allow_redirects"] is False for call in session.calls)
