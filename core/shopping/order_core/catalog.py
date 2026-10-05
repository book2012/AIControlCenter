"""SHOP_ORDER_001C trusted catalog resolution for order creation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from core.shopping.models import Product
from core.shopping.order_core.create import (
    OrderCreateCommand, OrderCreateContractError, OrderCreateLine,
)


class OrderCreateCatalogRead(Protocol):
    def get_product(self, product_id: str) -> dict:
        ...


class OrderCreateCatalogResolutionError(OrderCreateContractError):
    pass


@dataclass(frozen=True, slots=True)
class ResolvedOrderCreateLine:
    product_id: str
    variation_id: str | None
    provider_product_id: int
    provider_variation_id: int
    quantity: int

    def __post_init__(self) -> None:
        if type(self.product_id) is not str or not self.product_id:
            raise OrderCreateCatalogResolutionError("product_id:INVALID")
        if self.variation_id is not None and (
            type(self.variation_id) is not str or not self.variation_id
        ):
            raise OrderCreateCatalogResolutionError("variation_id:INVALID")
        if type(self.provider_product_id) is not int or self.provider_product_id <= 0:
            raise OrderCreateCatalogResolutionError("provider_product_id:INVALID")
        if type(self.provider_variation_id) is not int or self.provider_variation_id < 0:
            raise OrderCreateCatalogResolutionError("provider_variation_id:INVALID")
        if type(self.quantity) is not int or self.quantity <= 0:
            raise OrderCreateCatalogResolutionError("quantity:INVALID")


@dataclass(frozen=True, slots=True)
class ResolvedOrderCreateCommand:
    customer_id: str
    line_items: tuple[ResolvedOrderCreateLine, ...]

    def __post_init__(self) -> None:
        if type(self.customer_id) is not str or not self.customer_id:
            raise OrderCreateCatalogResolutionError("customer_id:INVALID")
        if type(self.line_items) is not tuple or not self.line_items:
            raise OrderCreateCatalogResolutionError("line_items:INVALID")
        if any(type(item) is not ResolvedOrderCreateLine for item in self.line_items):
            raise OrderCreateCatalogResolutionError("line_items:MEMBER_TYPE")


def _provider_identifier(value: str, field: str) -> int:
    if not value.isdecimal() or value.startswith("0") or len(value) > 20:
        raise OrderCreateCatalogResolutionError(f"{field}:PROVIDER_ID_UNAVAILABLE")
    result = int(value)
    if result <= 0:
        raise OrderCreateCatalogResolutionError(f"{field}:PROVIDER_ID_UNAVAILABLE")
    return result


class ShoppingServiceOrderCatalogResolver:
    """Read-only resolver; it never owns a provider write or credential."""

    def __init__(self, catalog: OrderCreateCatalogRead) -> None:
        self._catalog = catalog

    def resolve(self, command: OrderCreateCommand) -> ResolvedOrderCreateCommand:
        if type(command) is not OrderCreateCommand:
            raise OrderCreateCatalogResolutionError("command:TYPE")
        resolved=[]
        for line in command.line_items:
            product_data=self._catalog.get_product(line.product_id)
            if not isinstance(product_data, dict):
                raise OrderCreateCatalogResolutionError("catalog:INVALID_PRODUCT")
            try:
                product=Product(**product_data)
            except (TypeError, ValueError) as exc:
                raise OrderCreateCatalogResolutionError("catalog:INVALID_PRODUCT") from exc
            if product.id != line.product_id:
                raise OrderCreateCatalogResolutionError("catalog:PRODUCT_ID_MISMATCH")
            if not product.in_stock:
                raise OrderCreateCatalogResolutionError("catalog:OUT_OF_STOCK")
            if product.source != "woocommerce":
                raise OrderCreateCatalogResolutionError("catalog:WRITE_SOURCE_UNAVAILABLE")
            provider_product_id=_provider_identifier(product.id,"product_id")
            provider_variation_id=0
            if line.variation_id is not None:
                variant=next((item for item in product.variants if item.id==line.variation_id),None)
                if variant is None:
                    raise OrderCreateCatalogResolutionError("catalog:VARIATION_NOT_FOUND")
                if not variant.available:
                    raise OrderCreateCatalogResolutionError("catalog:VARIATION_UNAVAILABLE")
                provider_variation_id=_provider_identifier(variant.id,"variation_id")
            resolved.append(ResolvedOrderCreateLine(
                product_id=line.product_id, variation_id=line.variation_id,
                provider_product_id=provider_product_id,
                provider_variation_id=provider_variation_id, quantity=line.quantity,
            ))
        return ResolvedOrderCreateCommand(command.customer_id,tuple(resolved))


__all__=("OrderCreateCatalogRead","OrderCreateCatalogResolutionError",
         "ResolvedOrderCreateCommand","ResolvedOrderCreateLine",
         "ShoppingServiceOrderCatalogResolver")
