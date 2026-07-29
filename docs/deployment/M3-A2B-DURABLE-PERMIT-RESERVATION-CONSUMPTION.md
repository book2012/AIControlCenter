# M3-A2B Durable Permit Reservation and Consumption

Status: `CLOSED`

`core.deployment.permit_replay_sqlite_writer` is the Mac Control Plane-owned,
existing-file-only durable permit registry. It is separate from the M3-A2A
read-only inspector, which remains unchanged and `CLOSED`.

The registry requires explicit immutable configuration, a policy-valid absolute
path and an already provisioned compatible database. It opens SQLite only by
URI `mode=rw`, requires WAL to be preconfigured, enables foreign keys and
FULL synchronous durability, uses bounded busy waits and serializes writes with
`BEGIN IMMEDIATE`. It creates no file, directory, schema or migration.

Every reservation binds permit and activation digests, package and plan,
readiness evidence, Mac sandbox target, environment, sandbox-root digest and
requester/operator/approver identities. Raw nonce material and secret-bearing
content are rejected. Production and Ubuntu targets are denied.

Before every append the complete sequence, canonical payload, payload digest,
event hash, previous-event hash and lifecycle are validated. Valid transitions
are `UNUSED → RESERVED → CONSUMED` and
`UNUSED → RESERVED → FAILED_CLOSED`. Identical retries are idempotent;
conflicts fail closed. Receipts expose a database path identity digest, never
the raw path.

Validation used pytest-owned temporary databases only. Operational replay
database: `NOT CREATED`. Operational writer: `NOT ACTIVATED`. Raw nonce writes:
`NOT ENABLED`. Production activation: `NOT_AUTHORIZED`.

Next: M3-A2C Replay State Backup, Recovery and Concurrency Validation.
