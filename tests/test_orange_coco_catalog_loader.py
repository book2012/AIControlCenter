from pathlib import Path

import pytest

from core.shopping.catalog.orange_coco import (
    OrangeCocoCatalogError,
    OrangeCocoCatalogLoader,
)


CATALOG_ROOT = Path(
    "brands/orange-coco/catalog"
)


def test_loads_orange_coco_catalog_bundle() -> None:
    bundle = OrangeCocoCatalogLoader(
        CATALOG_ROOT
    ).load()

    assert len(bundle.products) == 92
    assert len(bundle.pricing) == 92
    assert len(bundle.inventory) == 92

    product = bundle.get_product(
        "oc-demo-top-0001"
    )

    assert product is not None
    assert product["category"] == "top"
    assert product["is_demo"] is True


def test_collection_ids_reference_products() -> None:
    bundle = OrangeCocoCatalogLoader(
        CATALOG_ROOT
    ).load()

    known_ids = {
        product["id"]
        for product in bundle.products
    }

    for collection_id in bundle.collections:
        assert set(
            bundle.collection_product_ids(
                collection_id
            )
        ) <= known_ids


def test_missing_catalog_package_fails() -> None:
    with pytest.raises(
        OrangeCocoCatalogError,
        match="missing",
    ):
        OrangeCocoCatalogLoader(
            Path("/tmp/missing-orange-coco-catalog")
        ).load()
