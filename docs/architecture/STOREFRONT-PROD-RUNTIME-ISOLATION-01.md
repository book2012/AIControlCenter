# STOREFRONT-PROD-RUNTIME-ISOLATION-01 — immutable PROD runtime foundation

## Scope and status

This commit is a source foundation only. It does not claim that runtime
remediation is complete, and it does not apply a release, restart WordPress,
reload Caddy, mutate a database, or access Ubuntu.

The accepted migration candidate is Git commit
`567cb90ee7fdec0fa82f39c3ad6ce28d46381479`, plugin version `0.18.0`, and
presentation identifier `SHOP_MEDIA_003_AGACHICHI`.

## Failure being isolated

Implicit promotion was caused by a repository-backed Docker bind mount:
`shopping-wordpress` consumed the Git working-tree plugin directory directly.
As a result, a Git fast-forward implicitly promoted the candidate to PROD.
The current 0.18.0 runtime is an exact candidate match, but its provenance
path is unsafe because it is still backed by the repository working tree.

The Git working tree must never be a production artifact. Repository source is
not an immutable PROD release. DEV deployment is not PROD promotion.

## Contract

PROD must consume only an immutable, commit-addressed release directory:

`~/Library/Application Support/AIControlCenter/releases/storefront-prod/releases/<40-character-git-commit>/ai-shopping-storefront`

The compose bind is therefore parameterized by
`AICONTROLCENTER_STOREFRONT_PROD_PLUGIN_PATH`, fails closed when unset, and
remains read-only at the existing WordPress plugin destination. The
AIControlCenter-owned read-only module and CLI inspect the release identity,
the commit-addressed path, the provenance marker, and the plugin entrypoint.
Their plan contract is JSON-compatible and always has `execute=false`; it
does not materialize, copy, deploy, recreate, reload, or mutate anything.

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
