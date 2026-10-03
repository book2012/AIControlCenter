# HOMEPAGE-DEV-RUNTIME-001 — Managed pre-production Homepage DEV runtime

## Scope

This candidate defines a read-only foundation for the managed DEV Homepage
runtime on the Mac mini Control Plane.  It does not install a plist, create a
release, start a process, or execute a lifecycle operation.

The runtime contract is fixed to `127.0.0.1:18080`, with the existing Host
Caddy route remaining outside this candidate.  The repository-owned launchd
candidate is `com.aicontrolcenter.homepage-dev`; its future installed wrapper
is `/usr/local/libexec/aicontrolcenter/run-homepage-dev-immutable-release.sh`.

## Three separate boundaries

* **Interactive Preview != Managed DEV Runtime.**
  `scripts/preview_orange_coco.py` remains a developer-only interactive
  preview and may retain `reload=True`.  It is not a launchd target.
* **Managed DEV != Production.**
  The managed runtime is a pre-production release service with a loopback-only
  listener, a DEV manifest, and no production authority.
* **DEV deployment != PROD promotion.**
  A valid DEV release is not permission to promote, activate, or mutate any
  production system.

## Release model

The future release root is:

```text
~/Library/Application Support/AIControlCenter/releases/homepage-dev/
  releases/<40-char-commit>/
    .aicontrolcenter-release.json
    core/...
  current.json
```

`current.json` and the release-owned provenance marker use schema version 1
and contain `environment`, `service`, `git_commit`, `release_path`,
`created_at`, `source_clean`, `source_provenance`, and the deterministic
presentation identifier.  The release directory must be exactly the directory
named by the full lowercase commit and must not be a symlink.

Materialization is planned around deterministic `git archive` semantics.  A
plan is not an apply operation.  The plan is approved only when the requested
commit is the repository `HEAD` and the working tree is clean.  No uncommitted
source may become an approved DEV release.  Secret or environment material is
not part of the release manifest; the wrapper does not read `.env` files.

## Runtime and wrapper safety

The future wrapper fails closed when the current manifest, release path,
provenance marker, or Homepage runtime files are absent or inconsistent.  It
uses only the materialized release as `PYTHONPATH`, clears the inherited
environment before the final process, and executes the configured project
virtual-environment interpreter with Uvicorn without a reload watcher.  The
final command binds only `127.0.0.1` on port `18080`.

The wrapper is repository source for a future installation.  This candidate
does not install it and does not write `/usr/local/libexec`.

## JSON-first read-only contracts

`python scripts/homepage_dev_runtime.py status --release-root <root>` returns
the stable status object.  `validate` returns a deterministic validation
object and fails closed for an invalid manifest.  `plan` returns a JSON
materialization plan with `execute: false`; it performs only Git inspection.
There is no write HTTP endpoint and no lifecycle executor in this sprint.

## Validation sequence

After a separately authorized DEV deployment materializes a release, the
read-only sequence is focused tests, manifest validation, managed runtime
status, and the existing `scripts/check_orange_coco_preview.py` validator.
The validator's current contract, including a load-more href containing
`page=2`, remains unchanged.  Visual QA and release freeze are gates before
any separately authorized PROD promotion.

No WooCommerce authority, Ubuntu authority, Caddy lifecycle mutation, or
production activation is introduced here.
