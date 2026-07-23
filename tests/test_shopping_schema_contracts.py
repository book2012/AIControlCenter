from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from core.shopping.contracts.schema_registry import (
    ShoppingSchemaRegistryError,
    load_schema_registry,
)
from core.shopping.contracts.validation import (
    ShoppingContractValidationError,
    validate_contract_payload,
)


DRAFT_URI = (
    "https://json-schema.org/draft/2020-12/schema"
)

TIMESTAMP = (
    "2026-07-23T00:00:00Z"
)


def _payloads():
    context = {
        "actor_id": "admin-1",
        "correlation_id": "correlation-1",
        "locale": "ko-KR",
        "requested_at": TIMESTAMP,
        "source": "test",
    }

    product = {
        "description": "Canonical product",
        "image_urls": [
            "https://example.com/product.jpg",
        ],
        "in_stock": True,
        "inventory_quantity": 5,
        "name": "Product",
        "price": {
            "amount_minor": 39000,
            "currency": "KRW",
        },
        "product_id": "product-1",
        "sku": "SKU-1",
        "updated_at": TIMESTAMP,
        "url": "https://example.com/product",
    }

    content = {
        "body": "Body",
        "content_id": "content-1",
        "content_type": "page",
        "published": True,
        "published_at": TIMESTAMP,
        "slug": "home-page",
        "title": "Home",
        "updated_at": TIMESTAMP,
        "url": "https://example.com/home",
    }

    order = {
        "created_at": TIMESTAMP,
        "customer_id": "customer-1",
        "item_count": 2,
        "order_id": "order-1",
        "status": "processing",
        "total": {
            "amount_minor": 78000,
            "currency": "KRW",
        },
        "updated_at": TIMESTAMP,
    }

    health = {
        "adapter": "woocommerce",
        "checked_at": TIMESTAMP,
        "latency_ms": 20,
        "message": None,
        "status": "healthy",
    }

    decision = {
        "allowed": True,
        "capability": "shopping.product.read",
        "correlation_id": "correlation-1",
        "decision_id": "decision-1",
        "evaluated_at": TIMESTAMP,
        "reason_code": "shopping.policy.allowed",
        "reason_message": None,
    }

    audit = {
        "action": "shopping.product.read",
        "actor_id": "admin-1",
        "correlation_id": "correlation-1",
        "event_id": "event-1",
        "message": None,
        "occurred_at": TIMESTAMP,
        "outcome": "observed",
        "resource_id": "product-1",
        "resource_type": "product",
    }

    discovery = {
        "contract_name": "ProductSnapshot",
        "discovered_at": TIMESTAMP,
        "draft": DRAFT_URI,
        "schema_id": (
            "urn:aicontrolcenter:shopping:"
            "contract:v1:product-snapshot"
        ),
        "schema_version": "1.0.0",
    }

    snapshot = {
        "captured_at": TIMESTAMP,
        "contract_name": "ProductSnapshot",
        "payload": product,
        "schema_id": (
            "urn:aicontrolcenter:shopping:"
            "contract:v1:product-snapshot"
        ),
        "schema_version": "1.0.0",
        "snapshot_id": "snapshot-1",
        "source": "test",
    }

    return {
        "AdapterHealth": health,
        "AuditEvent": audit,
        "AuditEventPage": {
            "has_more": False,
            "items": [
                audit,
            ],
            "next_cursor": None,
        },
        "ContentSnapshot": content,
        "ContentSnapshotPage": {
            "has_more": False,
            "items": [
                content,
            ],
            "next_cursor": None,
        },
        "OrderSummary": order,
        "PageRequest": {
            "cursor": None,
            "limit": 25,
        },
        "PolicyDecision": decision,
        "ProductSnapshot": product,
        "ProductSnapshotPage": {
            "has_more": False,
            "items": [
                product,
            ],
            "next_cursor": None,
        },
        "ReadContext": context,
        "ReadPolicyRequest": {
            "action": "read",
            "capability": "shopping.product.read",
            "context": context,
            "requested_fields": [
                "name",
                "price",
            ],
            "resource_id": "product-1",
            "resource_type": "product",
        },
        "SchemaDiscoveryResult": discovery,
        "SnapshotEnvelope": snapshot,
        "SnapshotEnvelopePage": {
            "has_more": False,
            "items": [
                snapshot,
            ],
            "next_cursor": None,
        },
    }


def test_registry_scope_and_meta_schema():
    registry = load_schema_registry()

    assert len(
        registry.contracts
    ) == 15

    assert len(
        registry.schemas_by_id
    ) == 17

    assert (
        registry.manifest[
            "network_resolution"
        ]
        is False
    )

    assert set(
        registry.contracts
    ) == set(
        _payloads()
    )

    for schema in (
        registry.schemas_by_id.values()
    ):
        Draft202012Validator.check_schema(
            dict(
                schema
            )
        )


def test_all_contracts_accept_canonical_payloads():
    registry = load_schema_registry()

    for (
        contract_name,
        payload,
    ) in _payloads().items():
        validate_contract_payload(
            registry=registry,
            contract_name=contract_name,
            payload=payload,
        )


def test_strict_required_format_and_numeric_rules():
    registry = load_schema_registry()

    payloads = _payloads()

    invalid_payloads = [
        (
            "PageRequest",
            {
                "cursor": None,
                "limit": 25,
                "unexpected": True,
            },
        ),
        (
            "PageRequest",
            {
                "cursor": None,
            },
        ),
        (
            "ProductSnapshot",
            {
                **payloads[
                    "ProductSnapshot"
                ],
                "updated_at": (
                    "2026-07-23T09:00:00+09:00"
                ),
            },
        ),
        (
            "ProductSnapshot",
            {
                **payloads[
                    "ProductSnapshot"
                ],
                "price": {
                    "amount_minor": 39.5,
                    "currency": "KRW",
                },
            },
        ),
    ]

    for (
        contract_name,
        payload,
    ) in invalid_payloads:
        with pytest.raises(
            ShoppingContractValidationError
        ):
            validate_contract_payload(
                registry=registry,
                contract_name=contract_name,
                payload=payload,
            )


def test_non_json_and_unknown_contract_are_denied():
    registry = load_schema_registry()

    product = {
        **_payloads()[
            "ProductSnapshot"
        ],
        "description": bytes(
            [
                115,
                117,
                112,
                101,
                114,
                45,
                115,
                101,
                99,
                114,
                101,
                116,
            ]
        ),
    }

    with pytest.raises(
        ShoppingContractValidationError
    ) as error_info:
        validate_contract_payload(
            registry=registry,
            contract_name="ProductSnapshot",
            payload=product,
        )

    assert (
        "super-secret"
        not in str(
            error_info.value
        )
    )

    with pytest.raises(
        ShoppingContractValidationError
    ):
        validate_contract_payload(
            registry=registry,
            contract_name="UnknownContract",
            payload={},
        )


def test_snapshot_payload_discriminator_is_enforced():
    registry = load_schema_registry()

    payloads = _payloads()

    invalid_snapshot = {
        **payloads[
            "SnapshotEnvelope"
        ],
        "payload": payloads[
            "ContentSnapshot"
        ],
    }

    with pytest.raises(
        ShoppingContractValidationError
    ):
        validate_contract_payload(
            registry=registry,
            contract_name="SnapshotEnvelope",
            payload=invalid_snapshot,
        )


def test_remote_schema_reference_is_denied(
    tmp_path: Path,
):
    registry = load_schema_registry()

    copied_root = (
        tmp_path
        / "v1"
    )

    shutil.copytree(
        registry.schema_root,
        copied_root,
    )

    product_path = (
        copied_root
        / "product-snapshot.schema.json"
    )

    product_schema = json.loads(
        product_path.read_text(
            encoding="utf-8"
        )
    )

    product_schema[
        "properties"
    ][
        "price"
    ][
        "$ref"
    ] = (
        "https://example.invalid/"
        "remote.schema.json"
    )

    product_path.write_text(
        json.dumps(
            product_schema,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ShoppingSchemaRegistryError
    ):
        load_schema_registry(
            schema_root=copied_root
        )
