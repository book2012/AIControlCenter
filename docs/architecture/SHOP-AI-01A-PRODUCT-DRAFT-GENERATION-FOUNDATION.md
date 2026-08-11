# SHOP-AI-01A ProductDraft Generation Foundation

Status: `SHOP-AI-01A_PRODUCT_DRAFT_GENERATION_FOUNDATION_READY`

Verified implementation HEAD: `52db3600ae76c70926e27ce930be70fe34f98452`

Verified canonical regression: `2691 passed, 5 deselected, 437 warnings`

Canonical command:
`ops/macos/validation/run-deployment-regression-gate.sh -q`

## Domain and contract

`core/shopping/` remains the canonical Shopping domain. SHOP-AI-01A reuses the
existing SHOP-02 `ProductDraft`, its `ProposedFields`, and immutable
`ProductDraftRevision`; it does not replace the core model. The Shopping-owned
structured generation contract is version `1.0.0` and accepts only existing
`ProposedFields` members.

Successful preparation creates an immutable revision candidate with AI
`SuggestionProvenance` for generated fields. The candidate remains
`LifecycleState.DRAFT`. Preparation performs no automatic validation, human
approval, or deployment-intent creation.

## Provider boundary

The generation adapter reuses canonical `core.providers.ProviderAdapter` and
has exactly one explicitly injected provider. Requests use a bounded timeout
and `RetryPolicy(max_attempts=1)`. There is no provider fallback. The command
canonicalizes and snapshots `source_context` before execution. The provider,
model, response digest, and optional `provider_request_id` remain traceable in
the generation result and audit projection.

## Invocation semantics

The generation service consumes the operation key through its injected
coordinator before it invokes the provider. A completed duplicate with the same
command digest returns the recorded result; a concurrent in-flight duplicate
is suppressed; key reuse with a different digest fails as a conflict; and a
failed consumed operation is terminal rather than automatically retried.

The precise guarantee is:

> AT-MOST-ONE provider invocation per consumed operation key within the
> injected coordinator's durability scope.

This is not global exactly-once semantics. The current coordinator,
`InMemoryProductDraftGenerationOperationCoordinator`, is thread-safe but
process-local, memory-only, and explicitly non-production. Its state does not
survive process loss and it cannot supply a Production durability guarantee.

## Persistence and transaction boundary

SHOP-AI-01A prepares a revision and audit projection in memory. It does not
implement:

- durable ProductDraft persistence;
- a durable generation operation ledger;
- a transactional revision + audit + operation Unit of Work;
- a generation API or Dashboard generation mutation;
- a recommendation or ranking engine;
- WooCommerce write integration or Production mutation authority;
- automatic retry or automatic rollback.

The desired-state candidate is preparation output only; it is not activation
authorization. WooCommerce remains the Commerce Engine, and no live Commerce
mutation is performed.

## Control Plane placement and Production safety

The Mac mini M4 remains the always-on Brain and AIControlCenter remains the
single Control Plane. ProductDraft state, generation operation state, AI
application state, governance, authorization, audit, and business logic belong
to AIControlCenter. Ubuntu is an optional stateless infrastructure Worker and
may own none of that state or authority. The generation path is not routed
through a generic Ubuntu command boundary.

Production mutation authority remains prohibited. This milestone introduces
no Production persistence adapter, API mutation, Dashboard mutation,
WooCommerce mutation, approval, deployment intent, retry, or rollback.

## Next milestone

`SHOP-AI-01B_DURABLE_PRODUCT_DRAFT_GENERATION_TRANSACTION` is next. Its first
bounded task is architecture/discovery of existing durable persistence and
transaction conventions before implementation. The design must establish a
Mac Control Plane-owned durable ProductDraft store, durable operation ledger,
and atomic revision + audit + operation transaction without placing
ProductDraft or AI application state on Ubuntu.

Recommendation is a separate future stream:
`SHOP-REC-01A_RECOMMENDATION_ARCHITECTURE`.
