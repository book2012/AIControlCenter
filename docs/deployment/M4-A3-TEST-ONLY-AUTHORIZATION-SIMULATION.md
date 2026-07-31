# M4-A3 Test-Only Authorization Simulation

M4-A1, M4-A1R1, and M4-A2 are closed. M4-A3 deterministically simulates each
capability in isolation and closes with
`READY_FOR_READ_ONLY_OPERATIONAL_OBSERVATION`. This does not authorize runtime
activation, an operational writer, monitoring, dispatch, notification, Ubuntu,
or production. Future work requires separate architecture and authorization.

The injected clock and scenario seed produce stable test IDs, canonical JSON,
SHA-256 digests, and the immutable chain `REQUESTED → INDEPENDENTLY_APPROVED →
AUTHORIZATION_PLANNED → SIMULATED_AUTHORIZED → SIMULATED_PERMITTED →
SIMULATED_CLAIMED → SIMULATION_VALIDATED`. The operational state machine and
`CONTROLLED_ACTIVE` are never called.

Every artifact has `test_only=true`, `operationally_valid=false`,
`production_authorized=false`, `ubuntu_participation=false`,
`runtime_activation_allowed=false`, namespace `m4-a3-test-only`, source
`deterministic-simulation`, and an unmistakable `m4-a3-test-*` ID. Marker
removal or field renaming cannot make it operational. Live authorization,
permit, claim, bootstrap, and activation boundaries reject it fail-closed.

The process-local permit permits exactly one deterministic claim. Duplicate
claim, permit reuse, capability or digest mismatch, skipped state, timestamp
regression, and evidence tampering are denied. All five capabilities are
independent. Monitoring does not imply writers or dispatch; dispatch and
external-notification dependency references are evidence, never authorization.
There is no endpoint, credential, network, subprocess, command, API write, n8n,
WordPress, WooCommerce, Ubuntu authority, operational database, or live runner.

Optional JSON reporting is confined beneath an injected test root. No real
authorization, permit, claim, writer, monitoring, dispatch, notification,
activation, service restart, or production change occurred. Production remains
`NOT_AUTHORIZED`; Ubuntu is excluded; `.env` is not required or read. The 427
deprecation warnings remain separate backlog.

## Verification

The M4-A3 targeted suite passed 48 tests; M4-A2 passed 59; M4-A1/M4-A1R1
passed 46; M3-A4C passed 59; dependency boundaries passed 18; combined M3/M4
passed 212; all deployment tests passed 1,065 with 9 warnings; and the full
suite passed 2,049 with 5 configured deselections and the existing 427
warnings. No test was weakened and no operational state was accessed.
