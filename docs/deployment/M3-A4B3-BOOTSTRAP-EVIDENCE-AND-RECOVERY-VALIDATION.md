# M3-A4B3 Bootstrap Evidence and Recovery Validation

## Decision

M3-A4B3 is `READY_FOR_CONTROLLED_ACTIVATION_VALIDATION`. This is an evidence
decision only. It does not authorize production, runtime writers, monitoring,
external dispatch, permit issuance, another claim, or permit reuse.

## Completed operational facts

The controlled non-production bootstrap bound to commit
`f7a81b73b86c170300bb6b80f437dbb753362f7e` completed once. Activation
authorization
`m3-a4b2b2b-r2-60cc9ee1f8cf6c9a55a97cea3224786d` issued typed permit
`m3-a4b2b2b-r4-permit-a72d2e43cc42cf05150884e95919d4b7`, which was consumed
by the single atomic claim
`m3-a4b2b2a-claim-ef74c0c861feb6868e45999396e6f6db`.

Five managed directories, two SQLite databases, and two baseline backups were
created. Audit and replay inspections are `HEALTHY` with zero events. Both
baseline backups passed isolated restore validation. Shared-parent mode `0755`
compatibility and existing siblings were preserved. Writers, monitoring, and
dispatch remain inactive; Ubuntu participation is zero; production is
`NOT_AUTHORIZED`.

## Architecture boundary

`core.deployment.bootstrap_evidence_recovery` consumes only immutable evidence
and operational snapshots. It uses canonical digest helpers and the public
audit and replay read-only inspectors. Restore outputs exist only below the
explicit recovery-work root. The boundary has no issuer, claim registry,
bootstrap runner, writer, monitoring activation, dispatch, network, command,
Ubuntu, or application-business-logic dependency.

The outer snapshot projection may remove owner-write permission, producing
`0500` directories and `0400` files. Validation accepts that immutable subset
of the successful `0700`/`0600` state but never broader permissions. Symlinks,
wrong ownership, executable managed files, group/world access, unmanaged
entries, path escape, and pre-existing restore destinations fail closed.

## Evidence and recovery rules

The strict approval, shared-parent preflight, live request, full
acknowledgement projection, activation authorization and evidence, typed permit
and issuance evidence, one claim, receipt, bootstrap bundle, post-validation,
and `PRE_ACTIVATION` step are content- and digest-validated. Exact Git,
identity, restriction, warning-pair, root, time-window, and ID cross-bindings
are required. `failure-evidence.json` must be absent.

Each baseline manifest must be canonical, non-production, service-correct, and
bound to the exact backup byte digest. Restores use fresh `0700` drill
directories and `0600` destinations under recovery work. Restored databases
must be `HEALTHY`, schema-current, query-only, zero-event, and source-immutable.
The resulting report is canonical deterministic JSON.

## Safety conclusion

The successful permit is permanently consumed. A desired-state package or
this readiness decision is not activation authority. The next task is
`M3-A4C_ACTIVATION_VALIDATION_AND_CLOSEOUT`; production remains
`NOT_AUTHORIZED`.
