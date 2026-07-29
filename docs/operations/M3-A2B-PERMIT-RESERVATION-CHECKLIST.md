# M3-A2B Permit Reservation Checklist

- [x] M3-A2A remains read-only and CLOSED.
- [x] Writer package is separate and explicitly configured.
- [x] Existing absolute policy-valid database path is required.
- [x] Missing databases and parent directories remain missing.
- [x] Runtime uses SQLite URI `mode=rw`; `mode=rwc` is prohibited.
- [x] WAL must already be configured; runtime never changes journal mode.
- [x] Schema, indexes, triggers, settings and complete chain are validated.
- [x] `BEGIN IMMEDIATE` serializes reservation and terminal transitions.
- [x] Reservation binds all permit, activation, package and identity fields.
- [x] Only `RESERVED → CONSUMED` and `RESERVED → FAILED_CLOSED` are accepted.
- [x] Identical retries are idempotent and conflicts are denied.
- [x] Concurrent transitions preserve exactly one terminal state.
- [x] Raw nonce, secrets, Production and Ubuntu are denied.
- [x] Immutable receipts disclose no raw database path.
- [x] Tests wrote only pytest temporary databases.
- [x] Operational creation, migration, repair and activation equal zero.

Operational replay database: `NOT CREATED`.
Operational writer: `NOT ACTIVATED`.
Production activation: `NOT_AUTHORIZED`.
