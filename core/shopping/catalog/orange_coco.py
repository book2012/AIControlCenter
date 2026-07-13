from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CATALOG_ROOT = Path(
    "brands/orange-coco/catalog"
)


class OrangeCocoCatalogError(RuntimeError):
    """Raised when the Orange Coco catalog package is invalid."""


@dataclass(frozen=True)
class OrangeCocoCatalogBundle:
    products: tuple[dict[str, Any], ...]
    pricing: dict[str, dict[str, Any]]
    inventory: dict[str, dict[str, Any]]
    collections: dict[str, dict[str, Any]]
    homepage: dict[str, Any]

    def get_product(
        self,
        product_id: str,
    ) -> dict[str, Any] | None:
        for product in self.products:
            if product.get("id") == product_id:
                return product

        return None

    def collection_product_ids(
        self,
        collection_id: str,
    ) -> tuple[str, ...]:
        collection = self.collections.get(collection_id)

        if not collection:
            return ()

        return tuple(collection.get("product_ids", ()))


class OrangeCocoCatalogLoader:
    """Load and validate the JSON-first demo catalog package."""

    def __init__(
        self,
        root: Path | str = DEFAULT_CATALOG_ROOT,
    ) -> None:
        self._root = Path(root)

    def load(self) -> OrangeCocoCatalogBundle:
        catalog = self._read_json("catalog.json")
        pricing = self._read_json("pricing.json")
        inventory = self._read_json("inventory.json")
        collections = self._read_json("collections.json")
        homepage = self._read_json("homepage.json")

        products = tuple(catalog.get("products", ()))
        product_ids = {
            str(product.get("id", ""))
            for product in products
        }

        if not products:
            raise OrangeCocoCatalogError(
                "Orange Coco catalog contains no products"
            )

        if "" in product_ids:
            raise OrangeCocoCatalogError(
                "Orange Coco catalog contains an empty product ID"
            )

        if len(product_ids) != len(products):
            raise OrangeCocoCatalogError(
                "Orange Coco catalog contains duplicate product IDs"
            )

        price_map = pricing.get("prices", {})
        inventory_map = inventory.get("inventory", {})
        collection_map = collections.get("collections", {})

        self._validate_id_map(
            "pricing",
            product_ids,
            set(price_map),
        )

        self._validate_id_map(
            "inventory",
            product_ids,
            set(inventory_map),
        )

        for collection_id, collection in collection_map.items():
            unknown_ids = (
                set(collection.get("product_ids", ()))
                - product_ids
            )

            if unknown_ids:
                raise OrangeCocoCatalogError(
                    f"Collection {collection_id!r} references "
                    f"unknown products: {sorted(unknown_ids)}"
                )

        for product in products:
            if product.get("is_demo") is not True:
                raise OrangeCocoCatalogError(
                    "Non-demo product found in Orange Coco demo catalog"
                )

            if (
                product.get("demo_batch_id")
                != "orange-coco-v1"
            ):
                raise OrangeCocoCatalogError(
                    "Unexpected demo batch ID"
                )

        return OrangeCocoCatalogBundle(
            products=products,
            pricing=price_map,
            inventory=inventory_map,
            collections=collection_map,
            homepage=homepage,
        )

    def _read_json(
        self,
        filename: str,
    ) -> dict[str, Any]:
        path = self._root / filename

        if not path.is_file():
            raise OrangeCocoCatalogError(
                f"Catalog file is missing: {path}"
            )

        try:
            payload = json.loads(
                path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:
            raise OrangeCocoCatalogError(
                f"Invalid JSON in {path}: {exc}"
            ) from exc

        if not isinstance(payload, dict):
            raise OrangeCocoCatalogError(
                f"Catalog file must contain an object: {path}"
            )

        return payload

    @staticmethod
    def _validate_id_map(
        name: str,
        product_ids: set[str],
        mapped_ids: set[str],
    ) -> None:
        missing = product_ids - mapped_ids
        unknown = mapped_ids - product_ids

        if missing or unknown:
            raise OrangeCocoCatalogError(
                f"{name} product IDs do not match catalog; "
                f"missing={sorted(missing)}, "
                f"unknown={sorted(unknown)}"
            )
