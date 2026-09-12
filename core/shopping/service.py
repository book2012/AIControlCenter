from dataclasses import asdict

from core.shopping.config import (
    ShoppingSettings,
    load_shopping_settings,
)
from core.shopping.factory import create_catalog_adapter
from core.shopping.models import Product
from core.shopping.observability.health_probe import DEFAULT_STATE_BY_FAILURE, HealthFailureCode
from core.shopping.ports import CatalogReadQueryError, CatalogReadUnavailable, CommerceCatalogPort
from core.shopping.schemas import ProductListResponse, ProductResponse


class ProductNotFoundError(Exception):
    pass


class ShoppingService:
    def __init__(
        self,
        settings: ShoppingSettings | None = None,
        catalog: CommerceCatalogPort | None = None,
    ):
        self.settings = settings or load_shopping_settings()

        self.catalog = catalog or create_catalog_adapter(
            self.settings.catalog_adapter,
            woocommerce_base_url=(
                self.settings.woocommerce_base_url
            ),
            woocommerce_connect_base_url=(
                self.settings.woocommerce_connect_base_url
            ),
            woocommerce_consumer_key=(
                self.settings.woocommerce_consumer_key
            ),
            woocommerce_consumer_secret=(
                self.settings.woocommerce_consumer_secret
            ),
            timeout_seconds=(
                self.settings.woocommerce_timeout_seconds
            ),
        )

    def health(self) -> dict:
        return {
            "service": "AIShoppingPlatform",
            "status": (
                "ONLINE"
                if self.settings.enabled
                else "DISABLED"
            ),
            "environment": self.settings.environment,
            "runtime": self.settings.runtime,
            "deployment_target": (
                self.settings.deployment_target
            ),
            "control_plane": "AIControlCenter",
            "write_mode": self.settings.write_mode,
        }

    def readiness(self) -> dict:
        checks = {
            "enabled": self.settings.enabled,
            "write_mode_supported": (
                self.settings.write_mode_supported
            ),
            "safe_default_mode": (
                self.settings.write_mode == "read_only"
                and self.settings.approval_required
                and not self.settings.automation_enabled
            ),
            "deployment_target_configured": bool(
                self.settings.deployment_target
            ),
            "catalog_adapter_supported": (
                self.settings.catalog_adapter_supported
            ),
        }

        ready = all(checks.values())

        return {
            "service": "AIShoppingPlatform",
            "ready": ready,
            "status": (
                "READY"
                if ready
                else "NOT_READY"
            ),
            "checks": checks,
        }

    def read_path_health(self) -> dict:
        """One fresh bounded catalog read; liveness remains configuration-only."""
        failure = HealthFailureCode.NONE
        try:
            self.list_products(page=1, page_size=1)
        except CatalogReadUnavailable as error:
            failure = error.failure_code
        except CatalogReadQueryError:
            # The probe uses a fixed valid query; rejection is an adapter failure.
            failure = HealthFailureCode.UNKNOWN
        return {
            "service": "AIShoppingPlatform",
            "healthy": failure is HealthFailureCode.NONE,
            "state": DEFAULT_STATE_BY_FAILURE[failure].value,
            "failure_code": failure.value,
            "read_only": True,
        }

    def capabilities(self) -> dict:
        return {
            "service": "AIShoppingPlatform",
            "read_catalog": self.settings.enabled,
            "write_catalog": False,
            "configured_write_mode": self.settings.write_mode,
            "write_executor_available": False,
            "production_mutation_authorized": False,
            "generate_ai_content": (
                self.settings.enabled
                and self.settings.ai_enabled
            ),
            "execute_automation": (
                self.settings.enabled
                and self.settings.automation_enabled
            ),
            "approval_required": (
                self.settings.approval_required
            ),
        }

    def integration_status(self) -> dict:
        return {
            "catalog_adapter": (
                self.settings.catalog_adapter
            ),
            "configured": True,
            "read_only": (
                self.settings.write_mode == "read_only"
            ),
            "source": type(self.catalog).__name__,
        }




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
    ) -> dict:
        products, total = self.catalog.search_products(
            query=query,
            category=category,
            minimum_price=minimum_price,
            maximum_price=maximum_price,
            in_stock=in_stock,
            page=page,
            page_size=page_size,
        )

        return {
            "items": [
                asdict(product)
                for product in products
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "filters": {
                "query": query,
                "category": category,
                "minimum_price": minimum_price,
                "maximum_price": maximum_price,
                "in_stock": in_stock,
            },
        }

    def list_featured_products(
        self,
        limit: int = 4,
    ) -> dict:
        products, total = self.catalog.list_products(
            page=1,
            page_size=max(limit * 3, limit),
        )

        in_stock = [
            product
            for product in products
            if product.in_stock
        ]

        out_of_stock = [
            product
            for product in products
            if not product.in_stock
        ]

        selected = (
            in_stock + out_of_stock
        )[:limit]

        return {
            "items": [
                asdict(product)
                for product in selected
            ],
            "total": len(selected),
            "available_catalog_total": total,
            "limit": limit,
            "strategy": "in_stock_first",
        }

    def list_categories(self) -> dict:
        categories = self.catalog.list_categories()

        return {
            "items": categories,
            "total": len(categories),
        }

    def list_products(
        self,
        page: int,
        page_size: int,
    ) -> dict:
        if (type(page) is not int or page < 1 or type(page_size) is not int
                or not 1 <= page_size <= 100):
            raise CatalogReadQueryError("shopping_invalid_product_query")
        if not self.settings.enabled:
            raise CatalogReadUnavailable("shopping_catalog_unavailable",
                                         failure_code=HealthFailureCode.CONFIGURATION)
        try:
            observation = self.catalog.list_products(page=page, page_size=page_size)
        except (CatalogReadQueryError, CatalogReadUnavailable):
            raise
        except Exception:
            raise CatalogReadUnavailable("shopping_catalog_unavailable") from None

        try:
            products, total = observation
            if (not isinstance(products, list) or type(total) is not int or total < 0
                    or len(products) != min(page_size, max(0, total - (page - 1) * page_size))):
                raise ValueError
            return ProductListResponse(
                items=[self._product_response(product) for product in products],
                total=total, page=page, page_size=page_size,
            ).model_dump(mode="json")
        except (TypeError, ValueError):
            raise CatalogReadUnavailable("shopping_catalog_unavailable",
                                         failure_code=HealthFailureCode.SCHEMA_MISMATCH) from None

    @staticmethod
    def _product_response(product: Product) -> ProductResponse:
        if not isinstance(product, Product):
            raise ValueError
        response = ProductResponse(**asdict(product))
        # JSON strings containing unpaired surrogates cannot be rendered as UTF-8.
        for value in response.model_dump().values():
            if isinstance(value, str):
                value.encode("utf-8")
        return response

    def get_product(
        self,
        product_id: str,
    ) -> dict:
        if (not isinstance(product_id, str) or not product_id or len(product_id) > 128
                or not product_id.isascii()
                or not all(char.isalnum() or char in "-_" for char in product_id)):
            raise CatalogReadQueryError("shopping_invalid_product_query")
        if not self.settings.enabled:
            raise CatalogReadUnavailable("shopping_catalog_unavailable",
                                         failure_code=HealthFailureCode.CONFIGURATION)
        try:
            product = self.catalog.get_product(product_id)
        except (CatalogReadQueryError, CatalogReadUnavailable):
            raise
        except Exception:
            raise CatalogReadUnavailable("shopping_catalog_unavailable") from None

        if product is None:
            raise ProductNotFoundError(product_id)

        try:
            response = self._product_response(product)
            if response.id != product_id:
                raise ValueError("product identity mismatch")
            return response.model_dump(mode="json")
        except (TypeError, ValueError):
            raise CatalogReadUnavailable("shopping_catalog_unavailable",
                                         failure_code=HealthFailureCode.SCHEMA_MISMATCH) from None
