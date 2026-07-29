# M3-A3B Alert Routing and Deduplication

AIControlCenter on the Mac Control Plane owns alert-routing, deduplication and
escalation policy. `core.deployment.alert_routing` consumes immutable M3-A3A
`AlertCandidate` values, explicit history evidence, explicit configuration,
snapshot bindings and an explicit evaluation timestamp.

The pure service deterministically produces canonical logical routing plans.
It calls no clock, database, command, network, Ubuntu client, API, worker,
notification or persistence adapter. A plan never claims delivery:
`alerts_dispatched`, `notifications_sent` and `persistence_writes` are zero.

The default logical routes are the Control Plane dashboard, operator review,
incident response, security review and documentation backlog. They are policy
labels only. Caller-controlled destinations and concrete notification adapters
are denied.

M3-A1, M3-A2, M3-A3A and M3-A3B are `CLOSED` after validation. Logical alert
routing, deterministic deduplication and severity escalation policy are
`AVAILABLE`. External alert dispatch and alert-routing persistence are
`NOT IMPLEMENTED`. Operational monitoring is `NOT ACTIVATED`; operational
databases are `NOT CREATED`; Production activation is `NOT_AUTHORIZED`.
Next: M3-A3C Monitoring and Alert Operational Drill.
