from typing import Protocol

from core.shopping.models import Product


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
