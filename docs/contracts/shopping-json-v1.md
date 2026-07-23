# Shopping JSON Contract v1

## Status

- Namespace: `shopping.v1`
- API family: `/shopping/v1`
- Transport: REST/JSON
- Sprint 1 writes: Disabled

## Common Envelope

```json
{
  "schema_version": "shopping.v1",
  "kind": "product_snapshot",
  "id": "shp_prod_01J...",
  "source": {
    "adapter": "woocommerce",
    "site_id": "primary-store",
    "external_id": "123"
  },
  "observed_at": "2026-07-23T00:00:00Z",
  "received_at": "2026-07-23T00:00:01Z",
  "trace_id": "trc_01J...",
  "provenance": {
    "adapter_version": "1.0.0",
    "content_hash": "sha256:...",
    "etag": null
  },
  "security": {
    "classification": "internal",
    "contains_pii": false
  },
  "data": {}
}
```

## Envelope Requirements

- `schema_version` must equal `shopping.v1`.
- Canonical IDs are owned by AIControlCenter.
- External IDs must not become canonical IDs.
- Timestamps must use UTC ISO 8601.
- `trace_id` connects API, policy, adapter, and audit evidence.
- Vendor-specific fields must remain inside adapters until validated.

## Canonical Models

- `ProductSnapshot`
- `VariantSnapshot`
- `PriceSnapshot`
- `InventorySnapshot`
- `CategorySnapshot`
- `ContentSnapshot`
- `CustomerReference`
- `OrderSummary`
- `AdapterHealth`
- `SyncRun`
- `SchemaDriftReport`
- `PolicyDecision`
- `OperationalApproval`
- `AuditEvent`

## Read-Only Contract Rules

- Snapshot models represent observations, not commands.
- Customer and order models minimize PII.
- Raw credentials, payment tokens, and secrets are prohibited.
- Contract validation precedes snapshot persistence.
- Unknown vendor fields must not silently become canonical fields.

## Error Envelope

```json
{
  "schema_version": "shopping.v1",
  "kind": "error",
  "trace_id": "trc_01J...",
  "error": {
    "code": "adapter_authentication_failed",
    "message": "External adapter authentication failed.",
    "retryable": false,
    "source": "woocommerce",
    "details": {}
  }
}
```

## Versioning

- Backward-compatible additions remain within `shopping.v1`.
- Breaking semantic changes require a new namespace.
- Adapter versions remain independent from canonical schema versions.
- Consumers reject unsupported major schema versions.
