# M2-P3 Pilot Evidence and Rollback Validation

Status: **CLOSED**

`core.deployment.pilot_evidence` provides immutable canonical evidence,
deterministic validation and evidence-derived rollback plans. Rollback is
available only through an injected `SandboxRollbackPort`; production code has
no filesystem rollback adapter, command runner, network client, database or
persistence.

Evidence binds the exact M2-P1 permit, accepted readiness report, execution
authorization, M2-P2 activation receipt, package, plan, Mac target,
non-production environment, sandbox-root identity, identities, ordered
activation results, before/after manifests, artifacts, explicit time and zero
safety counters. Missing, reordered, duplicated, mismatched, altered, unsafe
or persistent-host claims fail closed.

Automated validation performed exactly one rollback below a pytest-owned
temporary directory. The request was consumed before the test adapter ran.
Only activation-created artifacts from the immutable plan were removed and the
recorded pre-activation digest was restored. Replay after success and failure
was denied.

`ROLLED_BACK` means only that the controlled pytest sandbox returned to its
recorded pre-activation state. It does not mean persistent-host or Production
rollback.

- DPL-04: `CLOSED`
- M2 readiness: `ACCEPTED`
- M2-P1, M2-P2 and M2-P3: `CLOSED`
- M2 controlled pilot validation: `CLOSED`
- Persistent host pilot activation: `NOT STARTED`
- Persistent host rollback: `NOT IMPLEMENTED`
- Persistent SQLite audit adapter: `NOT IMPLEMENTED`
- Production activation: `NOT_AUTHORIZED`
- Next: M3-A1 Durable SQLite Audit Adapter
