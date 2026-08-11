# SHOP-01A2 Repository Utilization and Architecture Reconciliation

Status: `SHOP-01A2_REPOSITORY_UTILIZATION_AND_ARCHITECTURE_RECONCILED`

This is a retrospective architecture reconciliation and Production
baseline-hardening record. It is not a greenfield restart, a replacement
Shopping domain, or a rewrite of completed SHOP-01, SHOP-02, or SHOP-03
history. The canonical Shopping domain remains `core/shopping/`; no parallel
`src/aicontrolcenter/shopping` domain is authorized.

## Verified baseline

- SHOP-01A1 HEAD: `f95ba9ae2133b55db06c362df321b16785f21423`
- Milestone: `SHOP-01A_READ_ONLY_RUNTIME_RECONCILED`
- Canonical regression: `2670 passed, 5 deselected, 437 warnings`
- Canonical command:
  `ops/macos/validation/run-deployment-regression-gate.sh -q`

The raw `.venv/bin/python -m pytest -q` invocation is not the canonical full
repository gate. Deployment tests require the macOS validation wrapper and the
test roots it provisions.

## Permanent ownership

- The Mac mini M4 is the always-on Brain.
- AIControlCenter is the single Control Plane and owns Governance, Shopping
  business logic, authorization, orchestration, audit, and deployment control.
- Ubuntu is an optional stateless infrastructure Worker. It owns no Shopping
  business logic, Governance, AI workload, application state, or Control Plane
  authority.
- WordPress is the CMS and Shopping/Commerce presentation boundary. It does not
  own Shopping business logic.
- WooCommerce is the Commerce Engine.
- Host Caddy remains the only public edge.

## Repository utilization classification

Only the following classification vocabulary is canonical.

### `ACTIVE_RUNTIME`

- `core/api/routes/shopping.py`
- Shopping registration in `core/api/app.py`
- Shopping composition in `core/api/routes/dashboard.py`
- `core/dashboard/shopping_management.py`
- `core/shopping/service.py`
- `core/shopping/config.py`
- `core/shopping/factory.py`
- active Shopping read adapters under `core/shopping/adapters/`
- `core/shopping/secure_runtime.py`

`build_default_shopping_service()` is the canonical runtime composition used by
both `/shopping` and the Shopping dashboard.

### `ACTIVE_LIBRARY`

- `core/shopping/application/`
- `core/shopping/ports/`
- `core/shopping/contracts/`
- `core/shopping/governance/`
- `core/shopping/observability/`
- `core/shopping/product_drafts/`
- the intercepted SHOP-03 deployment/live boundary, including
  `WooCommerceControlledWriteAdapter`

The SHOP-03 adapter is retained library capability. Its existence is not
Production enablement.

### `MAPPED_FOR_REUSE`

- `core/shopping/adapters/woocommerce_read_transport.py`
- `core/cms/`
- selected generic Governance and Deployment abstractions where their
  authorization, evidence, and execution boundaries fit without moving
  Shopping business ownership

### `DOMAIN_SPECIFIC_RETAINED`

- `deploy/shopping/`
- `scripts/shopping/`
- catalog and storefront domain support assets

### `DEPRECATED_OR_CANDIDATE_REMOVAL`

None currently established. Age alone is not removal evidence.

## Read-only runtime contract

The Shopping API is GET-only. One WooCommerce read invocation permits exactly
one outbound HTTP GET attempt. Automatic read retry is disabled. Runtime
capabilities report:

- `write_catalog = false`
- `write_executor_available = false`
- `production_mutation_authorized = false`

`configured_write_mode` is informational only and grants no executable or
Production authority.

## SHOP-03 write boundary

`WooCommerceControlledWriteAdapter` can prepare an allowlisted WooCommerce PUT
request for intercepted validation. It remains `ACTIVE_LIBRARY` and must not be
deleted or described as Production enabled.

The following Production capabilities do not exist:

- concrete outbound Production `CommerceWriteTransport`;
- Production credential provider;
- runtime construction;
- API wiring;
- mutation endpoint; and
- Production mutation authority.

There is no automatic retry or automatic rollback. A desired-state package is
not activation authorization, and DPL must not be routed through
`UbuntuWorkerClient.execute` or generic remote commands.

## Governance invariants

Production mutation requires explicit human authorization. Authorization must
be consumed before invocation, and one permission permits one bounded
invocation. Remaining mutation budget is accounting only, not retry authority.
Governance adapters cannot authorize or widen scope or budget. The Governance
API projection is READ ONLY. Evidence must be value-free, and `/private/tmp`
is transient only.

## Historical reconciliation

The repository already contains delivered SHOP-01 read/dashboard work,
SHOP-02A ProductDraft architecture, SHOP-02B domain work, SHOP-02C application
services, SHOP-03A controlled-write architecture, and SHOP-03B1 intercepted
adapter work. SHOP-01A reconciles and hardens that existing chronology; it does
not renumber, replace, or invalidate it.

## Closeout path

The next milestone is `SHOP-01A3_CLOSEOUT_AND_FINAL_SYNC`: human review of this
documentation-only change, Git closeout on the approved feature branch, and
final external documentation synchronization. No external synchronization is
claimed here. The recommended terminal milestone name is
`SHOP-01A_REPOSITORY_AND_ARCHITECTURE_RECONCILED`.
