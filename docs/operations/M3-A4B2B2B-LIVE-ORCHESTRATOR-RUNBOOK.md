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
