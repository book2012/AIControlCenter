# M3-A4B2A Controlled Mac Bootstrap Executor Validation

M3-A4B2A is `CLOSED`. `core.deployment.operational_bootstrap` implements the
controlled Mac bootstrap executor solely for
`TEST_ONLY_BOOTSTRAP_VALIDATION`, confined to the exact injected
`AICONTROLCENTER_BOOTSTRAP_TEST_ROOT` under `/private/tmp`.

The executor validates the original M3-A4B1 request, decision and canonical
synthetic permit, including exact Git, readiness, restrictions, targets,
schemas, plan, safety, expiry, one-use and inactive/production-false bindings.
It atomically claims the injected in-memory registry before mutation.

Validation creates the equivalent application-state layout only below the
pytest root, applies `0700` directory and `0600` file permissions, bootstraps
empty append-only audit and replay SQLite schemas, and verifies both with
public read-only inspectors. It creates baseline backups and manifests,
restores each into a separate validation subtree, requires `HEALTHY`, and
removes restore targets when configured. PRE_ACTIVATION monitoring evidence is
derived in memory and is neither persisted nor dispatched.

Failure cleanup removes only artifacts below target subtrees proven absent
before this execution. The permit remains claimed and no partial success is
returned. Existing targets are never overwritten, migrated, repaired or
inferred to be idempotent.

Status: M3-A4A `CLOSED`; M3-A4B1 `CLOSED`; M3-A4B2A `CLOSED`; executor
`IMPLEMENTED`; synthetic permit consumption, audit/replay bootstrap, baseline
backup/restore and cleanup `VALIDATED`. Operational permit `NOT ISSUED`;
operational bootstrap `NOT EXECUTED`; operational directories/databases `NOT
CREATED`; writers and monitoring `NOT ACTIVATED`; Production activation
`NOT_AUTHORIZED`.

Next: M3-A4B2B Authorized Mac Operational Bootstrap Execution.
