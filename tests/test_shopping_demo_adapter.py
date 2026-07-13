from decimal import Decimal

from core.shopping.adapters.demo_commerce import (
    DemoCommerceCatalogAdapter,
)
from core.shopping.factory import create_catalog_adapter


def test_demo_catalog_loads_all_products() -> None:
    adapter = DemoCommerceCatalogAdapter()

    products, total = adapter.list_products(
        page=1,
        page_size=100,
    )

    assert total == 92
    assert len(products) == 92
    assert all(
        product.id.startswith("oc-demo-")
        for product in products
    )
    assert all(
        product.image_url is not None
        for product in products
    )


def test_demo_catalog_lists_categories_and_collections() -> None:
    adapter = DemoCommerceCatalogAdapter()

    categories = adapter.list_categories()

    by_slug = {
        category["slug"]: category
        for category in categories
    }

    assert by_slug["women-tops"]["count"] == 20
    assert by_slug["women-dresses"]["count"] == 20
    assert by_slug["women-bottoms"]["count"] == 15
    assert by_slug["women-outer"]["count"] == 15
    assert by_slug["women-bags"]["count"] == 12
    assert by_slug["women-accessories"]["count"] == 10

    assert by_slug["new"]["count"] == 24
    assert by_slug["best"]["count"] > 0
    assert by_slug["sale"]["count"] > 0


def test_demo_catalog_searches_by_category_slug() -> None:
    adapter = DemoCommerceCatalogAdapter()

    products, total = adapter.search_products(
        query=None,
        category="women-dresses",
        minimum_price=None,
        maximum_price=None,
        in_stock=None,
        page=1,
        page_size=100,
    )

    assert total == 20
    assert all(
        product.category == "DRESS"
        for product in products
    )


def test_demo_catalog_searches_sale_collection() -> None:
    adapter = DemoCommerceCatalogAdapter()

    products, total = adapter.search_products(
        query=None,
        category="sale",
        minimum_price=None,
        maximum_price=None,
        in_stock=None,
        page=1,
        page_size=100,
    )

    assert total > 0
    assert products

    first_product = products[0]

    assert isinstance(
        first_product.price,
        Decimal,
    )


def test_demo_catalog_filters_out_of_stock_products() -> None:
    adapter = DemoCommerceCatalogAdapter()

    products, total = adapter.search_products(
        query=None,
        category=None,
        minimum_price=None,
        maximum_price=None,
        in_stock=False,
        page=1,
        page_size=100,
    )

    assert total == 2
    assert all(
        product.in_stock is False
        for product in products
    )


def test_demo_catalog_gets_product_by_id() -> None:
    adapter = DemoCommerceCatalogAdapter()

    product = adapter.get_product(
        "oc-demo-top-0001"
    )

    assert product is not None
    assert product.category == "TOP"
    assert product.source == "demo"
    assert (
        "orange-coco-v1/products/top/"
        in str(product.image_url)
    )


def test_factory_creates_demo_adapter() -> None:
    adapter = create_catalog_adapter("demo")

    assert isinstance(
        adapter,
        DemoCommerceCatalogAdapter,
    )
