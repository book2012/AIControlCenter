from __future__ import annotations

import ast
import json
from pathlib import Path

from core.shopping.adapters.cms_contract import (
    EXPECTED_RETURN_CONTRACTS as CMS_RETURNS,
    cms_contract_manifest,
)
from core.shopping.adapters.commerce_contract import (
    EXPECTED_RETURN_CONTRACTS as COMMERCE_RETURNS,
    commerce_contract_manifest,
)


COMMERCE_SOURCE = Path(
    "core/shopping/adapters/commerce_contract.py"
)

CMS_SOURCE = Path(
    "core/shopping/adapters/cms_contract.py"
)


def test_manifests_have_distinct_authoritative_ports():
    commerce = commerce_contract_manifest()
    cms = cms_contract_manifest()

    assert commerce["authoritative_port"] == "CommerceReadPort"
    assert cms["authoritative_port"] == "CmsReadPort"
    assert (
        commerce["authoritative_port"]
        != cms["authoritative_port"]
    )


def test_capability_sets_are_exact_and_disjoint():
    commerce = commerce_contract_manifest()
    cms = cms_contract_manifest()

    commerce_ids = {
        item["capability_id"]
        for item in commerce["methods"].values()
    }

    cms_ids = {
        item["capability_id"]
        for item in cms["methods"].values()
    }

    assert commerce_ids == {
        "shopping.order.summary.get",
        "shopping.product.get",
        "shopping.product.list",
    }

    assert cms_ids == {
        "shopping.content.get",
        "shopping.content.list",
    }

    assert commerce_ids.isdisjoint(
        cms_ids
    )


def test_all_adapter_contract_capabilities_are_read_only_identifiers():
    manifests = (
        commerce_contract_manifest(),
        cms_contract_manifest(),
    )

    forbidden_tokens = (
        ".append",
        ".create",
        ".delete",
        ".persist",
        ".register",
        ".update",
        ".write",
    )

    for manifest in manifests:
        assert (
            manifest[
                "write_methods_allowed"
            ]
            is False
        )

        for item in manifest[
            "methods"
        ].values():
            capability_id = item[
                "capability_id"
            ]

            assert capability_id.startswith(
                "shopping."
            )

            assert not any(
                token
                in capability_id
                for token
                in forbidden_tokens
            )


def test_return_contract_sets_are_exact_and_isolated():
    assert dict(
        COMMERCE_RETURNS
    ) == {
        "get_order_summary": "OrderSummary",
        "get_product": "ProductSnapshot",
        "list_products": "ProductSnapshotPage",
    }

    assert dict(
        CMS_RETURNS
    ) == {
        "get_content": "ContentSnapshot",
        "list_content": "ContentSnapshotPage",
    }

    assert set(
        COMMERCE_RETURNS
    ).isdisjoint(
        set(
            CMS_RETURNS
        )
    )


def test_contract_modules_have_no_vendor_or_network_imports():
    forbidden_roots = {
        "aiohttp",
        "httpx",
        "os",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }

    vendor_tokens = {
        "magento",
        "shopify",
        "woocommerce",
        "wordpress",
    }

    for path in (
        COMMERCE_SOURCE,
        CMS_SOURCE,
    ):
        tree = ast.parse(
            path.read_text(
                encoding="utf-8"
            )
        )

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
                        item.name
                    )

            elif (
                isinstance(
                    node,
                    ast.ImportFrom,
                )
                and node.module
            ):
                imported.add(
                    node.module
                )

        roots = {
            module.split(
                "."
            )[0]
            for module in imported
        }

        assert not (
            roots
            & forbidden_roots
        )

        lowered = {
            module.lower()
            for module in imported
        }

        assert not any(
            token
            in module
            for token in vendor_tokens
            for module in lowered
        )


def test_contract_modules_do_not_depend_on_application_layer():
    for path in (
        COMMERCE_SOURCE,
        CMS_SOURCE,
    ):
        tree = ast.parse(
            path.read_text(
                encoding="utf-8"
            )
        )

        modules = []

        for node in ast.walk(
            tree
        ):
            if (
                isinstance(
                    node,
                    ast.ImportFrom,
                )
                and node.module
            ):
                modules.append(
                    node.module
                )

            elif isinstance(
                node,
                ast.Import,
            ):
                modules.extend(
                    item.name
                    for item in node.names
                )

        assert not any(
            module.startswith(
                "core.shopping.application"
            )
            for module in modules
        )


def test_manifests_disable_live_vendor_connection_and_policy_ownership():
    for manifest in (
        commerce_contract_manifest(),
        cms_contract_manifest(),
    ):
        assert (
            manifest[
                "live_vendor_connection"
            ]
            is False
        )

        assert (
            manifest[
                "policy_evaluation_in_adapter"
            ]
            is False
        )

        assert (
            manifest[
                "business_logic_in_adapter"
            ]
            is False
        )

        assert (
            manifest[
                "vendor_dto_escape_allowed"
            ]
            is False
        )


def test_combined_manifest_is_json_serializable():
    combined = {
        "commerce": (
            commerce_contract_manifest()
        ),
        "cms": (
            cms_contract_manifest()
        ),
    }

    rendered = json.dumps(
        combined,
        sort_keys=True,
    )

    assert rendered
