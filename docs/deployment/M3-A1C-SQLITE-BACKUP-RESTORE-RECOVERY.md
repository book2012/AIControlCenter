# M3-A1C SQLite Backup, Restore and Recovery Validation

Status: `CLOSED`

`core.deployment.audit_sqlite_recovery` is a separately composed Mac Control
Plane package. It provides immutable contracts and ports for SQLite online
backup, separate-target restore and deterministic recovery validation.

Every path is explicitly injected, absolute, outside Git, within the Mac user
application-state tree and checked by the M3 path policy. Runtime never creates
a parent directory. Relative, traversal, symlink, repository, protected,
Linux, network, removable, secret-bearing and overlapping paths are denied.

Backup requires a `HEALTHY` M3-A1A inspection with valid schema and hash chain,
zero privacy findings and zero production authorization violations. It uses
`sqlite3.Connection.backup` into a restrictive temporary file below the
supplied root, verifies it, binds byte and logical ledger digests into canonical
JSON, then atomically renames the database and manifest. Exact existing content
is idempotent; conflicts are never overwritten.

Restore verifies the manifest, database byte and logical ledger digests,
schema and M3-A1A report before using SQLite online backup into a restrictive
temporary file. The restored database must reproduce every ordered event
identity, payload digest, previous hash and event hash and pass read-only
inspection before atomic rename to a nonexistent target.

Recovery failure never activates, migrates or repairs a database. M2 controlled
pilot validation, M3-A1A, M3-A1B and M3-A1C are `CLOSED`. Validation used only
pytest temporary databases. Operational audit database: `NOT CREATED`.
Operational backup schedule: `NOT ACTIVATED`. Operational restore:
`NOT PERFORMED`. Persistent audit writer activation: `NOT STARTED`. Production
activation: `NOT_AUTHORIZED`. Next: M3-A2 Durable Permit and Replay State.
