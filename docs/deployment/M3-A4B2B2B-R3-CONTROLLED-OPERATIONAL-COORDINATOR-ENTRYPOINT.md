# M3-A4B2B2B-R3 Controlled Operational Coordinator Entrypoint

Recovery-2 closes the first recovery's remaining Git-evidence blocker. The
default composition now uses `ReadOnlyGitEvidenceCollector`; subprocess is
permitted only in `core.deployment.git_readonly_evidence` for a fixed
`/usr/bin/git` read-only allowlist. Tests independently invoke the public audit
and replay inspectors, public PRE_ACTIVATION monitoring, and validate canonical
mode-0600 post-claim failure evidence. The validation runner remains
validation-only. Actual bootstrap is `NOT EXECUTED`, actual targets remain
absent, fresh approval must bind the final R3 commit, and production remains
`NOT_AUTHORIZED`.

The previous R3 attempt was `BLOCKED_PRE_AUTHORIZATION`. Recovery adds
`core.deployment.operational_bootstrap_live.composition` as the reviewed
default collaborator root and completes the mandatory pytest-only end-to-end
scenario. R3 retains `core.deployment.operational_bootstrap_live` as the sole reviewed local
composition boundary for a controlled non-production Mac bootstrap. The prior
attempt remains `BLOCKED_PRE_AUTHORIZATION`; no gate was removed or bypassed.

The package owns immutable request contracts, canonical JSON parsing,
approval/preflight/Git/host binding, atomic artifact persistence, and direct
invocation of `OperationalMacBootstrapExecutionCoordinator`.
`operational_bootstrap_execution.runner` remains validation-only.
The live runner accepts only `--request` and assembles its fixed graph itself;
JSON, CLI, and environment cannot inject collaborators.

No operational bootstrap ran. Actual managed targets remain absent and real
authorization, permit, and claim counts remain zero. Production activation is
`NOT_AUTHORIZED`. A fresh independent approval bound to the new commit is
mandatory.

Next: M3-A4B2B2B Fresh Approval and Authorized Mac Bootstrap.
