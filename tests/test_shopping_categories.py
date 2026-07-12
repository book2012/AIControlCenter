from fastapi.testclient import TestClient

from core.api.app import app
from core.api.routes import shopping as shopping_routes
from core.shopping.adapters.mock_commerce import (
    MockCommerceCatalogAdapter,
)


client = TestClient(app)


def test_mock_adapter_lists_categories():
    adapter = MockCommerceCatalogAdapter()

    categories = adapter.list_categories()

    assert categories
    assert all(
        {
            "id",
            "name",
            "slug",
            "count",
        }
        <= set(category)
        for category in categories
    )


def test_category_api_uses_mock_catalog():
    original_catalog = shopping_routes.shopping.catalog

    try:
        shopping_routes.shopping.catalog = (
            MockCommerceCatalogAdapter()
        )

        response = client.get("/shopping/categories")

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == len(data["items"])
        assert data["total"] > 0

        for item in data["items"]:
            assert item["id"]
            assert item["name"]
            assert item["slug"]
            assert item["count"] >= 1
    finally:
        shopping_routes.shopping.catalog = original_catalog
