# M3-A1A SQLite Read-Only Integrity Foundation

Status: `CLOSED`

AIControlCenter on the Mac Control Plane owns authoritative durable audit state.
M3-A1A adds only an inspection capability over an explicitly injected SQLite
path. It consumes the canonical DPL audit contracts but does not implement
`DurableAuditPort`, append behavior, creation, DDL, migration, repair, VACUUM,
checkpoint, journal mutation, network access or commands.

The future schema contract requires `audit_ledger_meta`, `audit_events`, unique
event-ID and ledger-sequence indexes, canonical event fields and immutable
append-only behavior. Runtime opens an existing file through SQLite URI
`mode=ro`, enables `query_only`, uses a bounded timeout and closes the
connection deterministically. A missing file reports `UNAVAILABLE`.

Reports are canonical JSON. The configured path is represented only by an
identity digest. Explicit `inspected_at`, stable finding order and database
bytes determine the report ID and digest. Payload contents are never emitted.

M2 controlled pilot validation is `CLOSED`; M3-A1A is `CLOSED` after
validation. The operational audit database was not created, persistent audit
writes are not enabled, migrations were not executed and Production activation
is `NOT_AUTHORIZED`. Next: M3-A1B Append-Only SQLite Audit Writer.
