from decimal import Decimal

from core.shopping.models import Product


class MockCommerceCatalogAdapter:
    def __init__(self):
        self._products = [
            Product(
                id="mock-001",
                name="AI Home Datacenter Starter Guide",
                slug="ai-home-datacenter-starter-guide",
                description="A practical guide for building an AI Home Datacenter.",
                price=Decimal("29.90"),
                currency="USD",
                category="Guides",
                in_stock=True,
                source="mock",
            ),
            Product(
                id="mock-002",
                name="AI Shopping Automation Template",
                slug="ai-shopping-automation-template",
                description="Reusable workflow templates for AI commerce automation.",
                price=Decimal("49.90"),
                currency="USD",
                category="Automation",
                in_stock=True,
                source="mock",
            ),
            Product(
                id="mock-003",
                name="Commerce Analytics Dashboard Pack",
                slug="commerce-analytics-dashboard-pack",
                description="Dashboard components for sales and product analytics.",
                price=Decimal("39.90"),
                currency="USD",
                category="Analytics",
                in_stock=False,
                source="mock",
            ),
            Product(
                id="mock-004",
                name="AI SEO Content Toolkit",
                slug="ai-seo-content-toolkit",
                description="Structured prompts and workflows for commerce SEO.",
                price=Decimal("19.90"),
                currency="USD",
                category="SEO",
                in_stock=True,
                source="mock",
            ),
            Product(
                id="mock-005",
                name="Shopping Assistant Blueprint",
                slug="shopping-assistant-blueprint",
                description="Architecture blueprint for an AI-native shopping assistant.",
                price=Decimal("59.90"),
                currency="USD",
                category="AI",
                in_stock=True,
                source="mock",
            ),
        ]

    def list_products(
        self,
        page: int,
        page_size: int,
    ) -> tuple[list[Product], int]:
        start = (page - 1) * page_size
        end = start + page_size

        return self._products[start:end], len(self._products)

    def get_product(self, product_id: str) -> Product | None:
        for product in self._products:
            if product.id == product_id:
                return product

        return None

    def list_categories(self) -> list[dict]:
        categories: dict[str, int] = {}

        for product in self._products:
            categories[product.category] = (
                categories.get(product.category, 0) + 1
            )

        return [
            {
                "id": str(index),
                "name": name,
                "slug": name.lower().replace(" ", "-"),
                "count": count,
            }
            for index, (name, count) in enumerate(
                sorted(categories.items()),
                start=1,
            )
        ]

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
            normalized = query.strip().lower()
            products = [
                product
                for product in products
                if normalized in product.name.lower()
                or normalized in product.description.lower()
                or normalized in product.slug.lower()
            ]

        if category:
            normalized_category = category.strip().lower()
            products = [
                product
                for product in products
                if product.category.lower() == normalized_category
            ]

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

        total = len(products)
        start = (page - 1) * page_size
        end = start + page_size

        return products[start:end], total
