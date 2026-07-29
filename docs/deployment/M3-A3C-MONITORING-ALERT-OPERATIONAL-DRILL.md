# M3-A3C Monitoring and Alert Operational Drill

## Architecture

AIControlCenter on the Mac Control Plane owns monitoring evidence evaluation,
logical alert policy, and drill governance. The isolated
`core.deployment.monitoring_alert_drill` package depends only on the public
M3-A3A and M3-A3B contracts plus canonical deployment utilities. Ubuntu owns no
monitoring, routing, alert, or drill state.

The drill accepts immutable evidence, creates and validates an M3-A3A snapshot,
creates and validates M3-A3B decisions, converts only routed logical
destinations into simulated envelopes, and submits them only to an injected
object-scoped `InMemorySimulatedAlertSink`. Suppressed and blocked decisions
produce no envelope.

## Safety and validation

Envelope, receipt, plan, and report identities are canonical and deterministic.
The validator checks snapshot, candidate, decision, plan, envelope, and receipt
bindings; exact counts; allowed routes; uniqueness; and zero side-effect claims.
Malformed or tampered evidence, arbitrary destinations, incomplete receipts,
sink failure, dispatch requests, or production authorization fail closed.

The simulator has no filesystem, database, socket, network, external adapter,
global instance, retry, or production composition. Receipts always state
`simulated=true`, `dispatched=false`, `delivered=false`, `persisted=false`, and
`network_used=false`.

## Closure

M3-A1, M3-A2, M3-A3A, M3-A3B, and M3-A3C are `CLOSED`. The M3-A3 Monitoring and
Alert Track is `CLOSED`. End-to-end monitoring drill and simulated logical
delivery are `VALIDATED`. External alert dispatch and alert persistence are
`NOT IMPLEMENTED`. Operational monitoring is `NOT ACTIVATED`; operational
databases are `NOT CREATED`; Production activation is `NOT_AUTHORIZED`.

Next: M3-A4 Controlled Operational Activation Gate.
