# M3-A2C Replay-State Backup, Recovery and Concurrency Validation

Status: `CLOSED`

`core.deployment.permit_replay_sqlite_recovery` composes the public M3-A2A
inspector and M3-A2B writer contracts on the Mac Control Plane. It provides
immutable explicit-path backup, restore, manifest, receipt, finding and
validation contracts; replaceable ports; online backup/restore services; exact
recovery validation; and post-recovery concurrency validation. Production
composition is absent and disabled.

Backup requires a healthy existing source and supplied existing backup root.
It uses `sqlite3.Connection.backup` into a restrictive temporary file,
reinspects it read-only, binds byte, ordered logical-ledger, derived-state and
source-report digests into canonical JSON, then atomically renames the verified
database and manifest. Restore verifies every binding before using the same
online API into a restrictive temporary restore file. It proves exact ordered
event and permit-state equality before atomic rename and never selects the
result operationally.

Path policy rejects implicit, relative, traversal, repository, protected,
Ubuntu, network/removable, overlapping, symlink and secret-bearing paths.
Parents are never silently created and existing targets are never overwritten.
Failures before final rename, manifest-write failures, corruption, mismatch and
transaction interruption fail closed and clean partial outputs.

M3-A1 and M3-A2A through M3-A2C are `CLOSED`. Validation used only pytest-owned
temporary databases. Post-recovery concurrency proved exactly one reservation,
an idempotent identical loser, exactly one terminal state, denial of the
conflict and a healthy final ledger without duplicate sequences or event IDs.

Operational replay DB: `NOT CREATED`. Operational backup schedule:
`NOT ACTIVATED`. Operational restore: `NOT PERFORMED`. Operational writer:
`NOT ACTIVATED`. Raw nonce writes: zero. Production activation:
`NOT_AUTHORIZED`. Next: M3-A3 Operational Monitoring and Alerts.
