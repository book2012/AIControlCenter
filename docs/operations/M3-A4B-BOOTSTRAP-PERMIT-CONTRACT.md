# M3-A4B Bootstrap Permit Contract

The immutable M3-A4B1 permit binds its request and decision IDs, the sole
controlled non-production stage, exact branch and commit, M3-A4A report ID and
digest, complete restriction-acknowledgement digest, target/schema/plan/safety
digests, requester/operator/approver identities, explicit issue and expiry
times, maximum uses of one, and a canonical permit digest.

Within that exact permit scope only, `bootstrap_authorized=true`. The permit
always has `writers_authorized=false`, `monitoring_authorized=false`,
`external_dispatch_authorized=false`, and `production_authorized=false`.

Before future use, validation recomputes the canonical digest and checks every
request, decision, Git, readiness, restriction, target, schema, plan, safety,
identity, time, use-limit, and environment binding. Malformed, tampered,
expired, privileged, or contradictory permits fail closed.

Use is separated from validation through
`OperationalBootstrapPermitUseRegistryPort`. A caller supplies a registry that
can inspect status and atomically claim an unused permit. The package supplies
no filesystem, SQLite, network, global, or singleton registry and the use guard
never executes bootstrap.

Canonical hashing provides deterministic integrity binding, not a
cryptographic signature or identity authentication. No operational permit has
been issued.
