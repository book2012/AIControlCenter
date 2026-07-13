from fastapi.testclient import TestClient

from core.api.app import app
from core.api.routes import shopping as shopping_routes
from core.shopping.adapters.mock_commerce import (
    MockCommerceCatalogAdapter,
)
from core.shopping.service import ShoppingService


client = TestClient(app)


def test_service_searches_by_query():
    service = ShoppingService(
        catalog=MockCommerceCatalogAdapter(),
    )

    result = service.search_products(
        query="AI",
        category=None,
        minimum_price=None,
        maximum_price=None,
        in_stock=None,
        page=1,
        page_size=20,
    )

    assert result["total"] > 0
    assert result["items"]

    for item in result["items"]:
        combined = (
            item["name"]
            + item["description"]
            + item["slug"]
        ).lower()

        assert "ai" in combined


def test_service_filters_in_stock():
    service = ShoppingService(
        catalog=MockCommerceCatalogAdapter(),
    )

    result = service.search_products(
        query=None,
        category=None,
        minimum_price=None,
        maximum_price=None,
        in_stock=True,
        page=1,
        page_size=20,
    )

    assert all(
        item["in_stock"] is True
        for item in result["items"]
    )


def test_search_api():
    original_catalog = shopping_routes.shopping.catalog

    try:
        shopping_routes.shopping.catalog = (
            MockCommerceCatalogAdapter()
        )

        response = client.get(
            "/shopping/search?q=AI&page=1&page_size=10"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["filters"]["query"] == "AI"
        assert data["items"]
    finally:
        shopping_routes.shopping.catalog = original_catalog


def test_search_price_range_validation():
    response = client.get(
        "/shopping/search"
        "?minimum_price=50000"
        "&maximum_price=10000"
    )

    assert response.status_code == 422

    detail = response.json()["detail"]

    assert detail["code"] == (
        "shopping_invalid_price_range"
    )


def test_search_page_size_validation():
    response = client.get(
        "/shopping/search?page_size=101"
    )

    assert response.status_code == 422
