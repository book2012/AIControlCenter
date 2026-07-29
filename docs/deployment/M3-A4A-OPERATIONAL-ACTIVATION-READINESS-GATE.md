# M3-A4A Operational Activation Readiness Gate

M3-A4A is `CLOSED`. The activation readiness gate is `AVAILABLE` for the sole
stage `PRE_ACTIVATION_READINESS`. It is a pure, immutable, evidence-driven
decision boundary owned by AIControlCenter on the Mac Control Plane.

The gate validates M2, M3-A1, M3-A2 and M3-A3 closure; test, Git,
documentation, recovery, concurrency, monitoring-drill and safety evidence;
future paths and permissions; the controlled bootstrap plan; rollback
requirements; explicit timestamps; and production contradictions. It returns
stable canonical JSON, IDs, digests, ordered checks, findings and restrictions.
Deprecation warnings create a remediation finding and restriction and normally
produce `READY_WITH_RESTRICTIONS`.

A readiness decision is not authorization. Every report sets bootstrap,
writer, monitoring, external-dispatch and production authorization to false.
The package has no clock, filesystem probe, database access, persistence,
notification, command, network, API, worker, Ubuntu, bootstrap executor or
activation executor.

Pre-activation absence of operational databases, backup roots and monitoring
evidence is expected. An existing operational path without an authorized
bootstrap receipt, an active writer, active monitoring or active external
dispatch fails closed.

Status: M2 `CLOSED`; M3-A1 `CLOSED`; M3-A2 `CLOSED`; M3-A3 `CLOSED`; M3-A4A
`CLOSED`. Operational databases are `NOT CREATED`; writers and monitoring are
`NOT ACTIVATED`; external alert dispatch is `NOT IMPLEMENTED`; bootstrap
authorization is `NOT GRANTED`; Production activation is `NOT_AUTHORIZED`.

Next: M3-A4B Controlled Mac Operational Bootstrap.
