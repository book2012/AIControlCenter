from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from core.shopping.adapters.commerce_contract import (
    CommerceAdapterContractError,
    EXPECTED_RETURN_CONTRACTS,
    commerce_contract_manifest,
    validate_commerce_adapter_class,
    validate_commerce_adapter_instance,
)
from core.shopping.contracts.provisional import (
    OrderSummary,
    ProductSnapshot,
    ProductSnapshotPage,
)


class GoodCommerceAdapter:
    async def get_order_summary(self, *, context, order_id) -> OrderSummary:
        return {}

    async def get_product(self, *, context, product_id) -> ProductSnapshot:
        return {}

    async def list_products(self, *, context, page) -> ProductSnapshotPage:
        return {}



def test_manifest_has_exact_capability_bindings():
    manifest = commerce_contract_manifest()

    assert manifest["methods"] == {
        "get_order_summary": {
            "capability_id": (
                "shopping.order.summary.get"
            ),
            "return_contract": (
                "OrderSummary"
            ),
        },
        "get_product": {
            "capability_id": (
                "shopping.product.get"
            ),
            "return_contract": (
                "ProductSnapshot"
            ),
        },
        "list_products": {
            "capability_id": (
                "shopping.product.list"
            ),
            "return_contract": (
                "ProductSnapshotPage"
            ),
        },
    }


def test_manifest_is_json_serializable_and_read_only():
    manifest = commerce_contract_manifest()

    rendered = json.dumps(
        manifest,
        sort_keys=True,
    )

    assert rendered
    assert manifest["read_only"] is True
    assert (
        manifest[
            "write_methods_allowed"
        ]
        is False
    )
    assert (
        manifest[
            "vendor_dto_escape_allowed"
        ]
        is False
    )


def test_valid_adapter_class_passes():
    assert (
        validate_commerce_adapter_class(
            GoodCommerceAdapter
        )
        is GoodCommerceAdapter
    )


def test_valid_adapter_instance_passes():
    adapter = GoodCommerceAdapter()

    assert (
        validate_commerce_adapter_instance(
            adapter
        )
        is adapter
    )


def test_missing_required_method_is_rejected():
    class MissingAdapter(
        GoodCommerceAdapter
    ):
        get_product = None

    with pytest.raises(
        CommerceAdapterContractError
    ):
        validate_commerce_adapter_class(
            MissingAdapter
        )


def test_sync_required_method_is_rejected():
    class SyncAdapter(
        GoodCommerceAdapter
    ):
        def get_product(
            self,
            **kwargs,
        ) -> ProductSnapshot:
            return {}

    with pytest.raises(
        CommerceAdapterContractError
    ):
        validate_commerce_adapter_class(
            SyncAdapter
        )


def test_wrong_signature_is_rejected():
    class WrongSignatureAdapter(
        GoodCommerceAdapter
    ):
        async def get_product(
            self,
            unexpected,
        ) -> ProductSnapshot:
            return {}

    with pytest.raises(
        CommerceAdapterContractError
    ):
        validate_commerce_adapter_class(
            WrongSignatureAdapter
        )


def test_write_like_public_method_is_rejected():
    class WriteAdapter(
        GoodCommerceAdapter
    ):
        async def update_product(
            self,
        ):
            return None

    with pytest.raises(
        CommerceAdapterContractError
    ):
        validate_commerce_adapter_class(
            WriteAdapter
        )


def test_return_contract_mapping_is_immutable():
    with pytest.raises(
        TypeError
    ):
        EXPECTED_RETURN_CONTRACTS[
            "get_product"
        ] = "VendorProduct"


def test_contract_module_has_no_network_or_environment_imports():
    path = Path(
        "core/shopping/adapters/commerce_contract.py"
    )

    tree = ast.parse(
        path.read_text(
            encoding="utf-8"
        )
    )

    forbidden = {
        "aiohttp",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }

    imported = set()

    for node in ast.walk(
        tree
    ):
        if isinstance(
            node,
            ast.Import,
        ):
            for item in node.names:
                imported.add(
                    item.name.split(
                        "."
                    )[0]
                )

        elif (
            isinstance(
                node,
                ast.ImportFrom,
            )
            and node.module
        ):
            imported.add(
                node.module.split(
                    "."
                )[0]
            )

    assert not (
        imported
        & forbidden
    )
