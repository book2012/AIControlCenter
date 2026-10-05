# STOREFRONT-PROD-RUNTIME-ISOLATION-01 — immutable PROD runtime foundation

## Scope and status

This commit is a source foundation only. It does not claim that runtime
remediation is complete, and it does not apply a release, restart WordPress,
reload Caddy, mutate a database, or access Ubuntu.

The repository `HEAD` is the AIControlCenter Control Plane source revision.
It is independent from the accepted storefront payload. The accepted
production storefront payload revision is `ACCEPTED_GIT_COMMIT`:
`ee229261459e24d1a2d73b39bbbb8e2fa4042ba9`, with plugin version `0.19.1` and
presentation identifier `SHOP_MEDIA_003_AGACHICHI`.

## Failure being isolated

Implicit promotion was caused by a repository-backed Docker bind mount:
`shopping-wordpress` consumed the Git working-tree plugin directory directly.
As a result, a Git fast-forward implicitly promoted the candidate to PROD.
The previous 0.19.0 runtime proved the immutable mount path, but external verification exposed a canonical-catalog compatibility defect. The accepted 0.19.1 payload keeps canonical Shopping items instead of filtering them by demo media eligibility.

The Git working tree is never the production artifact. Repository source is
not an immutable PROD release. DEV deployment is not PROD promotion.

## Contract

PROD must consume only an immutable, commit-addressed release directory:

`~/AIControlCenterRuntime/releases/storefront-prod/releases/<40-character-git-commit>/ai-shopping-storefront`

The compose bind is therefore parameterized by
`AICONTROLCENTER_STOREFRONT_PROD_PLUGIN_PATH`, fails closed when unset, and
remains read-only at the existing WordPress plugin destination. The
AIControlCenter-owned read-only module and CLI inspect the release identity,
the commit-addressed path, the provenance marker, and the plugin entrypoint.
When `--commit` is omitted, the plan contract selects `ACCEPTED_GIT_COMMIT`,
never the repository `HEAD`. An explicit non-accepted commit is rejected
fail-closed. The plan contract is JSON-compatible and always has
`execute=false`; it does not materialize, copy, deploy, recreate, reload, or
mutate anything.

## Boundaries

AIControlCenter on the Mac mini remains the sole Control Plane and owns
governance, policy, orchestration, authorization, audit, deployment control,
and business logic. WordPress remains presentation/CMS only. WooCommerce
state is untouched. Database mounts, WordPress persistent-volume ownership,
WooCommerce, Caddy, the Shopping API topology, and Ubuntu are outside this
remediation.

Any future production release write or runtime cutover requires separate,
one-shot explicit authorization. This candidate introduces no apply command,
no lifecycle operation, and no authorization consumption.

## Control-plane HEAD and accepted payload identity

The current control-plane Git HEAD and the accepted storefront payload commit
are intentionally separate identities.

`git_commit` remains the immutable storefront payload revision selected for
`git archive`. `control_plane_head` records the current governance/control-plane
revision. A clean control-plane repository may therefore approve an earlier
exact accepted payload commit.

Plan approval does not authorize a release write or PROD activation. Those
remain separate explicit authorization gates.

## Colima-visible release boundary

The default PROD storefront release root is intentionally outside the Git repository and uses a no-space host path:

~/AIControlCenterRuntime/releases/storefront-prod

The commerce Colima profile must expose this root read-only through virtiofs before Docker activation. Host-side release validation alone is insufficient: promotion proof requires the same accepted payload to be visible from the host, the Colima VM, and the WordPress container.
