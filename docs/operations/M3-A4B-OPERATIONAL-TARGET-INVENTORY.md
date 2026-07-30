# M3-A4B Operational Target Inventory

All targets are future Mac Control Plane state and must be absent before an
authorized bootstrap:

| Responsibility | Exact target | Future mode |
|---|---|---|
| Audit database | `~/Library/Application Support/AIControlCenter/audit/audit-ledger.sqlite3` | `0600` |
| Audit backup root | `~/Library/Application Support/AIControlCenter/audit/backups` | `0700` |
| Replay database | `~/Library/Application Support/AIControlCenter/security/permit-replay.sqlite3` | `0600` |
| Replay backup root | `~/Library/Application Support/AIControlCenter/security/backups` | `0700` |
| Monitoring root | `~/Library/Application Support/AIControlCenter/monitoring` | `0700` |

Future SQLite, backup and manifest files use `0600`; directories use `0700`.
The expected owner is the AIControlCenter Mac operator. Group write, world
access, Ubuntu/Linux ownership, network/removable filesystems, symlinks,
repository overlap and protected paths are prohibited.

M3-A4B2B0 does not create or modify this inventory. Operational permit is
`NOT ISSUED`, authorization is `NOT GRANTED`, bootstrap is `NOT EXECUTED`, and
Production activation is `NOT_AUTHORIZED`.
# Shared-parent ownership correction

`~/Library/Application Support/AIControlCenter` is a shared parent and is not
an exclusively managed target. Deployment control owns only `audit/`,
`security/`, and `monitoring/`. All other existing siblings remain outside its
ownership and must not be modified.
