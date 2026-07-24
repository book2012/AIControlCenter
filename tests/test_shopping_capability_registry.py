from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.shopping.governance.capabilities import (
    CapabilityDefinition,
    CapabilityRegistry,
    CapabilityRegistryError,
    DEFAULT_CAPABILITY_REGISTRY,
    OperationClass,
    READ_CAPABILITY_IDS,
    RESERVED_WRITE_CAPABILITY_IDS,
)


EXPECTED = {
    "shopping.product.get": (
        "product",
        "CommerceReadPort",
        "get_product",
    ),
    "shopping.product.list": (
        "product",
        "CommerceReadPort",
        "list_products",
    ),
    "shopping.order.summary.get": (
        "order",
        "CommerceReadPort",
        "get_order_summary",
    ),
    "shopping.content.get": (
        "content",
        "CmsReadPort",
        "get_content",
    ),
    "shopping.content.list": (
        "content",
        "CmsReadPort",
        "list_content",
    ),
    "shopping.adapter.health.get": (
        "adapter_health",
        "AdapterHealthPort",
        "get_health",
    ),
    "shopping.schema.discover": (
        "schema",
        "SchemaDiscoveryPort",
        "discover_schema",
    ),
    "shopping.snapshot.get": (
        "snapshot",
        "SnapshotRepositoryPort",
        "get_latest_snapshot",
    ),
    "shopping.snapshot.list": (
        "snapshot",
        "SnapshotRepositoryPort",
        "list_snapshots",
    ),
    "shopping.audit.get": (
        "audit",
        "AuditPort",
        "get_event",
    ),
    "shopping.audit.list": (
        "audit",
        "AuditPort",
        "list_events",
    ),
}


def test_default_registry_contains_exact_read_capabilities():
    assert len(
        DEFAULT_CAPABILITY_REGISTRY
    ) == 11

    assert set(
        DEFAULT_CAPABILITY_REGISTRY
    ) == set(
        EXPECTED
    )

    assert set(
        READ_CAPABILITY_IDS
    ) == set(
        EXPECTED
    )


def test_default_registry_bindings_match_decision():
    for (
        capability_id,
        expected,
    ) in EXPECTED.items():
        definition = (
            DEFAULT_CAPABILITY_REGISTRY.get(
                capability_id
            )
        )

        assert definition is not None

        assert (
            definition.operation_class
            is OperationClass.READ
        )

        assert (
            definition.resource_type,
            definition.port,
            definition.method,
        ) == expected


def test_reserved_write_capabilities_are_not_executable():
    assert len(
        RESERVED_WRITE_CAPABILITY_IDS
    ) == 9

    for capability_id in (
        RESERVED_WRITE_CAPABILITY_IDS
    ):
        assert (
            DEFAULT_CAPABILITY_REGISTRY.get(
                capability_id
            )
            is None
        )

        assert not (
            DEFAULT_CAPABILITY_REGISTRY
            .is_executable_read(
                capability_id
            )
        )


def test_unknown_capability_fails_closed():
    capability_id = (
        "shopping.unknown.operation"
    )

    assert (
        DEFAULT_CAPABILITY_REGISTRY.get(
            capability_id
        )
        is None
    )

    assert not (
        DEFAULT_CAPABILITY_REGISTRY
        .is_registered(
            capability_id
        )
    )

    assert not (
        DEFAULT_CAPABILITY_REGISTRY
        .is_executable_read(
            capability_id
        )
    )


def test_registry_mapping_is_immutable():
    with pytest.raises(
        TypeError
    ):
        DEFAULT_CAPABILITY_REGISTRY.definitions[
            "shopping.product.get"
        ] = DEFAULT_CAPABILITY_REGISTRY.definitions[
            "shopping.product.get"
        ]


def test_capability_definition_is_frozen():
    definition = (
        DEFAULT_CAPABILITY_REGISTRY.get(
            "shopping.product.get"
        )
    )

    assert definition is not None

    with pytest.raises(
        FrozenInstanceError
    ):
        definition.resource_type = "changed"


def test_duplicate_capability_identifier_is_rejected():
    definition = CapabilityDefinition(
        capability_id="shopping.test.get",
        operation_class=OperationClass.READ,
        resource_type="test",
        port="TestReadPort",
        method="get_test",
    )

    with pytest.raises(
        CapabilityRegistryError
    ):
        CapabilityRegistry(
            (
                definition,
                definition,
            )
        )


def test_invalid_and_vendor_specific_identifiers_are_rejected():
    invalid_ids = (
        "Shopping.Product.Get",
        "shopping",
        "shopping.product",
        "shopping.product.get!",
        "shopping.woocommerce.product.get",
        "shopping.wordpress.content.get",
    )

    for capability_id in invalid_ids:
        with pytest.raises(
            CapabilityRegistryError
        ):
            CapabilityDefinition(
                capability_id=capability_id,
                operation_class=OperationClass.READ,
                resource_type="test",
                port="TestReadPort",
                method="get_test",
            )
