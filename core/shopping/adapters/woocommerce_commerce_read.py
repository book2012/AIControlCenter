from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol

from core.shopping.contracts.provisional import (
    OrderSummary,
    PageRequest,
    ProductSnapshot,
    ProductSnapshotPage,
    ReadContext,
)
from core.shopping.governance.external_read_policy import (
    evaluate_external_read,
)


class WooCommerceCommerceReadError(RuntimeError):
    def __init__(
        self,
        reason_code: str,
    ) -> None:
        super().__init__(
            reason_code
        )
        self.reason_code = reason_code


class LegacyWooCommerceCatalog(Protocol):
    def get_product(
        self,
        product_id: str,
    ) -> Any | None:
        ...

    def list_products(
        self,
        page: int,
        page_size: int,
    ) -> tuple[list[Any], int]:
        ...


class WooCommerceOrderReader(Protocol):
    def get_order_summary(
        self,
        order_id: str,
    ) -> Any | None:
        ...


CursorPageDecoder = Callable[
    [Any],
    int,
]

ProductNormalizer = Callable[
    [Any],
    ProductSnapshot,
]

ProductPageNormalizer = Callable[
    [
        Sequence[Any],
        int,
        PageRequest,
        int,
    ],
    ProductSnapshotPage,
]

OrderSummaryNormalizer = Callable[
    [Any],
    OrderSummary,
]


class WooCommerceCommerceReadAdapter:
    def __init__(
        self,
        *,
        catalog: LegacyWooCommerceCatalog,
        order_reader: WooCommerceOrderReader,
        cursor_page_decoder: CursorPageDecoder,
        product_normalizer: ProductNormalizer,
        product_page_normalizer: ProductPageNormalizer,
        order_summary_normalizer: OrderSummaryNormalizer,
    ) -> None:
        self._catalog = catalog
        self._order_reader = order_reader
        self._cursor_page_decoder = (
            cursor_page_decoder
        )
        self._product_normalizer = (
            product_normalizer
        )
        self._product_page_normalizer = (
            product_page_normalizer
        )
        self._order_summary_normalizer = (
            order_summary_normalizer
        )

    @staticmethod
    def _authorize_external_read(
        *,
        path: str,
        query: Mapping[str, str],
    ) -> None:
        decision = evaluate_external_read(
            provider="woocommerce",
            method="GET",
            path=path,
            query=query,
        )

        if decision.allowed is not True:
            raise WooCommerceCommerceReadError(
                "external_read_policy_denied"
            )

    @staticmethod
    def _validate_identifier(
        value: Any,
    ) -> str:
        identifier = str(value)

        if (
            not identifier.isdigit()
            or int(identifier) <= 0
        ):
            raise WooCommerceCommerceReadError(
                "identifier_invalid"
            )

        return identifier

    def _decode_page_request(
        self,
        value: PageRequest,
    ) -> tuple[int, int]:
        if not isinstance(
            value,
            Mapping,
        ):
            raise WooCommerceCommerceReadError(
                "page_request_invalid"
            )

        if set(value) != {
            "cursor",
            "limit",
        }:
            raise WooCommerceCommerceReadError(
                "page_request_invalid"
            )

        limit = value[
            "limit"
        ]

        if (
            isinstance(
                limit,
                bool,
            )
            or not isinstance(
                limit,
                int,
            )
            or limit <= 0
            or limit > 100
        ):
            raise WooCommerceCommerceReadError(
                "page_request_invalid"
            )

        try:
            page_number = (
                self
                ._cursor_page_decoder(
                    value[
                        "cursor"
                    ]
                )
            )
        except Exception:
            raise WooCommerceCommerceReadError(
                "cursor_invalid"
            ) from None

        if (
            isinstance(
                page_number,
                bool,
            )
            or not isinstance(
                page_number,
                int,
            )
            or page_number <= 0
        ):
            raise WooCommerceCommerceReadError(
                "cursor_invalid"
            )

        return (
            page_number,
            limit,
        )


    async def _authorize_probe_for_test(
        self,
    ) -> None:
        self._authorize_external_read(
            path="/wp-json/wc/v3/customers",
            query={
                "context": "view",
            },
        )

    async def get_product(self, *, context: ReadContext, product_id: str) -> ProductSnapshot | None:
        _ = context

        identifier = self._validate_identifier(
            product_id
        )

        path = (
            "/wp-json/wc/v3/products/"
            + identifier
        )

        query = {
            "context": "view",
        }

        self._authorize_external_read(
            path=path,
            query=query,
        )

        try:
            payload = await asyncio.to_thread(
                self._catalog.get_product,
                identifier,
            )
        except Exception:
            raise WooCommerceCommerceReadError(
                "transport_error"
            ) from None

        if payload is None:
            return None

        try:
            return self._product_normalizer(
                payload
            )
        except Exception:
            raise WooCommerceCommerceReadError(
                "normalization_error"
            ) from None

    async def list_products(self, *, context: ReadContext, page: PageRequest) -> ProductSnapshotPage:
        _ = context

        (
            page_number,
            page_size,
        ) = self._decode_page_request(
            page
        )

        path = (
            "/wp-json/wc/v3/products"
        )

        query = {
            "context": "view",
            "status": "publish",
            "page": str(
                page_number
            ),
            "per_page": str(
                page_size
            ),
        }

        self._authorize_external_read(
            path=path,
            query=query,
        )

        try:
            result = await asyncio.to_thread(
                self._catalog.list_products,
                page_number,
                page_size,
            )
        except Exception:
            raise WooCommerceCommerceReadError(
                "transport_error"
            ) from None

        if (
            not isinstance(
                result,
                tuple,
            )
            or len(result) != 2
        ):
            raise WooCommerceCommerceReadError(
                "vendor_page_invalid"
            )

        items, total = result

        if (
            not isinstance(
                items,
                list,
            )
            or isinstance(
                total,
                bool,
            )
            or not isinstance(
                total,
                int,
            )
            or total < 0
        ):
            raise WooCommerceCommerceReadError(
                "vendor_page_invalid"
            )

        try:
            return (
                self
                ._product_page_normalizer(
                    items,
                    total,
                    page,
                    page_number,
                )
            )
        except Exception:
            raise WooCommerceCommerceReadError(
                "normalization_error"
            ) from None

    async def get_order_summary(self, *, context: ReadContext, order_id: str) -> OrderSummary | None:
        _ = context

        identifier = self._validate_identifier(
            order_id
        )

        path = (
            "/wp-json/wc/v3/orders/"
            + identifier
        )

        query = {
            "context": "view",
        }

        self._authorize_external_read(
            path=path,
            query=query,
        )

        try:
            payload = await asyncio.to_thread(
                self._order_reader.get_order_summary,
                identifier,
            )
        except Exception:
            raise WooCommerceCommerceReadError(
                "transport_error"
            ) from None

        if payload is None:
            return None

        try:
            return (
                self
                ._order_summary_normalizer(
                    payload
                )
            )
        except Exception:
            raise WooCommerceCommerceReadError(
                "normalization_error"
            ) from None
