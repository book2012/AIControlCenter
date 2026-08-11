# SHOP-01A Repository and Architecture Reconciliation

NOTION_SYNC=READY_FOR_FINAL_SYNC
EXTERNAL_NOTION_SYNC_PERFORMED=false

This is a sync-ready payload. It does not claim that Notion synchronization
occurred.

- SHOP-01A1 HEAD: `f95ba9ae2133b55db06c362df321b16785f21423`
- SHOP-01A1 milestone: `SHOP-01A_READ_ONLY_RUNTIME_RECONCILED`
- SHOP-01A2 status:
  `SHOP-01A2_REPOSITORY_UTILIZATION_AND_ARCHITECTURE_RECONCILED`
- SHOP-01A2 HEAD: `55270476e4b4e8d57c041084ff8eafda889c2660`
- Canonical regression: `2670 passed, 5 deselected, 437 warnings`
- Canonical command:
  `ops/macos/validation/run-deployment-regression-gate.sh -q`
- Production mutation authority: disabled
- Final SHOP-01A milestone: `SHOP-01A_SHOPPING_READ_ONLY_FOUNDATION_READY`
- Next: `SHOP-01B_SHOPPING_AI_AND_RECOMMENDATION_RECONCILIATION`

Final architecture state:

- Mac mini M4: always-on Brain and Control Plane host.
- AIControlCenter: single Control Plane; owns Shopping business logic and
  Governance, authorization, and orchestration.
- Ubuntu: stateless infrastructure Worker only; no Shopping business logic,
  Governance, AI workload, application state, or Control Plane authority.
- WordPress: CMS/presentation boundary.
- WooCommerce: Commerce Engine.
- Canonical Shopping domain: `core/shopping/`.
- Shopping API: GET-only.
- Runtime composition: `build_default_shopping_service()`.
- One Shopping read invocation permits one outbound HTTP GET attempt; no
  automatic retry or automatic rollback.
- Capabilities: `write_catalog=false`, `write_executor_available=false`, and
  `production_mutation_authorized=false`.

`WooCommerceControlledWriteAdapter` remains intercepted `ACTIVE_LIBRARY` code
and is not Production enabled. The repository has no concrete Production
outbound write transport, Production credential provider, runtime write
construction, mutation API endpoint, Production mutation authority, automatic
retry, or automatic rollback. Existing SHOP-03 records are preserved.

The next milestone reuses existing SHOP-02 `ProductDraft` work and does not
restart the Shopping architecture. No Git push, external Notion page ID, or
sync timestamp is claimed.

Canonical repository record:
`docs/architecture/SHOP-01A2-REPOSITORY-UTILIZATION-AND-ARCHITECTURE-RECONCILIATION.md`.
