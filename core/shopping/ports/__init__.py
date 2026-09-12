from typing import Protocol

from core.shopping.models import Product
from core.shopping.observability.health_probe import HealthFailureCode


class CatalogReadUnavailable(RuntimeError):
    """The catalog could not supply a valid observation; never an empty result."""

    def __init__(self, message: str, *, failure_code: HealthFailureCode = HealthFailureCode.UNKNOWN):
        super().__init__(message)
        # Only repository-owned codes cross the adapter boundary.
        try:
            code = HealthFailureCode(failure_code)
        except (TypeError, ValueError):
            code = HealthFailureCode.UNKNOWN
        self.failure_code = (
            HealthFailureCode.UNKNOWN
            if code in {HealthFailureCode.NONE, HealthFailureCode.LATENCY} else code
        )


class CatalogReadQueryError(ValueError):
    """Invalid product identifier or pagination; rejected before external I/O."""


class CommerceCatalogPort(Protocol):
    def list_products(
        self,
        page: int,
        page_size: int,
    ) -> tuple[list[Product], int]:
        ...

    def get_product(self, product_id: str) -> Product | None:
        ...

    def list_categories(self) -> list[dict]:
        ...


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
        ...
