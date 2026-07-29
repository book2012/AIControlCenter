# M3-A3A Read-Only Operational Monitoring

Status: `CLOSED`

AIControlCenter on the Mac mini M4 is the single Control Plane and operational
monitoring authority. `core.deployment.operational_monitoring` consumes only
immutable, explicitly timestamped evidence and returns a deterministic
canonical monitoring snapshot. It calls no clock, database, command, network,
API, worker or concrete infrastructure adapter.

The only supported operational stage is `PRE_ACTIVATION`. Production, live,
customer-production and unknown privileged stages fail closed. Expected
pre-activation restrictions—including absent operational audit/replay
databases, inactive writers and backup schedules, and unauthorized production
activation—are represented explicitly and do not claim production health.

The snapshot evaluates ordered Control Plane, audit/replay integrity and
recovery, replay concurrency, deployment readiness, regression, Git, safety,
documentation and production-authorization dimensions. Configuration binds
all freshness thresholds, failed-test tolerance, warning policy and Git
ahead/behind tolerance. Identical semantic evidence and explicit timestamps
produce stable ordering, IDs, deduplication keys, canonical JSON and digests.

Alert evaluation creates immutable candidates only. Every candidate has a
redacted summary, evidence references, explicit first-observed and observed
times, `dispatch_authorized=false`, `dispatched=false` and
`production_authorized=false`. External alert dispatch and monitoring
persistence are not implemented.

M3-A1 is `CLOSED`; M3-A2 is `CLOSED`; M3-A3A is `CLOSED` after validation.
Read-only monitoring snapshot: `AVAILABLE`. Alert candidate evaluation:
`AVAILABLE`. Operational databases: `NOT CREATED`. Operational writers:
`NOT ACTIVATED`. Production activation: `NOT_AUTHORIZED`. Next: M3-A3B Alert
Routing and Deduplication.
