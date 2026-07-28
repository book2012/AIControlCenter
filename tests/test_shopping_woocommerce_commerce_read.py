from __future__ import annotations

import asyncio

import pytest

from core.shopping.adapters.commerce_contract import (
    validate_commerce_adapter_class,
)
from core.shopping.adapters.woocommerce_commerce_read import (
    WooCommerceCommerceReadAdapter,
    WooCommerceCommerceReadError,
)


class FakeCatalog:
    def __init__(
        self,
        *,
        product=None,
        items=None,
        total=0,
        error=None,
    ):
        self.product = product
        self.items = (
            items
            if items is not None
            else []
        )
        self.total = total
        self.error = error
        self.calls = []

    def get_product(
        self,
        product_id,
    ):
        self.calls.append(
            (
                "get_product",
                product_id,
            )
        )

        if self.error is not None:
            raise self.error

        return self.product

    def list_products(
        self,
        page,
        page_size,
    ):
        self.calls.append(
            (
                "list_products",
                page,
                page_size,
            )
        )

        if self.error is not None:
            raise self.error

        return (
            self.items,
            self.total,
        )


class FakeOrderReader:
    def __init__(
        self,
        payload=None,
        error=None,
    ):
        self.payload = payload
        self.error = error
        self.calls = []

    def get_order_summary(
        self,
        order_id,
    ):
        self.calls.append(
            order_id
        )

        if self.error is not None:
            raise self.error

        return self.payload


def decode_cursor(value):
    mapping = {
        "page-1": 1,
        "page-2": 2,
        "page-3": 3,
    }

    return mapping[
        value
    ]


def normalize_product(value):
    return {
        "canonical": "product",
        "vendor_id": str(
            value[
                "id"
            ]
        ),
    }


def normalize_page(
    items,
    total,
    page_request,
    page_number,
):
    return {
        "canonical": "page",
        "item_count": len(
            items
        ),
        "total": total,
        "cursor": page_request[
            "cursor"
        ],
        "limit": page_request[
            "limit"
        ],
        "page_number": page_number,
    }


def normalize_order(value):
    return {
        "canonical": "order",
        "vendor_id": str(
            value[
                "id"
            ]
        ),
    }


def make_adapter(
    *,
    catalog=None,
    order_reader=None,
):
    return WooCommerceCommerceReadAdapter(
        catalog=(
            catalog
            or FakeCatalog()
        ),
        order_reader=(
            order_reader
            or FakeOrderReader()
        ),
        cursor_page_decoder=decode_cursor,
        product_normalizer=normalize_product,
        product_page_normalizer=normalize_page,
        order_summary_normalizer=normalize_order,
    )


def test_contract_validator_accepts_canonical_wrapper():
    validate_commerce_adapter_class(
        WooCommerceCommerceReadAdapter
    )


def test_product_read_reuses_legacy_catalog():
    catalog = FakeCatalog(
        product={
            "id": 42,
        }
    )

    value = asyncio.run(
        make_adapter(
            catalog=catalog
        ).get_product(
            context={},
            product_id="42",
        )
    )

    assert value == {
        "canonical": "product",
        "vendor_id": "42",
    }

    assert catalog.calls == [
        (
            "get_product",
            "42",
        )
    ]


def test_page_request_translates_to_legacy_page_and_page_size():
    catalog = FakeCatalog(
        items=[
            {
                "id": 1,
            },
            {
                "id": 2,
            },
        ],
        total=12,
    )

    page_request = {
        "cursor": "page-2",
        "limit": 5,
    }

    value = asyncio.run(
        make_adapter(
            catalog=catalog
        ).list_products(
            context={},
            page=page_request,
        )
    )

    assert catalog.calls == [
        (
            "list_products",
            2,
            5,
        )
    ]

    assert value[
        "canonical"
    ] == "page"

    assert value[
        "page_number"
    ] == 2

    assert value[
        "limit"
    ] == 5

    assert value[
        "total"
    ] == 12


def test_order_read_uses_separate_order_reader_boundary():
    reader = FakeOrderReader(
        payload={
            "id": 7,
        }
    )

    value = asyncio.run(
        make_adapter(
            order_reader=reader
        ).get_order_summary(
            context={},
            order_id="7",
        )
    )

    assert value == {
        "canonical": "order",
        "vendor_id": "7",
    }

    assert reader.calls == [
        "7",
    ]


def test_policy_denial_happens_before_vendor_transport():
    catalog = FakeCatalog()

    instance = make_adapter(
        catalog=catalog
    )

    with pytest.raises(
        WooCommerceCommerceReadError
    ) as captured:
        asyncio.run(
            instance._authorize_probe_for_test()
        )

    assert captured.value.reason_code == (
        "external_read_policy_denied"
    )

    assert catalog.calls == []


def test_malformed_page_request_never_reaches_catalog():
    catalog = FakeCatalog()

    with pytest.raises(
        WooCommerceCommerceReadError
    ) as captured:
        asyncio.run(
            make_adapter(
                catalog=catalog
            ).list_products(
                context={},
                page={
                    "cursor": "page-2",
                    "limit": 5,
                    "unexpected": True,
                },
            )
        )

    assert captured.value.reason_code == (
        "page_request_invalid"
    )

    assert catalog.calls == []


def test_transport_error_is_sanitized():
    catalog = FakeCatalog(
        error=RuntimeError(
            "RAW_VENDOR_SECRET_MUST_NOT_ESCAPE"
        )
    )

    with pytest.raises(
        WooCommerceCommerceReadError
    ) as captured:
        asyncio.run(
            make_adapter(
                catalog=catalog
            ).get_product(
                context={},
                product_id="42",
            )
        )

    assert captured.value.reason_code == (
        "transport_error"
    )

    assert (
        "RAW_VENDOR_SECRET_MUST_NOT_ESCAPE"
        not in str(
            captured.value
        )
    )
