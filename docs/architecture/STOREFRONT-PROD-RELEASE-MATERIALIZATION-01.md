# STOREFRONT-PROD-RELEASE-MATERIALIZATION-01 — immutable release materialization

## Purpose

This foundation gives the Control Plane a separate, explicit operator for
creating the production storefront release. The read-only
`storefront_prod_runtime` module and `scripts/storefront_prod_runtime.py` keep
their status, validate, and plan-only contract; they do not gain a materialize
or apply command.

The only accepted payload is the exact Git archive of commit
`6eaaaef4aa4ec0fa57d5e3d21bad056aeb9a59e7` for
`deploy/shopping/wordpress/plugins/ai-shopping-storefront`. The operator never
reads the repository working-tree plugin directory. It rejects archive
symlinks, traversal paths, unexpected file types, identity drift, and any
existing conflicting destination. The accepted payload contains 299 regular
files.

## Release contract

The release root is:

`~/AIControlCenterRuntime/releases/storefront-prod`

The payload is written only at:

`releases/6eaaaef4aa4ec0fa57d5e3d21bad056aeb9a59e7/ai-shopping-storefront`

The operator writes `current.json` at the root and the existing
`.aicontrolcenter-release.json` marker inside the plugin directory. Both carry
the accepted commit, plugin version `0.19.0`, presentation identifier
`SHOP_MEDIA_003_AGACHICHI`, `git_archive` provenance, and a deterministic
relative-file SHA-256 manifest. The existing runtime validate/status contract
is used for the final read-back check.

## Authorization and boundaries

Every materialization requires an explicit authorization bound to the accepted
commit and exact release root. Authorization is single-use. Destination and
archive checks occur before consumption; the first release-root write occurs
only after authorization consumption, and file-backed authorization state is
marked consumed before that write.

This operation is repository-governed artifact preparation only. It does not
change the current WordPress mount or runtime state, perform a runtime
lifecycle operation, modify compose state, reload the public edge, mutate a
database or commerce state, access Ubuntu, or push Git. DEV deployment remains
distinct from PROD promotion, and a release artifact is not activation
authorization.

## Clean control-plane source invariant

Before one-shot authorization is consumed, release materialization checks
`git status --porcelain=v1 --untracked-files=all` for the control-plane
repository and fails closed if any tracked or untracked change is present.

This makes `source_clean=true` and
`source_provenance.working_tree_clean=true` observed provenance rather than
an assumed value. The release payload still comes only from `git archive` of
the exact accepted payload commit; the control-plane HEAD does not need to be
the same commit as the accepted storefront payload.

## VM visibility requirement

The release root uses ~/AIControlCenterRuntime/releases/storefront-prod because the commerce Colima profile must mount it read-only into the VM. Materialization does not itself modify Colima configuration or restart the VM. A later, separately authorized infrastructure step must establish that mount before runtime activation. Post-activation proof must compare host, VM, and container payload identity.
