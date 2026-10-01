"""AIControlCenter-owned Woo READ_ORDER runtime composition."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from core.shopping.adapters.woocommerce_commerce_read import (
    WooCommerceCommerceReadAdapter,
)
from core.shopping.adapters.woocommerce_normalization import (
    build_woocommerce_commerce_read_adapter,
)
from core.shopping.adapters.woocommerce_order_core_bridge import (
    WooCommerceExistingStackOrderReadBridge,
)
from core.shopping.adapters.woocommerce_order_projector import (
    project_woocommerce_order_summary,
)
from core.shopping.adapters.woocommerce_read_transport import (
    WooCommerceReadTransportSession,
)
from core.shopping.adapters.woocommerce_rest import WooCommerceRESTAdapter
from core.shopping.order_core.service import OrderService
from core.shopping.secure_runtime import (
    DEFAULT_WOOCOMMERCE_READ_SECRET_PATH,
    load_secure_woocommerce_read_settings,
)


class WooCommerceRawReadVendor(Protocol):
    def get_product_raw(self, product_id: str) -> dict[str, Any] | None:
        ...

    def list_products_raw(
        self,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        ...

    def get_order_summary_raw(self, order_id: str) -> dict[str, Any] | None:
        ...


class _SynchronousCanonicalOrderReadStack:
    """Sync bridge for the existing async canonical read adapter."""

    def __init__(
        self,
        adapter: WooCommerceCommerceReadAdapter,
    ) -> None:
        self._adapter = adapter

    def get_order_summary(self, context: Any, order_id: str) -> Any | None:
        return asyncio.run(
            self._adapter.get_order_summary(
                context=context,
                order_id=order_id,
            )
        )


@dataclass(frozen=True, slots=True)
class WooCommerceOrderRuntime:
    """The complete read-only composition exposed to AIControlCenter."""

    transport: WooCommerceReadTransportSession | None
    rest_adapter: WooCommerceRESTAdapter | None
    commerce_read_adapter: WooCommerceCommerceReadAdapter
    order_bridge: WooCommerceExistingStackOrderReadBridge
    order_service: OrderService

    @property
    def read_order_enabled(self) -> bool:
        return self.order_bridge.read_order_enabled

    @property
    def list_orders_enabled(self) -> bool:
        return self.order_bridge.list_orders_enabled

    @property
    def writes_enabled(self) -> bool:
        return self.order_bridge.writes_enabled


def _compose(
    *,
    vendor: WooCommerceRawReadVendor,
    rest_adapter: WooCommerceRESTAdapter | None,
    read_context_provider: Callable[[], Any],
    currency_code: str,
    currency_minor_unit: int,
) -> WooCommerceOrderRuntime:
    commerce_read_adapter = build_woocommerce_commerce_read_adapter(
        vendor=vendor,
        currency_code=currency_code,
        currency_minor_unit=currency_minor_unit,
    )
    existing_stack = _SynchronousCanonicalOrderReadStack(
        commerce_read_adapter,
    )
    bridge = WooCommerceExistingStackOrderReadBridge(
        existing_read_stack=existing_stack,
        read_context_provider=read_context_provider,
        order_summary_projector=lambda summary: project_woocommerce_order_summary(
            summary,
            currency_minor_unit=currency_minor_unit,
        ),
    )
    if rest_adapter is not None and rest_adapter._transport.max_retries != 0:
        raise ValueError("woocommerce_retry_authority_must_remain_disabled")
    return WooCommerceOrderRuntime(
        transport=(rest_adapter._transport if rest_adapter is not None else None),
        rest_adapter=rest_adapter,
        commerce_read_adapter=commerce_read_adapter,
        order_bridge=bridge,
        order_service=OrderService(bridge),
    )


def build_offline_woocommerce_order_runtime(
    *,
    vendor: WooCommerceRawReadVendor,
    read_context_provider: Callable[[], Any] = dict,
    currency_code: str = "KRW",
    currency_minor_unit: int = 0,
) -> WooCommerceOrderRuntime:
    """Build the complete graph from an injected fake/offline raw port."""

    return _compose(
        vendor=vendor,
        rest_adapter=None,
        read_context_provider=read_context_provider,
        currency_code=currency_code,
        currency_minor_unit=currency_minor_unit,
    )


def build_live_woocommerce_order_runtime(
    *,
    secret_path: str | None = None,
    read_context_provider: Callable[[], Any] = dict,
    currency_code: str = "KRW",
    currency_minor_unit: int = 0,
) -> WooCommerceOrderRuntime:
    """Explicit live entrypoint; this is the only composition that reads secrets."""

    settings = load_secure_woocommerce_read_settings(
        secret_path=(
            secret_path
            if secret_path is not None
            else DEFAULT_WOOCOMMERCE_READ_SECRET_PATH
        ),
    )
    rest_adapter = WooCommerceRESTAdapter(
        base_url=settings.woocommerce_base_url,
        consumer_key=settings.woocommerce_consumer_key,
        consumer_secret=settings.woocommerce_consumer_secret,
        timeout_seconds=settings.woocommerce_timeout_seconds,
        connect_base_url=settings.woocommerce_connect_base_url,
    )
    return _compose(
        vendor=rest_adapter,
        rest_adapter=rest_adapter,
        read_context_provider=read_context_provider,
        currency_code=currency_code,
        currency_minor_unit=currency_minor_unit,
    )


__all__ = (
    "WooCommerceOrderRuntime",
    "build_live_woocommerce_order_runtime",
    "build_offline_woocommerce_order_runtime",
)
