# M3-A4B2B2 — Authorized Bootstrap Execution Runbook

This runbook applies only to the Mac mini M4 Brain and single Control Plane.
It does not authorize execution by itself.

Before a future controlled run, obtain fresh readiness and preflight evidence,
an independently approved permit bound to the exact clean synchronized feature
branch commit, and an explicit execution request. Confirm the operator is a
non-root local macOS account. The trusted root must resolve through the local
account database to:

`<home>/Library/Application Support/AIControlCenter`

The only targets are `audit/audit-ledger.sqlite3`, `audit/backups`,
`security/permit-replay.sqlite3`, `security/backups`, and `monitoring`.
The parent may safely preexist and is shared application state. Never chmod,
chown, remove or recursively inspect it or its unrelated siblings. Accept it
only under the shared-parent policy with every managed subtree absent. Record
pre-existing mode `0755` as `EXISTING_SHARED_PARENT_MODE_NOT_0700`; require
`0700` on newly created managed directories and `0600` on managed files.

Invoke the narrow module with one canonical JSON request:

`.venv/bin/python -m core.deployment.operational_bootstrap_execution.runner --request <path>`

Unknown arguments, unknown fields, commands, scripts, URLs, secrets,
production scope and activation flags are rejected. The validation runner
accepts test mode only. A future controlled execution requires separate
authorization and all coordinator gates. `BLOCKED` or `FAILED` exits nonzero.

Never delete a claim, reuse a permit, select another root, route through
Ubuntu, or activate writers, monitoring, dispatch or production.

## Completed bootstrap validation

The one controlled bootstrap bound to
`f7a81b73b86c170300bb6b80f437dbb753362f7e` completed successfully. Its
permit and claim are permanently consumed. M3-A4B3 subsequently validated the
canonical chain, `HEALTHY` zero-event databases, baseline backups, isolated
restores, shared-parent/sibling preservation, and inactive runtime flags. This
historical success does not authorize rerun or production.
