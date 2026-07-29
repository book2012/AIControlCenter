# M3-A2A Permit and Replay Integrity Checklist

- [x] AIControlCenter and the Mac Control Plane own authoritative replay state.
- [x] Ubuntu ownership and Production use fail closed.
- [x] The database path is explicit, absolute, outside Git and policy-valid.
- [x] Missing state reports `UNAVAILABLE` without file or directory creation.
- [x] Every runtime SQLite connection uses URI `mode=ro`.
- [x] `query_only` is enabled and the timeout is bounded.
- [x] Required tables, columns, indexes and immutability triggers are checked.
- [x] Event IDs, sequences, gaps, ordering and previous hashes are checked.
- [x] Reservation and terminal lifecycle rules are checked.
- [x] Activation ID and permit digest remain stable per lifecycle.
- [x] Canonical payload, payload digest and event hash are checked.
- [x] Secret, raw nonce, credential and executable payload fields are redacted.
- [x] Reports and permit-state derivation are deterministic canonical JSON.
- [x] Writes, reservations, consumptions, migrations and repairs equal zero.
- [x] M2 and M3-A1 compatibility tests pass.
- [x] M3-A2A is closed after pytest-only validation.

Operational database: `NOT CREATED`.
Durable reservation and consumption: `NOT ENABLED`.
Persistent nonce writes: `NOT ENABLED`.
Production activation: `NOT_AUTHORIZED`.
Next: M3-A2B Durable Permit Reservation and Consumption.
