# M3-A4B2B2A — Authorized Mac Bootstrap Execution Capability

Status: CLOSED after validation.

AIControlCenter now owns an approved, fail-closed Mac Control Plane capability
for validating a live controlled-non-production permit, atomically consuming
that permit, and performing the previously validated audit/replay bootstrap.
The implementation is isolated in
`core.deployment.operational_bootstrap_execution`. It reuses the M3-A4B2A
SQLite bootstrap adapter and read-only expectations; no schema was copied.

The two code modes are `TEST_ONLY_OPERATIONAL_EXECUTION_VALIDATION` and
`CONTROLLED_NON_PRODUCTION_OPERATIONAL_BOOTSTRAP`. Only the first was invoked
for this increment. The controlled mode is available but was not executed.
Ubuntu, workers, WordPress, WooCommerce and n8n have no role.

Runtime validation is deterministic and ordered. It requires exact Git
binding and parity, Darwin/non-root evidence, trusted `pwd` home resolution,
the exact Application Support layout, local fixed storage, capacity, absent
targets, canonical permit and issuance JSON, matching identity/digest,
not-before/expiry/bootstrap deadline, single use, independent identities, two
warning acknowledgements, readiness/preflight/schema/target/plan bindings, and
all activation/production flags false.

The M3-A4B2B1C permit remained unclaimed and untouched. It expires or will
expire unused and is invalid once this increment changes the bound commit.
Fresh preflight evidence and a fresh permit are required for M3-A4B2B2B.

Operational result: targets and databases were not created; writers,
monitoring and dispatch were not activated; production remains
`NOT_AUTHORIZED`.
