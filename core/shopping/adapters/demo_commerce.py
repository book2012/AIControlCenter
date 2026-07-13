from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path
from typing import Any

from core.shopping.catalog.orange_coco import (
    DEFAULT_CATALOG_ROOT,
    OrangeCocoCatalogBundle,
    OrangeCocoCatalogLoader,
)
from core.shopping.models import Product


CATEGORY_DEFINITIONS = {
    "top": {
        "name": "TOP",
        "slug": "women-tops",
    },
    "dress": {
        "name": "DRESS",
        "slug": "women-dresses",
    },
    "bottom": {
        "name": "BOTTOM",
        "slug": "women-bottoms",
    },
    "outer": {
        "name": "OUTER",
        "slug": "women-outer",
    },
    "bag": {
        "name": "BAG",
        "slug": "women-bags",
    },
    "acc": {
        "name": "ACC",
        "slug": "women-accessories",
    },
}

COLLECTION_DEFINITIONS = {
    "new": {
        "name": "NEW",
        "slug": "new",
    },
    "best": {
        "name": "BEST",
        "slug": "best",
    },
    "sale": {
        "name": "SALE",
        "slug": "sale",
    },
}

CATEGORY_ORDER = (
    "new",
    "best",
    "top",
    "dress",
    "bottom",
    "outer",
    "bag",
    "acc",
    "sale",
)


class DemoCommerceCatalogAdapter:
    """Read-only JSON-backed catalog for Storefront validation."""

    def __init__(
        self,
        catalog_root: Path | str = DEFAULT_CATALOG_ROOT,
    ) -> None:
        self._bundle = OrangeCocoCatalogLoader(
            catalog_root
        ).load()

        self._site_base_url = os.getenv(
            "SHOPPING_DEMO_SITE_BASE_URL",
            "http://bokstory.iptime.org:58088",
        ).rstrip("/")

        self._products = [
            self._map_product(product)
            for product in self._bundle.products
            if product.get("enabled", True)
        ]

        self._products_by_id = {
            product.id: product
            for product in self._products
        }

        self._catalog_by_id = {
            str(product["id"]): product
            for product in self._bundle.products
        }

    def list_products(
        self,
        page: int,
        page_size: int,
    ) -> tuple[list[Product], int]:
        return self._paginate(
            self._products,
            page,
            page_size,
        )

    def get_product(
        self,
        product_id: str,
    ) -> Product | None:
        return self._products_by_id.get(product_id)

    def list_categories(self) -> list[dict]:
        category_counts = {
            category_id: sum(
                1
                for product in self._bundle.products
                if product.get("category") == category_id
                and product.get("enabled", True)
            )
            for category_id in CATEGORY_DEFINITIONS
        }

        collection_counts = {
            collection_id: len(
                self._enabled_collection_product_ids(
                    collection_id
                )
            )
            for collection_id in COLLECTION_DEFINITIONS
        }

        categories: list[dict] = []

        for item_id in CATEGORY_ORDER:
            if item_id in CATEGORY_DEFINITIONS:
                definition = CATEGORY_DEFINITIONS[item_id]
                count = category_counts[item_id]
                item_type = "category"
            else:
                definition = COLLECTION_DEFINITIONS[item_id]
                count = collection_counts[item_id]
                item_type = "collection"

            if count <= 0:
                continue

            categories.append(
                {
                    "id": definition["slug"],
                    "name": definition["name"],
                    "slug": definition["slug"],
                    "count": count,
                    "type": item_type,
                }
            )

        return categories

    def search_products(
        self,
        *,
        query: str | None,
        category: str | None,
        minimum_price: float | None,
        maximum_price: float | None,
        in_stock: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Product], int]:
        products = list(self._products)

        if query:
            normalized_query = query.strip().lower()

            products = [
                product
                for product in products
                if self._matches_query(
                    product,
                    normalized_query,
                )
            ]

        if category:
            products = self._filter_category(
                products,
                category,
            )

        if minimum_price is not None:
            products = [
                product
                for product in products
                if float(product.price) >= minimum_price
            ]

        if maximum_price is not None:
            products = [
                product
                for product in products
                if float(product.price) <= maximum_price
            ]

        if in_stock is not None:
            products = [
                product
                for product in products
                if product.in_stock is in_stock
            ]

        return self._paginate(
            products,
            page,
            page_size,
        )

    def _map_product(
        self,
        product_data: dict[str, Any],
    ) -> Product:
        product_id = str(product_data["id"])

        pricing = self._bundle.pricing[product_id]
        inventory = self._bundle.inventory[product_id]

        effective_price = (
            pricing.get("sale_price")
            if pricing.get("is_sale")
            and pricing.get("sale_price") is not None
            else pricing["regular_price"]
        )

        image_path = str(
            product_data["image_path"]
        ).lstrip("/")

        return Product(
            id=product_id,
            name=str(product_data["name"]),
            slug=str(
                product_data.get("slug")
                or product_id
            ),
            description=str(
                product_data.get("style_story")
                or ""
            ),
            price=Decimal(str(effective_price)),
            currency=str(
                pricing.get("currency", "KRW")
            ),
            category=str(
                product_data.get(
                    "category_label",
                    product_data["category"],
                )
            ),
            in_stock=bool(
                inventory.get("in_stock", False)
            ),
            source="demo",
            image_url=(
                f"{self._site_base_url}/"
                f"{image_path}"
            ),
        )

    def _matches_query(
        self,
        product: Product,
        query: str,
    ) -> bool:
        source = self._catalog_by_id[product.id]

        searchable_values = (
            product.id,
            product.name,
            product.slug,
            product.description,
            product.category,
            str(source.get("style_tip", "")),
            " ".join(
                str(item)
                for item in source.get(
                    "collections",
                    []
                )
            ),
        )

        return any(
            query in value.lower()
            for value in searchable_values
        )

    def _filter_category(
        self,
        products: list[Product],
        category: str,
    ) -> list[Product]:
        normalized = category.strip().lower()

        category_id = self._resolve_category_id(
            normalized
        )

        if category_id is not None:
            return [
                product
                for product in products
                if self._catalog_by_id[
                    product.id
                ].get("category") == category_id
            ]

        collection_id = self._resolve_collection_id(
            normalized
        )

        if collection_id is not None:
            allowed_ids = set(
                self._enabled_collection_product_ids(
                    collection_id
                )
            )

            return [
                product
                for product in products
                if product.id in allowed_ids
            ]

        return []

    @staticmethod
    def _resolve_category_id(
        value: str,
    ) -> str | None:
        for category_id, definition in (
            CATEGORY_DEFINITIONS.items()
        ):
            aliases = {
                category_id,
                definition["name"].lower(),
                definition["slug"].lower(),
            }

            if value in aliases:
                return category_id

        return None

    @staticmethod
    def _resolve_collection_id(
        value: str,
    ) -> str | None:
        for collection_id, definition in (
            COLLECTION_DEFINITIONS.items()
        ):
            aliases = {
                collection_id,
                definition["name"].lower(),
                definition["slug"].lower(),
            }

            if value in aliases:
                return collection_id

        return None

    def _enabled_collection_product_ids(
        self,
        collection_id: str,
    ) -> tuple[str, ...]:
        enabled_ids = {
            product.id
            for product in self._products
        }

        return tuple(
            product_id
            for product_id in (
                self._bundle.collection_product_ids(
                    collection_id
                )
            )
            if product_id in enabled_ids
        )

    @staticmethod
    def _paginate(
        products: list[Product],
        page: int,
        page_size: int,
    ) -> tuple[list[Product], int]:
        if page < 1:
            raise ValueError(
                "page must be greater than or equal to 1"
            )

        if page_size < 1:
            raise ValueError(
                "page_size must be greater than or equal to 1"
            )

        total = len(products)
        start = (page - 1) * page_size
        end = start + page_size

        return products[start:end], total
