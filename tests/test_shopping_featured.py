from fastapi.testclient import TestClient

from core.api.app import app
from core.api.routes import shopping as shopping_routes
from core.shopping.adapters.mock_commerce import (
    MockCommerceCatalogAdapter,
)
from core.shopping.service import ShoppingService


client = TestClient(app)


def test_service_returns_featured_products():
    service = ShoppingService(
        catalog=MockCommerceCatalogAdapter(),
    )

    result = service.list_featured_products(
        limit=3,
    )

    assert result["total"] == 3
    assert result["limit"] == 3
    assert result["strategy"] == "in_stock_first"
    assert result["available_catalog_total"] >= 3
    assert len(result["items"]) == 3


def test_featured_products_prioritize_in_stock():
    service = ShoppingService(
        catalog=MockCommerceCatalogAdapter(),
    )

    result = service.list_featured_products(
        limit=5,
    )

    stock_values = [
        item["in_stock"]
        for item in result["items"]
    ]

    first_out_of_stock = next(
        (
            index
            for index, value in enumerate(stock_values)
            if value is False
        ),
        len(stock_values),
    )

    assert all(
        stock_values[index] is True
        for index in range(first_out_of_stock)
    )


def test_featured_products_api():
    original_catalog = shopping_routes.shopping.catalog

    try:
        shopping_routes.shopping.catalog = (
            MockCommerceCatalogAdapter()
        )

        response = client.get(
            "/shopping/featured-products?limit=2"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 2
        assert data["limit"] == 2
        assert data["strategy"] == "in_stock_first"
        assert len(data["items"]) == 2
    finally:
        shopping_routes.shopping.catalog = original_catalog


def test_featured_products_limit_validation():
    response = client.get(
        "/shopping/featured-products?limit=0"
    )

    assert response.status_code == 422
