from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import re


_STATUS_RE = re.compile(
    r"[a-z0-9][a-z0-9_-]{0,63}\Z"
)

_CURRENCY_RE = re.compile(
    r"[A-Z]{3}\Z"
)


class OrderContractError(ValueError):
    pass


def _bounded_text(
    value: str,
    *,
    field: str,
    maximum: int,
) -> str:
    if type(value) is not str:
        raise OrderContractError(
            f"{field}:TYPE"
        )

    normalized = value.strip()

    if (
        not normalized
        or len(normalized) > maximum
    ):
        raise OrderContractError(
            f"{field}:BOUNDS"
        )

    return normalized


def _money(
    value: Decimal,
    *,
    field: str,
) -> Decimal:
    if type(value) is not Decimal:
        raise OrderContractError(
            f"{field}:TYPE"
        )

    if not value.is_finite():
        raise OrderContractError(
            f"{field}:NON_FINITE"
        )

    if value < Decimal("0"):
        raise OrderContractError(
            f"{field}:NEGATIVE"
        )

    return value


@dataclass(frozen=True, slots=True)
class OrderLineItem:
    provider_line_item_id: int
    product_id: int
    variation_id: int
    sku: str | None
    name: str
    quantity: int
    subtotal: Decimal
    total: Decimal
    total_tax: Decimal

    def __post_init__(self) -> None:
        if (
            type(self.provider_line_item_id)
            is not int
            or self.provider_line_item_id <= 0
        ):
            raise OrderContractError(
                "provider_line_item_id:INVALID"
            )

        if (
            type(self.product_id) is not int
            or self.product_id < 0
        ):
            raise OrderContractError(
                "product_id:INVALID"
            )

        if (
            type(self.variation_id) is not int
            or self.variation_id < 0
        ):
            raise OrderContractError(
                "variation_id:INVALID"
            )

        if (
            type(self.quantity) is not int
            or self.quantity <= 0
        ):
            raise OrderContractError(
                "quantity:INVALID"
            )

        object.__setattr__(
            self,
            "name",
            _bounded_text(
                self.name,
                field="name",
                maximum=512,
            ),
        )

        if self.sku is not None:
            object.__setattr__(
                self,
                "sku",
                _bounded_text(
                    self.sku,
                    field="sku",
                    maximum=256,
                ),
            )

        for field in (
            "subtotal",
            "total",
            "total_tax",
        ):
            _money(
                getattr(self, field),
                field=field,
            )


@dataclass(frozen=True, slots=True)
class OrderSnapshot:
    provider: str
    provider_order_id: int
    provider_reference: str
    order_number: str
    status: str
    currency: str
    customer_reference: str | None
    line_items: tuple[OrderLineItem, ...]
    total: Decimal
    total_tax: Decimal
    created_at: datetime
    updated_at: datetime
    provider_version: str

    def __post_init__(self) -> None:
        if self.provider != "woocommerce":
            raise OrderContractError(
                "provider:INVALID"
            )

        if (
            type(self.provider_order_id)
            is not int
            or self.provider_order_id <= 0
        ):
            raise OrderContractError(
                "provider_order_id:INVALID"
            )

        object.__setattr__(
            self,
            "provider_reference",
            _bounded_text(
                self.provider_reference,
                field="provider_reference",
                maximum=256,
            ),
        )

        object.__setattr__(
            self,
            "order_number",
            _bounded_text(
                self.order_number,
                field="order_number",
                maximum=128,
            ),
        )

        status = _bounded_text(
            self.status,
            field="status",
            maximum=64,
        ).lower()

        if _STATUS_RE.fullmatch(status) is None:
            raise OrderContractError(
                "status:FORMAT"
            )

        object.__setattr__(
            self,
            "status",
            status,
        )

        currency = _bounded_text(
            self.currency,
            field="currency",
            maximum=3,
        ).upper()

        if _CURRENCY_RE.fullmatch(
            currency
        ) is None:
            raise OrderContractError(
                "currency:FORMAT"
            )

        object.__setattr__(
            self,
            "currency",
            currency,
        )

        if self.customer_reference is not None:
            object.__setattr__(
                self,
                "customer_reference",
                _bounded_text(
                    self.customer_reference,
                    field="customer_reference",
                    maximum=256,
                ),
            )

        if type(self.line_items) is not tuple:
            raise OrderContractError(
                "line_items:TYPE"
            )

        for item in self.line_items:
            if type(item) is not OrderLineItem:
                raise OrderContractError(
                    "line_items:MEMBER_TYPE"
                )

        _money(
            self.total,
            field="total",
        )

        _money(
            self.total_tax,
            field="total_tax",
        )

        for field in (
            "created_at",
            "updated_at",
        ):
            value = getattr(self, field)

            if (
                type(value) is not datetime
                or value.tzinfo is None
            ):
                raise OrderContractError(
                    f"{field}:TIMEZONE_REQUIRED"
                )

        object.__setattr__(
            self,
            "provider_version",
            _bounded_text(
                self.provider_version,
                field="provider_version",
                maximum=64,
            ),
        )


@dataclass(frozen=True, slots=True)
class OrderListQuery:
    page: int = 1
    page_size: int = 20
    statuses: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (
            type(self.page) is not int
            or self.page < 1
        ):
            raise OrderContractError(
                "page:INVALID"
            )

        if (
            type(self.page_size) is not int
            or not 1 <= self.page_size <= 100
        ):
            raise OrderContractError(
                "page_size:INVALID"
            )

        if type(self.statuses) is not tuple:
            raise OrderContractError(
                "statuses:TYPE"
            )

        normalized = []

        for status in self.statuses:
            value = _bounded_text(
                status,
                field="status",
                maximum=64,
            ).lower()

            if _STATUS_RE.fullmatch(
                value
            ) is None:
                raise OrderContractError(
                    "status:FORMAT"
                )

            normalized.append(value)

        object.__setattr__(
            self,
            "statuses",
            tuple(normalized),
        )
