# M3-A4B1 Controlled Bootstrap Authorization

M3-A4B1 is `CLOSED`. AIControlCenter on the Mac Control Plane owns the pure
authorization boundary for the sole stage
`CONTROLLED_NON_PRODUCTION_BOOTSTRAP_AUTHORIZATION`.

The boundary binds the exact feature branch and commit, the complete M3-A4A
readiness report, every restriction acknowledgement, future target identities,
audit and replay schema expectations, path/permission/bootstrap/rollback
plans, test and Git parity evidence, zero safety counters, independent operator
and approver identities, and explicit issue and expiry timestamps.

`READY_WITH_RESTRICTIONS` is accepted only when every original restriction is
acknowledged without rewriting its text. The existing 427 deprecation warnings
remain represented by `DEPRECATION_WARNINGS_OUTSTANDING` and require an exact
operator-and-approver acknowledgement.

The resulting permit is canonical-hash integrity bound, deterministic,
controlled-non-production only, and limited to one use. It is not
cryptographically signed and is not an identity-authentication mechanism. It
authorizes only a future controlled bootstrap attempt within its exact scope;
writer activation, monitoring activation, external dispatch, API writes,
service restarts, Ubuntu participation, arbitrary commands, and Production
activation remain false.

The package has no clock, filesystem, SQLite, network, notification, command,
API, worker, executor, or concrete registry implementation. Synthetic permits
and claims were validated only with an object-scoped test fake.

Status: M2 `CLOSED`; M3-A1 `CLOSED`; M3-A2 `CLOSED`; M3-A3 `CLOSED`; M3-A4A
`CLOSED`; M3-A4B1 `CLOSED`. Bootstrap authorization capability `AVAILABLE`;
synthetic test permit issuance `VALIDATED`; operational bootstrap permit `NOT
ISSUED`; operational bootstrap authorization `NOT GRANTED`; operational paths
`NOT CREATED`; writers `NOT ACTIVATED`; Production activation
`NOT_AUTHORIZED`.

Next: M3-A4B2 Controlled Mac Operational Bootstrap.
