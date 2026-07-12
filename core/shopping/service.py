from dataclasses import asdict

from core.shopping.adapters.mock_commerce import (
    MockCommerceCatalogAdapter,
)
from core.shopping.config import (
    ShoppingSettings,
    load_shopping_settings,
)
from core.shopping.ports import CommerceCatalogPort


class ProductNotFoundError(Exception):
    pass


class ShoppingService:
    def __init__(
        self,
        settings: ShoppingSettings | None = None,
        catalog: CommerceCatalogPort | None = None,
    ):
        self.settings = settings or load_shopping_settings()
        self.catalog = catalog or MockCommerceCatalogAdapter()

    def health(self) -> dict:
        return {
            "service": "AIShoppingPlatform",
            "status": "ONLINE" if self.settings.enabled else "DISABLED",
            "environment": self.settings.environment,
            "runtime": self.settings.runtime,
            "deployment_target": self.settings.deployment_target,
            "control_plane": "AIControlCenter",
            "write_mode": self.settings.write_mode,
        }

    def readiness(self) -> dict:
        checks = {
            "enabled": self.settings.enabled,
            "write_mode_supported": self.settings.write_mode_supported,
            "safe_default_mode": (
                self.settings.write_mode == "read_only"
                and self.settings.approval_required
                and not self.settings.automation_enabled
            ),
            "deployment_target_configured": bool(
                self.settings.deployment_target
            ),
        }

        ready = all(checks.values())

        return {
            "service": "AIShoppingPlatform",
            "ready": ready,
            "status": "READY" if ready else "NOT_READY",
            "checks": checks,
        }

    def capabilities(self) -> dict:
        write_enabled = self.settings.write_mode in {
            "controlled_write",
            "automated",
        }

        return {
            "service": "AIShoppingPlatform",
            "read_catalog": self.settings.enabled,
            "write_catalog": (
                self.settings.enabled
                and write_enabled
                and self.settings.approval_required
            ),
            "generate_ai_content": (
                self.settings.enabled
                and self.settings.ai_enabled
            ),
            "execute_automation": (
                self.settings.enabled
                and self.settings.automation_enabled
            ),
            "approval_required": self.settings.approval_required,
        }

    def list_products(
        self,
        page: int,
        page_size: int,
    ) -> dict:
        products, total = self.catalog.list_products(
            page=page,
            page_size=page_size,
        )

        return {
            "items": [asdict(product) for product in products],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_product(self, product_id: str) -> dict:
        product = self.catalog.get_product(product_id)

        if product is None:
            raise ProductNotFoundError(product_id)

        return asdict(product)
