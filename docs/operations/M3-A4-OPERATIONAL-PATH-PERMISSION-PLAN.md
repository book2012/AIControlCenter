# M3-A4 Operational Path and Permission Plan

This plan defines future Mac Control Plane paths; it does not inspect or create
them. Explicit user-home resolution produces:

- audit database: `~/Library/Application Support/AIControlCenter/audit/audit-ledger.sqlite3`
- audit backups: `~/Library/Application Support/AIControlCenter/audit/backups`
- permit/replay database: `~/Library/Application Support/AIControlCenter/security/permit-replay.sqlite3`
- permit/replay backups: `~/Library/Application Support/AIControlCenter/security/backups`
- monitoring evidence: `~/Library/Application Support/AIControlCenter/monitoring`

Every resolved path must be absolute, Mac-owned, outside Git, outside Ubuntu,
Linux, network and removable ownership, non-symlinked, outside protected system
paths, separated by responsibility and free of secret-bearing names.
Existence is supplied as evidence and is never probed by the gate.

Application-state, audit, security and monitoring directories require `0700`.
SQLite databases, backup databases and manifests require `0600`. Group/world
write, Ubuntu ownership and network filesystems are prohibited. The owner is
the AIControlCenter Mac operator. No `chmod`, `chown` or filesystem operation
is performed by this plan.

Before M3-A4B, all operational paths are expected to be absent and operational
writers disabled. Production activation is `NOT_AUTHORIZED`.
