# SHOP-AI-01A ProductDraft Generation Foundation

NOTION_SYNC=READY_FOR_FINAL_SYNC
EXTERNAL_NOTION_SYNC_PERFORMED=false

This payload is ready for a separately authorized final synchronization. It
does not claim that any external Notion synchronization occurred.

- Final milestone: `SHOP-AI-01A_PRODUCT_DRAFT_GENERATION_FOUNDATION_READY`
- Verified implementation HEAD: `52db3600ae76c70926e27ce930be70fe34f98452`
- Canonical regression: `2691 passed, 5 deselected, 437 warnings`
- Canonical command:
  `ops/macos/validation/run-deployment-regression-gate.sh -q`
- Next milestone:
  `SHOP-AI-01B_DURABLE_PRODUCT_DRAFT_GENERATION_TRANSACTION`
- Separate future stream: `SHOP-REC-01A_RECOMMENDATION_ARCHITECTURE`

`core/shopping/` remains canonical. SHOP-02 `ProductDraft`, existing
`ProposedFields`, immutable `ProductDraftRevision`, and canonical
`core.providers.ProviderAdapter` are reused. Structured generation contract
`1.0.0` prepares AI provenance-bearing candidates that remain
`LifecycleState.DRAFT`; it performs no automatic validation, human approval,
or deployment-intent creation.

There is one injected provider, `RetryPolicy(max_attempts=1)`, bounded timeout,
no provider fallback, snapshotted source context, and a traceable optional
provider request ID. The exact guarantee is **AT-MOST-ONE provider invocation
per consumed operation key within the injected coordinator's durability
scope**, including concurrent duplicate suppression. Global exactly-once
semantics are not claimed. The current
`InMemoryProductDraftGenerationOperationCoordinator` is non-production.

Durable ProductDraft persistence, a durable generation operation ledger, a
transactional revision + audit + operation Unit of Work, generation API,
Dashboard generation mutation, recommendation/ranking engine, WooCommerce
write integration, Production mutation authority, automatic retry, and
automatic rollback are not implemented.

SHOP-AI-01B begins with architecture/discovery of existing durable persistence
and transaction conventions. ProductDraft and AI application state remain on
the Mac AIControlCenter Control Plane and may not be placed on Ubuntu.
