from decimal import Decimal

import pytest

from core.shopping.adapters.woocommerce_rest import (
    WooCommerceAPIError,
    WooCommerceRESTAdapter,
)


class FakeResponse:
    def __init__(
        self,
        payload,
        status_code=200,
        headers=None,
    ):
        self._payload = payload
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(
        self,
        url,
        params,
        auth=None,
        headers=None,
        timeout=None,
        allow_redirects=True,
    ):
        self.calls.append(
            {
                "url": url,
                "params": params,
                "auth": auth,
                "headers": headers or {},
                "timeout": timeout,
                "allow_redirects": allow_redirects,
            }
        )

        return self.responses.pop(0)


def make_adapter(responses):
    return WooCommerceRESTAdapter(
        base_url="http://wordpress.test",
        consumer_key="ck_test",
        consumer_secret="cs_test",
        session=FakeSession(responses),
    )



def test_get_product_returns_product():
    response = FakeResponse(
        {
            "id": 202,
            "name": "상세 상품",
            "slug": "detail-product",
            "description": "상세 설명",
            "price": "25000",
            "stock_status": "outofstock",
            "categories": [],
        }
    )

    adapter = make_adapter([response])
    product = adapter.get_product("202")

    assert product is not None
    assert product.id == "202"
    assert product.in_stock is False
    assert product.category == "Uncategorized"


def test_get_product_returns_none_for_404():
    adapter = make_adapter(
        [
            FakeResponse(
                {
                    "code": "woocommerce_rest_product_invalid_id",
                },
                status_code=404,
            )
        ]
    )

    assert adapter.get_product("missing") is None


def test_list_categories_maps_response():
    adapter = make_adapter(
        [
            FakeResponse(
                [
                    {
                        "id": 3,
                        "name": "AI",
                        "slug": "ai",
                        "count": 2,
                    }
                ]
            )
        ]
    )

    categories = adapter.list_categories()

    assert categories == [
        {
            "id": "3",
            "name": "AI",
            "slug": "ai",
            "count": 2,
        }
    ]


def test_health_returns_connected_status():
    adapter = make_adapter(
        [
            FakeResponse(
                [],
                status_code=200,
            )
        ]
    )

    result = adapter.health()

    assert result["healthy"] is True
    assert result["source"] == "woocommerce"


def test_api_error_is_raised_for_server_failure():
    adapter = make_adapter(
        [
            FakeResponse(
                {
                    "message": "server error",
                },
                status_code=500,
            )
        ]
    )

    with pytest.raises(
        WooCommerceAPIError,
        match="HTTP 500",
    ):
        adapter.list_products(
            page=1,
            page_size=20,
        )


def test_http_request_uses_oauth_parameters():
    adapter = make_adapter(
        [
            FakeResponse(
                [],
                status_code=200,
            )
        ]
    )

    adapter.health()

    call = adapter.session.calls[0]

    assert call["auth"] is None
    assert call["params"]["oauth_consumer_key"] == "ck_test"
    assert call["params"]["oauth_signature_method"] == "HMAC-SHA256"
    assert call["params"]["oauth_nonce"]
    assert call["params"]["oauth_timestamp"]
    assert call["params"]["oauth_signature"]


def test_https_request_uses_basic_auth():
    session = FakeSession(
        [
            FakeResponse(
                [],
                status_code=200,
            )
        ]
    )

    adapter = WooCommerceRESTAdapter(
        base_url="https://wordpress.test",
        consumer_key="ck_test",
        consumer_secret="cs_test",
        session=session,
    )

    adapter.health()

    call = session.calls[0]

    assert call["auth"] == (
        "ck_test",
        "cs_test",
    )
    assert "oauth_signature" not in call["params"]


def test_internal_connection_uses_canonical_host_for_signature():
    session = FakeSession(
        [
            FakeResponse(
                [],
                status_code=200,
            )
        ]
    )

    adapter = WooCommerceRESTAdapter(
        base_url="http://bokstory.iptime.org:58088",
        connect_base_url="http://127.0.0.1:8088",
        consumer_key="ck_test",
        consumer_secret="cs_test",
        session=session,
    )

    adapter.health()

    call = session.calls[0]

    assert call["url"].startswith(
        "http://127.0.0.1:8088/"
    )
    assert call["headers"]["Host"] == (
        "bokstory.iptime.org:58088"
    )
    assert call["allow_redirects"] is False
    assert call["params"]["oauth_signature"]


def test_list_products_maps_woocommerce_response():
    session = FakeSession(
        [
            FakeResponse(
                [
                    {
                        "id": 101,
                        "name": "테스트 상품",
                        "slug": "test-product",
                        "description": "상품 설명",
                        "price": "15900",
                        "stock_status": "instock",
                        "categories": [
                            {
                                "id": 7,
                                "name": "테스트",
                            }
                        ],
                        "images": [
                            {
                                "id": 10,
                                "src": (
                                    "https://example.test/"
                                    "product.jpg"
                                ),
                            }
                        ],
                    }
                ],
                headers={
                    "X-WP-Total": "1",
                },
            )
        ]
    )

    adapter = WooCommerceRESTAdapter(
        base_url="http://wordpress.test",
        consumer_key="ck_test",
        consumer_secret="cs_test",
        session=session,
    )

    products, total = adapter.list_products(
        page=1,
        page_size=20,
    )

    assert total == 1
    assert products[0].id == "101"
    assert products[0].price == Decimal("15900")
    assert products[0].currency == "KRW"
    assert products[0].source == "woocommerce"
    assert products[0].image_url == (
        "https://example.test/product.jpg"
    )


def test_product_without_image_maps_none():
    session = FakeSession(
        [
            FakeResponse(
                [
                    {
                        "id": 202,
                        "name": "이미지 없는 상품",
                        "slug": "product-without-image",
                        "description": "",
                        "price": "9900",
                        "stock_status": "instock",
                        "categories": [],
                        "images": [],
                    }
                ],
                headers={
                    "X-WP-Total": "1",
                },
            )
        ]
    )

    adapter = WooCommerceRESTAdapter(
        base_url="http://wordpress.test",
        consumer_key="ck_test",
        consumer_secret="cs_test",
        session=session,
    )

    products, total = adapter.list_products(
        page=1,
        page_size=20,
    )

    assert total == 1
    assert products[0].image_url is None
