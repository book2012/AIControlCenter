from decimal import Decimal

from fastapi.testclient import TestClient
import pytest

from core.api.app import app
from core.api.routes import shopping as shopping_routes
from core.shopping.adapters.mock_commerce import (
    MockCommerceCatalogAdapter,
)
from core.shopping.service import (
    ProductNotFoundError,
    ShoppingService,
)


client = TestClient(app)



@pytest.fixture(autouse=True)
def use_mock_catalog_for_api_tests():
    original_catalog = shopping_routes.shopping.catalog

    shopping_routes.shopping.catalog = (
        MockCommerceCatalogAdapter()
    )

    try:
        yield
    finally:
        shopping_routes.shopping.catalog = original_catalog


def test_mock_catalog_lists_products():
    adapter = MockCommerceCatalogAdapter()

    products, total = adapter.list_products(
        page=1,
        page_size=2,
    )

    assert total == 5
    assert len(products) == 2
    assert products[0].id == "mock-001"
    assert products[0].price == Decimal("29.90")


def test_mock_catalog_pagination():
    adapter = MockCommerceCatalogAdapter()

    products, total = adapter.list_products(
        page=2,
        page_size=2,
    )

    assert total == 5
    assert [product.id for product in products] == [
        "mock-003",
        "mock-004",
    ]


def test_shopping_service_product_not_found():
    service = ShoppingService()

    try:
        service.get_product("missing")
    except ProductNotFoundError as error:
        assert str(error) == "missing"
    else:
        raise AssertionError("ProductNotFoundError was not raised")


def test_product_list_api():
    response = client.get(
        "/shopping/products",
        params={
            "page": 1,
            "page_size": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == "mock-001"
    assert data["items"][0]["source"] == "mock"


def test_product_detail_api():
    response = client.get("/shopping/products/mock-001")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "mock-001"
    assert data["name"] == "AI Home Datacenter Starter Guide"
    assert data["price"] == "29.90"
    assert data["currency"] == "USD"


def test_product_detail_api_returns_404():
    response = client.get("/shopping/products/missing")

    assert response.status_code == 404

    detail = response.json()["detail"]

    assert detail["code"] == "shopping_product_not_found"
    assert detail["product_id"] == "missing"


def test_product_list_rejects_invalid_page():
    response = client.get(
        "/shopping/products",
        params={
            "page": 0,
            "page_size": 20,
        },
    )

    assert response.status_code == 422


def test_product_list_rejects_oversized_page():
    response = client.get(
        "/shopping/products",
        params={
            "page": 1,
            "page_size": 101,
        },
    )

    assert response.status_code == 422
