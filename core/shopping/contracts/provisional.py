"""Provisional JSON-first Shopping contracts.

SPF-004 will freeze canonical JSON Schema v1.
"""

from __future__ import annotations

from typing import Mapping, Sequence, TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = (
    JsonScalar
    | Mapping[str, object]
    | Sequence[object]
)
JsonObject: TypeAlias = Mapping[str, JsonValue]

AdapterHealth: TypeAlias = JsonObject
AuditEvent: TypeAlias = JsonObject
AuditEventPage: TypeAlias = JsonObject
ContentSnapshot: TypeAlias = JsonObject
ContentSnapshotPage: TypeAlias = JsonObject
OrderSummary: TypeAlias = JsonObject
PageRequest: TypeAlias = JsonObject
PolicyDecision: TypeAlias = JsonObject
ProductSnapshot: TypeAlias = JsonObject
ProductSnapshotPage: TypeAlias = JsonObject
ReadContext: TypeAlias = JsonObject
ReadPolicyRequest: TypeAlias = JsonObject
SchemaDiscoveryResult: TypeAlias = JsonObject
SnapshotEnvelope: TypeAlias = JsonObject
SnapshotEnvelopePage: TypeAlias = JsonObject

__all__ = (
    'JsonObject',
    'JsonScalar',
    'JsonValue',
    'AdapterHealth',
    'AuditEvent',
    'AuditEventPage',
    'ContentSnapshot',
    'ContentSnapshotPage',
    'OrderSummary',
    'PageRequest',
    'PolicyDecision',
    'ProductSnapshot',
    'ProductSnapshotPage',
    'ReadContext',
    'ReadPolicyRequest',
    'SchemaDiscoveryResult',
    'SnapshotEnvelope',
    'SnapshotEnvelopePage',
)
