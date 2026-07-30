# M3-A4B2B2B Live Orchestrator Runbook

Git evidence comes only from the fixed read-only `/usr/bin/git` allowlist in
`git_readonly_evidence`; the request cannot replace its collector or commands.
Independent public audit/replay inspection and PRE_ACTIVATION monitoring must
remain valid. Recovery-2 performed no actual operational bootstrap.

The reviewed entrypoint is:

`.venv/bin/python -m core.deployment.operational_bootstrap_live.runner --request <canonical-json-path>`

It accepts exactly `--request`. Approval must be fresh, independent,
non-synthetic, and bound to the exact feature branch, commit, restrictions,
shared parent, and trusted `pwd`-resolved Mac target. Git must be clean and
synchronized.

The live composition uses `MacOperationalBootstrapRuntimeAdapter` and invokes
the execution coordinator directly. Never use the validation runner, a test
adapter, a caller-provided HOME, or environment-only activation for this path.
`BLOCKED` and `FAILED` are nonzero and do not authorize retry.

No live invocation occurred during R3 closure. Obtain fresh independent
approval for the R3 commit before the next task.

R4 records the latest authorized attempt as `BLOCKED_PRE_AUTHORIZATION`.
Strict artifact normalization passed; the attempt created no activation
authorization, permit, claim, or target write. The corrected preflight reader
accepts only `ubuntu_participation=false`, and the permit service/orchestrator
share one frozen typed result. Do not reuse the forensic attempt directory.
Obtain fresh independent approval bound to the R4 commit before any new live
invocation. M3-A4B3 must wait for successful actual bootstrap.
