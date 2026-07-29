# M3-A3A Monitoring Checklist

Status: `CLOSED`

- [x] Mac mini M4 remains the Brain and single Control Plane.
- [x] AIControlCenter remains the monitoring and alert-decision authority.
- [x] Only explicit `PRE_ACTIVATION` evaluation is accepted.
- [x] All evidence and time values are immutable explicit inputs.
- [x] Audit/replay integrity, recovery and concurrency evidence is bound.
- [x] M2 readiness, controlled-pilot closeout, regression and Git evidence is bound.
- [x] Every required safety counter is present and zero in healthy evidence.
- [x] Snapshot, finding, candidate and dimension ordering is deterministic.
- [x] Snapshot IDs, candidate IDs, deduplication keys and digests are stable.
- [x] Missing, stale, malformed and contradictory evidence fails closed.
- [x] Secret-bearing fields, raw paths and privileged stages are excluded.
- [x] Writes performed, alerts dispatched and notifications sent remain zero.
- [x] No database, subprocess, network, API, worker or notification adapter is used.
- [x] Dependency policy and full regression validation pass.

Read-only monitoring snapshot and alert-candidate evaluation are `AVAILABLE`.
External alert dispatch and monitoring persistence are `NOT IMPLEMENTED`.
Operational databases are `NOT CREATED`; operational writers are
`NOT ACTIVATED`; Production activation is `NOT_AUTHORIZED`.

Next task: M3-A3B Alert Routing and Deduplication.
