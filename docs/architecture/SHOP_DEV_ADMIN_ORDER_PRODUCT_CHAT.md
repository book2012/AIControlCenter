# DEV order admin and Codex product intake

## Scope

This feature is mounted only in the isolated DEV order API at
`/dev-order/admin`. Caddy's existing DEV Basic Auth protects the page and
`/__order-dev/admin/*` APIs. PROD runtime, commerce data, and product catalog
are not connected.

The page combines recent DEV orders, on-demand address details, fulfillment
status, aftersales requests, inquiry records, and a chat panel. Order chat calls
the existing `OperatorConversation`, preserving its bounded intent parsing,
actor-scoped dialogue, and explicit confirmation step before mutations.

## Product intake

Messages beginning with “상품 등록”, “상품 추가”, or “신규 상품” are queued
to the existing Codex draft worker as product intake jobs. The worker creates an
isolated feature worktree from a pinned DEV source revision. Its prompt permits
only one file:
`brands/agachichi/catalog/intake-drafts/<job-id>.json`. The API validates the
exact schema, DEV environment, and job id before displaying it.

The draft can summarize supplied facts, suggest conservative product copy, and
list missing category, price, variant, stock, and image information. Codex must
not invent factual fields. User text is treated as task data, and the candidate
is shown as untrusted review material.

This path does not update the DEV catalog or media manifests, call WooCommerce,
register a product, publish a listing, or create images. Completing product
registration requires a reviewed image upload and verified spec handoff to the
existing `ops/macos/shopping/dev_upload_product_register.py --apply-dev`
workflow. Those steps remain a release gate for end-to-end product registration.

## Request protection

Browser POST routes require the exact DEV storefront origin. Admin routes remain
behind the Caddy Basic Auth boundary and return no-store responses. Order list
responses omit delivery addresses; addresses are fetched only after the operator
selects an order detail. Product intake uses generated random job ids and
parameterized SQLite writes. Product status exposes only a validated candidate
for a matching product-intake job.

## Validation

Focused tests cover address-on-demand behavior, same-origin chat requests,
product job queuing without Commerce writes, Codex prompt bounds, and review-only
job completion. DEV API immutable release `9c0784cdcb71c1bee8e4d6a98c3e3520d6106cf8`
is active. The external unauthenticated admin route returned 401, the local page
returned 200, and a same-origin read-only order-list chat returned 200. A
synthetic product request completed through the live Codex worker and produced
schema-valid JSON in an isolated worktree. No order mutation, WooCommerce
registration, or PROD write was performed. The rollback backup is stored under
`AIControlCenterRuntime/dev-order/backups/dev-order-admin-20261017-095343`.
