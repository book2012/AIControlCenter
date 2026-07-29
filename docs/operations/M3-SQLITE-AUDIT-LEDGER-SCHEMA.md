# M3 SQLite Audit Ledger Schema

Schema version: `dpl/audit-sqlite/v1`

The ledger has `audit_ledger_meta` and `audit_events`. Event storage contains:

- `ledger_sequence`
- `event_id`
- `schema_version`
- `event_type`
- `recorded_at`
- `actor_identity`
- `canonical_payload`
- `payload_digest`
- `previous_event_hash`
- `event_hash`
- `production_authorized`

Required controls are unique indexes
`ux_audit_events_event_id` and
`ux_audit_events_ledger_sequence`, plus triggers
`trg_audit_events_no_update` and
`trg_audit_events_no_delete`. The triggers reject every UPDATE and DELETE.
The writer exposes append only.

`SQLiteAuditSchemaDefinition.ddl_for_test_bootstrap()` is an inert schema
description for pytest fixtures. Runtime code never executes it and performs
no schema creation, migration or repair. Operational schema creation and
activation are outside M3-A1B and remain unauthorized.

