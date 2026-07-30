# M3-A4B2B0 Mac Bootstrap Host Preflight

Status: `CLOSED`. The read-only host preflight is `AVAILABLE`.

`core.deployment.operational_bootstrap_preflight` separates optional read-only
Mac evidence collection from deterministic policy evaluation. Explicit
timestamps, host/Git/test/safety evidence, exact future-target evidence,
filesystem and capacity facts, permission plans, and closed-track evidence
produce a canonical report. Identical inputs produce identical ordered checks,
findings, restrictions, decision, report ID, JSON and digest.

The approved host is Darwin arm64, non-root, on
`feature/deployment-package` at the explicitly approved commit, clean and
synchronized. The repository must remain outside the operational Application
Support root. All safety counters and test failures must be zero. The existing
427 warnings are an acknowledged restriction.

The boundary never issues or claims a permit, authorizes or executes bootstrap,
creates a path or database, changes permissions or ownership, activates a
writer or monitoring, dispatches externally, invokes Ubuntu, or authorizes
Production. Writable adapters and write requests are rejected.

M3-A4A, M3-A4B1 and M3-A4B2A are `CLOSED`. Operational permit `NOT ISSUED`;
operational authorization `NOT GRANTED`; operational bootstrap `NOT EXECUTED`;
operational directories and databases `NOT CREATED`; Production activation
`NOT_AUTHORIZED`. Next: M3-A4B2B1 Operational Permit Issuance.
