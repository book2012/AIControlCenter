# M3-A1B Append-Only SQLite Audit Writer

Status: `CLOSED`

`core.deployment.audit_sqlite_writer` is a separately composed Mac Control
Plane adapter. It preserves the canonical audit domain and implements the
append capability of `DurableAuditPort` without converting the M3-A1A
read-only package into a write layer.

The writer requires an explicitly injected absolute database path and an
existing regular file accepted by the M3 path policy. It opens SQLite with URI
`mode=rw`, never `mode=rwc`, and cannot create a file, directory, schema,
migration or repair. Production composition remains writer-disabled.

Each append uses a bounded busy timeout, `foreign_keys=ON`,
`synchronous=FULL`, preconfigured WAL validation and `BEGIN IMMEDIATE`.
Within the transaction it validates schema metadata, required columns, unique
indexes, append-only triggers, every existing payload digest and the complete
hash chain. It then validates the request’s next sequence and previous hash,
inserts exactly one canonical event, reads it back, verifies all values, and
commits. Any failure rolls back.

An identical existing event ID returns a deterministic idempotent receipt with
zero writes. Conflicting reuse is denied. Receipts expose only a database-path
identity digest and contain no payload values.

Validation used only pytest-owned temporary SQLite databases. No operational
database was created or changed. Operational writer activation is not started,
persistent Production audit writes are not enabled, and Production activation
is `NOT_AUTHORIZED`. Next: M3-A1C Backup, Restore and Recovery Validation.

