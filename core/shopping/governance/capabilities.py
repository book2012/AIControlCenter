from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Iterator, Mapping


_CAPABILITY_PATTERN = re.compile(
    r"^shopping(?:\.[a-z][a-z0-9]*){2,}$"
)

_RESOURCE_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*$"
)

_METHOD_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*$"
)

_PORT_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*$"
)

_FORBIDDEN_VENDOR_SEGMENTS = frozenset(
    {
        "magento",
        "shopify",
        "woocommerce",
        "wordpress",
    }
)


class CapabilityRegistryError(ValueError):
    pass


class OperationClass(str, Enum):
    READ = "READ"
    WRITE = "WRITE"


@dataclass(frozen=True, slots=True)
class CapabilityDefinition:
    capability_id: str
    operation_class: OperationClass
    resource_type: str
    port: str
    method: str

    def __post_init__(
        self,
    ) -> None:
        if (
            _CAPABILITY_PATTERN.fullmatch(
                self.capability_id
            )
            is None
        ):
            raise CapabilityRegistryError(
                "Invalid capability identifier."
            )

        segments = set(
            self.capability_id.split(
                "."
            )
        )

        if (
            segments
            & _FORBIDDEN_VENDOR_SEGMENTS
        ):
            raise CapabilityRegistryError(
                "Vendor-specific capability identifiers are forbidden."
            )

        if (
            _RESOURCE_PATTERN.fullmatch(
                self.resource_type
            )
            is None
        ):
            raise CapabilityRegistryError(
                "Invalid capability resource type."
            )

        if (
            _PORT_PATTERN.fullmatch(
                self.port
            )
            is None
        ):
            raise CapabilityRegistryError(
                "Invalid capability port binding."
            )

        if (
            _METHOD_PATTERN.fullmatch(
                self.method
            )
            is None
        ):
            raise CapabilityRegistryError(
                "Invalid capability method binding."
            )


class CapabilityRegistry:
    __slots__ = (
        "_definitions",
    )

    def __init__(
        self,
        definitions: Iterable[
            CapabilityDefinition
        ],
    ) -> None:
        by_id: dict[
            str,
            CapabilityDefinition,
        ] = {}

        for definition in definitions:
            capability_id = (
                definition.capability_id
            )

            if capability_id in by_id:
                raise CapabilityRegistryError(
                    "Duplicate capability identifier."
                )

            by_id[
                capability_id
            ] = definition

        self._definitions = (
            MappingProxyType(
                by_id
            )
        )

    @property
    def definitions(
        self,
    ) -> Mapping[
        str,
        CapabilityDefinition,
    ]:
        return self._definitions

    def __len__(
        self,
    ) -> int:
        return len(
            self._definitions
        )

    def __iter__(
        self,
    ) -> Iterator[str]:
        return iter(
            self._definitions
        )

    def get(
        self,
        capability_id: str,
    ) -> CapabilityDefinition | None:
        return self._definitions.get(
            capability_id
        )

    def is_registered(
        self,
        capability_id: str,
    ) -> bool:
        return (
            capability_id
            in self._definitions
        )

    def is_executable_read(
        self,
        capability_id: str,
    ) -> bool:
        definition = self.get(
            capability_id
        )

        return (
            definition
            is not None
            and definition.operation_class
            is OperationClass.READ
        )


_READ_CAPABILITY_DEFINITIONS = (
    CapabilityDefinition(
        capability_id="shopping.product.get",
        operation_class=OperationClass.READ,
        resource_type="product",
        port="CommerceReadPort",
        method="get_product",
    ),
    CapabilityDefinition(
        capability_id="shopping.product.list",
        operation_class=OperationClass.READ,
        resource_type="product",
        port="CommerceReadPort",
        method="list_products",
    ),
    CapabilityDefinition(
        capability_id="shopping.order.summary.get",
        operation_class=OperationClass.READ,
        resource_type="order",
        port="CommerceReadPort",
        method="get_order_summary",
    ),
    CapabilityDefinition(
        capability_id="shopping.content.get",
        operation_class=OperationClass.READ,
        resource_type="content",
        port="CmsReadPort",
        method="get_content",
    ),
    CapabilityDefinition(
        capability_id="shopping.content.list",
        operation_class=OperationClass.READ,
        resource_type="content",
        port="CmsReadPort",
        method="list_content",
    ),
    CapabilityDefinition(
        capability_id="shopping.adapter.health.get",
        operation_class=OperationClass.READ,
        resource_type="adapter_health",
        port="AdapterHealthPort",
        method="get_health",
    ),
    CapabilityDefinition(
        capability_id="shopping.schema.discover",
        operation_class=OperationClass.READ,
        resource_type="schema",
        port="SchemaDiscoveryPort",
        method="discover_schema",
    ),
    CapabilityDefinition(
        capability_id="shopping.snapshot.get",
        operation_class=OperationClass.READ,
        resource_type="snapshot",
        port="SnapshotRepositoryPort",
        method="get_latest_snapshot",
    ),
    CapabilityDefinition(
        capability_id="shopping.snapshot.list",
        operation_class=OperationClass.READ,
        resource_type="snapshot",
        port="SnapshotRepositoryPort",
        method="list_snapshots",
    ),
    CapabilityDefinition(
        capability_id="shopping.audit.get",
        operation_class=OperationClass.READ,
        resource_type="audit",
        port="AuditPort",
        method="get_event",
    ),
    CapabilityDefinition(
        capability_id="shopping.audit.list",
        operation_class=OperationClass.READ,
        resource_type="audit",
        port="AuditPort",
        method="list_events",
    ),
)


READ_CAPABILITY_IDS = tuple(
    definition.capability_id
    for definition
    in _READ_CAPABILITY_DEFINITIONS
)


RESERVED_WRITE_CAPABILITY_IDS = (
    "shopping.product.create",
    "shopping.product.update",
    "shopping.product.delete",
    "shopping.price.update",
    "shopping.order.update",
    "shopping.content.write",
    "shopping.webhook.register",
    "shopping.snapshot.persist",
    "shopping.audit.append",
)


DEFAULT_CAPABILITY_REGISTRY = (
    CapabilityRegistry(
        _READ_CAPABILITY_DEFINITIONS
    )
)


__all__ = (
    "CapabilityDefinition",
    "CapabilityRegistry",
    "CapabilityRegistryError",
    "DEFAULT_CAPABILITY_REGISTRY",
    "OperationClass",
    "READ_CAPABILITY_IDS",
    "RESERVED_WRITE_CAPABILITY_IDS",
)
