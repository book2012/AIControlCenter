from fastapi.testclient import TestClient

from core.api.app import app
from core.api.dependencies.shopping import get_shopping_service
from core.shopping.adapters.mock_commerce import (
    MockCommerceCatalogAdapter,
)
from core.shopping.service import ShoppingService


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
    service = ShoppingService(
        catalog=MockCommerceCatalogAdapter(),
    )
    app.dependency_overrides[get_shopping_service] = lambda: service

    try:
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
        app.dependency_overrides.pop(get_shopping_service, None)
