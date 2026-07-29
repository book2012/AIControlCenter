# M3-A4A Activation Readiness Checklist

- [x] Mac Control Plane ownership is explicit; Ubuntu ownership is rejected.
- [x] M2 and pilot closure evidence is required.
- [x] M3-A1A through M3-A1C closure evidence is required.
- [x] M3-A2A through M3-A2C closure evidence is required.
- [x] M3-A3A through M3-A3C closure evidence is required.
- [x] Full regression and deployment tests have zero failures.
- [x] Git is on the approved branch, clean and synchronized.
- [x] Architecture and documentation closure is explicit.
- [x] Every safety counter is zero.
- [x] Audit and replay recovery, post-recovery concurrency and monitoring drill pass.
- [x] Path, permission, bootstrap and rollback plans validate.
- [x] Evidence timestamps are explicit, current and non-contradictory.
- [x] Secrets and executable instructions are rejected.
- [x] Operational database absence is `PRE_ACTIVATION_EXPECTED`.
- [x] No write, directory, database, writer, monitoring or dispatch occurs.
- [x] Bootstrap and Production authorization remain false.

Gate outcome: `AVAILABLE`. M3-A4A: `CLOSED`. Operational databases: `NOT
CREATED`. Operational writers and monitoring: `NOT ACTIVATED`. External alert
dispatch: `NOT IMPLEMENTED`. Production activation: `NOT_AUTHORIZED`.

Next: M3-A4B Controlled Mac Operational Bootstrap.
