# Shopping storage/provider package 0.5.0 candidate

Date: 2026-11-03. Status: **FEATURE-BRANCH CANDIDATE VALIDATED; NOT DEPLOYED**.
This record supersedes earlier extraction-status statements where they conflict.
It does not supersede the deployed legacy application or production authority.

## Current result

AI Home Datacenter remains the umbrella and AIControlCenter the sole Mac control
plane. Three optional packages are independently selectable; absence/failure of one
does not take down core health. Shopping is now a local 0.5.0 candidate; Creative
Notes and Personal Assistant remain 0.1.0 adapters.

| Area | Completed code / evidence | Remaining gate |
| --- | --- | --- |
| Shopping domain | Product/order/catalog logic; customer identity, sessions, auth contracts, persistence, migration contracts and inquiries in wheel | Production verifier and runtime authority stay host-owned |
| WooCommerce reads | Product/category/search/order mapping and canonical normalization behind explicit ports and strict authorizers | Real credentials, destination, signing, policy and HTTP transport supplied by trusted host |
| Stored data | Explicit existing-store start/close; no attach-time creation/migration; leased-job drain, reattach and fixture backup/restore | Production DB inventory, backup/restore and authenticated E2E not performed |
| Creative Notes | Independent Site reference adapter and missing-package isolation | Per-account authenticated private API not connected |
| Personal Assistant | Injected provider status adapter and missing-package isolation | Authenticated provider transport/execution not connected |
| Common lifecycle | Admission close, leased work drain, cleanup, timeout/retry states, dependency-safe shutdown | Legacy jobs not registered as leases are outside this boundary |
| Release | Deterministic wheels and fresh offline target installation | Regression gate green; production gate remains separate |

## Source and compatibility

Shopping package owns `customer_identity.py`, `customer_sessions.py`,
`customer_auth.py`, `customer_persistence.py`, `customer_session_service.py`,
`migration_contract.py`, `inquiries.py` and `storage_resource.py`. Existing security
modules re-export the same implementation module, preserving class/patch identity.
The host inquiry constructors retain existing deployment contact configuration;
the wheel has no real contact URL and defaults to no contact channels. The host
SQLite bridge remains an instance of the host memory repository.

The inquiry atomic-transaction test now instruments the actual package module;
its BEGIN/COMMIT assertions and transaction semantics are unchanged.

Provider-specific order projection/bridge and canonical normalization are in the
wheel. Host wrappers still compose existing schema validation and external-read
policy. The standalone builders require both validator and authorizer callbacks;
only the exact boolean True grants access/validation. Category/product and order
ports have separate path scopes. Raw order not-found handling now uses structured
HTTP status 404 rather than matching an error-message substring.

`core/shopping/adapters/woocommerce_rest.py` retains legacy construction,
credentials, OAuth signing, HTTP transport and policy preflight. Its transport
module is byte-identical to the previous commit. Existing API responses, policy
boundaries and legacy production entry point are preserved. Host verifier,
workflow/bot orchestration, operator UI and deployment composition remain host
responsibilities; this is not a claim that every legacy file has moved.

## Storage ownership and lifecycle

`ShoppingStorageResource(database_path, data_root=..., channel_provider=...)`
performs no construction I/O. `start()` requires an explicit existing absolute
DB path inside the supplied root and rejects missing/outside/symlink stores.
It opens schema validation through SQLite mode=ro/query_only, validates the current
persistence schema and reads inquiry sequence state; it executes no DDL/migration.
Session/repository operations remain the existing authenticated implementation.
The legacy SQLite constructor still retains its old schema-creation behavior for
compatibility; managed attachment uses `open_existing`, never that constructor.

`core.modules.shopping_storage.storage_module_instance` composes this resource
with a trusted synchronous FastAPI application factory. The factory must supply
its own request authorization; resource readiness grants no API authority.
Child ASGI lifespan is not automatically invoked. Extra resources must use explicit
ModuleInstance lifecycle hooks. Register background work with `manager.lease`.
Manager closes admission, drains leases, then clears routes and storage references.
Short-lived DB connections close per operation. Detach never deletes files,
revokes sessions or migrates schema. Reattach opens the same existing store.

This is a cooperative, process-local boundary with a trusted local filesystem,
not a sandbox, distributed lock, or guarantee against concurrent privileged path
replacement. Production must separately establish single-writer/job ownership.

## Build and validate without activation

Use the compatible host Python environment and a **new empty target**:

```sh
python -m scripts.build_plugin_wheels --output dist/plugins/complete-v05-final
python -m pip --isolated --disable-pip-version-check install --no-index --no-deps --target .plugin-packages/complete-v05-final dist/plugins/complete-v05-final/*.whl
PYTHONPATH="$PWD/.plugin-packages/complete-v05-final" python -m pytest -q tests/test_plugin_packages.py tests/test_plugin_catalog.py tests/test_module_attach_detach.py tests/test_module_lifecycle.py tests/test_module_shopping_bindings.py tests/test_shopping_domain_package.py tests/test_catalog_plugin_extraction.py tests/test_woocommerce_plugin_read.py tests/test_shopping_storage_lifecycle.py tests/test_shopping_provider_package.py
```

Do not rerun pip into an existing target or install these candidate wheels into the
shared interpreter. Generated wheels/targets are Git-ignored. No new dependencies
were installed in the shared environment. Host and Shopping wheel must be promoted
as a matched generation: this host imports modules first added in 0.5.0. API v1
alone does not make an older Shopping wheel compatible with these legacy facades.
Rollback means the complete matching host+wheel generation, with its data retained;
no production upgrade/rollback or schema rollback was attempted.

## Verification and historical test reconciliation

- Fresh offline installation: **185 plugin/lifecycle/provider/storage cases passed,
  zero failures/skips**. Two builds produced identical wheel bytes; wheel RECORD
  hashes/sizes and package boundaries are verified.
- Expanded related scope: **2,415 passed, zero failures/skips**, 106 unique test
  files in six independent processes to preserve session import-isolation checks.
- Existing TestClient/datetime deprecation warnings remain; no dependency upgrade.
- This is related regression evidence, not a claim that every repository test or
  real-provider/production E2E was run.

An initial wider run found 234 failures, all reproduced with identical IDs at
`d4263e5`. These baseline failures are now resolved through test-composition fixes:

1. Historical preactivation tests used the currently deployed topology even though
   their eight-file observer contract predates it. They now copy byte-exact files
   from commit `f4d50eae4e452434922013463a3a486a2bbd8c52` into a temporary root.
   `tests/fixtures/preactivation_f4d50eae/provenance.json` pins every SHA-256.
   Existing deny-order, ambiguous-route, integrity, logging and adversarial
   assertions remain. A new separate test proves the current repository still
   fails closed under this old observer. No active policy digest/config changed.
2. Legacy read-port tests now assert exact host/package object identity and pass
   the installed plugin path to their guarded subprocess. All side-effect blockers
   remain active. A module's new package location is not a contract failure.
3. Inquiry contracts now use an explicitly injected in-memory test app and the
   required access token for detail reads. No-token access is asserted 401. A new
   preview regression requires creation/detail to remain 404. Variant and escaping
   assertions are retained. Production/preview security was not relaxed.

These are current-task regression repairs, not removed/skipped tests or changed
runtime policy. The repository test gate is green before feature-branch Git work.

The original main worktree's HEAD, index and 26 pre-existing dirty files are checked
against the saved baseline. No production DB, runtime, launchd, Caddy, DNS,
WordPress, WooCommerce, real customer data, Site or Ubuntu changes were made.

See [machine-readable evidence](SHOPPING_STORAGE_PROVIDER_PACKAGE_05.json).

## Next concrete work

1. Register any remaining legacy jobs with explicit module leases and prepare a
   matched host+Shopping-wheel generation for operator-shell migration.
2. Define and inject per-account Notes/Assistant credentials and read-only APIs;
   do not use a shared owner token or infer readiness from a public URL.
3. Collect production inventory, backup/restore, authenticated E2E and rollback
   evidence for separate activation review. `AGENTS.md` states: “Production
   activation requires a separate authorization gate.” No production switch is
   authorized by this candidate.
