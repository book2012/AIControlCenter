# MODULE-ATTACH-DETACH-01 — isolated modular composition

Date: 2026-11-03 (Asia/Seoul)
Status: implemented and fixture/in-process verified; not deployed.
Baseline: 29a40dc6f22b2b436a91c08532cb61387dc6d634.

## Ownership and scope
AI Home Datacenter is the overall platform. AIControlCenter on Mac owns
platform policy, approvals, audit, deployment and orchestration. Domain modules
own domain functionality and explicit interfaces; Ubuntu remains an infrastructure
worker. WordPress is CMS and WooCommerce is commerce. Atelier remains a separate
WordPress theme, not this platform module or the legacy shopping API package.

The existing core/api/app.py eagerly composes ShoppingRuntime and an inquiry
repository. Homepage and Dashboard also reference shopping directly. This change
introduces a separate core/api/modular.py factory rather than silently replacing
that production entry point. It is a minimal modular preview shell, NOT a drop-in
replacement for all existing operator, authentication or governance APIs.

## Module contract
- Registry IDs: shopping, creative-notes, personal-assistant.
- Manifest schema 1: exactly schema_version and attached. Unknown fields, duplicate
  keys, duplicate/unknown IDs, missing attached dependencies and cycles fail closed.
- Manifest is data, never a Python import path, credentials or deployment permission.
- Factories are trusted, stateless in-process read adapters; no automatic discovery,
  package execution, background work or dynamic code loading.
- Only explicitly selected implementations are constructed. All default to DETACHED.
- Namespace: /extensions/{module_id}; platform health/status remain separate.
- HTTP mutations and WebSockets are denied in the preview composition. This is not
  a security sandbox for untrusted Python; trusted GET handlers must be read-only.
- Snapshot status reports composition, not current upstream health. ATTACHED does
  not claim running jobs, verified external connectivity or production readiness.
- Optional construction failure produces UNAVAILABLE; dependent selected modules
  become BLOCKED. Other modules and core remain available. Exceptions are not
  included in the status projection. No automatic retry or fallback activation.

## Implemented shopping seam
core/modules/shopping.py lazily constructs the real existing ShoppingService with
explicit isolated mock catalog settings. It exposes health, paginated product list,
and product detail; it ignores inherited live WooCommerce/write-mode settings.
No inquiry DB, durable order/session data, credentials, notifications, AI calls,
legacy runtime imports or external network access are needed. This provides a
working attachment seam without migrating the current store's transactions.

Creative Notes and Personal Assistant are registered identities only. Selecting
them without a provider honestly reports UNAVAILABLE and mounts no routes. Their
source/deployment ownership must be resolved before implementation extraction.

## Attach / detach / reattach
Composition is fixed for one application generation. There is no public mutation
endpoint and no hot-unload while requests are in flight.

1. Review the data-only manifest. Detached example: config/modules/detached.json.
2. Shopping preview example: config/modules/shopping-preview.json.
3. Inspect the plan, from this worktree with the repository Python environment:

   python -m scripts.module_plan config/modules/shopping-preview.json
   python -m scripts.module_plan config/modules/detached.json

These commands only print JSON. They do not edit manifests, start/stop services,
change routes, contact providers, delete data, or change the current process.
To compose in code: create_app(manifest_path=path) from core.api.modular.
Calling create_app() defaults to all detached. A future reviewed runtime generation
must drain requests, then replace the old process using existing deployment control.
Changing a manifest does not modify an already running process. Existing launchd,
Caddy, DNS, containers and public routes were not changed here.

Detach retains module-owned data and does not revoke provider credentials, erase
WordPress/WooCommerce records or cancel existing external jobs. Legacy workers and
bots are not controlled by this preview. Real module adoption requires explicitly
binding those resources to a lifecycle and testing drain/restart/recovery. Data
purge is a separate explicit operation, absent from this implementation.

## Evidence
- 238 tests passed: test_module_attach_detach.py (39 cases),
  test_shopping_runtime_components.py, test_shop_api_read_003.py,
  test_capability_manifest_lookup.py. One existing TestClient deprecation warning.
- Fresh-process detached import test blocks disabled domain imports and DB/network/
  subprocess access; core composition still succeeds.
- Attach/detach/reattach generations, retained fixture data, cross-module failure,
  dependency ordering/cycles, invalid manifests, read-only methods/WebSocket,
  real mock-catalog adapter and unchanged core health are covered.
- Tests use TestClient; no live port, production service, order, SMS or Ubuntu access.
- MODULE_ATTACH_DETACH_01_IMPORTS.json lists 25 files with relevant absolute imports
  in the scanned scope. Static inventory only; not a full transitive/runtime graph.

## Remaining migration gates
1. Extract shopping domain package from current source snapshots after transitive
   dependencies, authorization and read/write boundaries are resolved. Retain
   approved legacy DEV/PROD versions; do not copy the dirty original worktree.
2. Resolve Creative Notes source, deployment and data owner; integrate a read-only
   provider. Do the same for Personal Assistant/OpenClaw.
3. Add governed real adapters and lifecycle for DB connections, scheduled jobs,
   notification consumers and in-flight work. Detach blocks new domain work, drains
   existing work and preserves data. Test retry/recovery before hot lifecycle support.
4. Extend the common operator shell without importing disabled domains. Run full
   regression, authenticated E2E, data restore and release/rollback gates before any
   service switch. No production migration or full plugin separation is claimed.
