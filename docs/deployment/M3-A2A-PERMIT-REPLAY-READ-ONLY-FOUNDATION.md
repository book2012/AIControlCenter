# M3-A2A Durable Permit and Replay State Read-Only Foundation

Status: `CLOSED`

AIControlCenter on the Mac Control Plane owns authoritative permit policy,
nonce disposition and replay state. Ubuntu cannot own or mutate that state.
`core.deployment.permit_replay_sqlite` defines immutable schema, path,
finding, report, event-type and derived-state contracts plus an explicit-path
read-only inspector.

The future operational path is:

`~/Library/Application Support/AIControlCenter/security/permit-replay.sqlite3`

This path is policy only and has no implicit runtime default. The inspector
accepts an explicitly injected absolute Mac user application-state path
outside Git, rejects traversal and symlinks, and opens only an existing regular
file through SQLite URI `mode=ro`. It activates `query_only`, uses a bounded
timeout, closes deterministically and performs no DDL, migration, repair,
journal change, reservation or consumption.

The inert future schema expectation models `permit_replay_meta` and an
append-only `permit_use_events` hash chain. It requires unique event IDs and
sequences, one reservation and at most one terminal event per permit,
immutable payloads, UPDATE/DELETE rejection, and
`production_authorized=false`.

Inspection detects schema drift, replay contradictions, lifecycle binding
changes, ordering and hash-chain damage, payload modification, secrets,
Production use and Ubuntu ownership. Permit histories derive deterministically
to `UNUSED`, `RESERVED`, `CONSUMED`, `FAILED_CLOSED` or `INVALID`. Reports
expose only path and permit identity digests and canonical redacted findings.

M2 controlled pilot validation and M3-A1 are `CLOSED`. M3-A2A is `CLOSED`
after pytest-only validation. Permit/replay read-only inspection is
`AVAILABLE`; the operational permit/replay database was `NOT CREATED`.
Durable reservation and consumption are `NOT ENABLED`; persistent nonce writes
are `NOT ENABLED`; Production activation is `NOT_AUTHORIZED`. Next:
M3-A2B Durable Permit Reservation and Consumption.
