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

## Reviewed DEV registration

The admin page now turns a Codex draft into an editable review form. The operator
must complete required product facts, choose inventory/price/options, and upload
five role-specific images: hero, original, model-front, garment-cutout, and
model-other. Each image has validated MIME/signature, size limits, SHA-256
recording, and a per-file AI provenance checkbox; the original image cannot be
marked AI-generated.

Saving the review reserves a unique DEV catalog ID in a private SQLite database.
A read-only preflight builds a temporary candidate packet and invokes the
existing registrar without WooCommerce writes. Only after preflight succeeds can
the operator type the exact product name and submit the separate DEV registration
action. An ambiguous outcome becomes non-retryable until an operator checks the
DEV catalog. No production endpoint or credentials are configured in this path.

Successful registration publishes a product in DEV WooCommerce. Homepage
catalog mapping/projection remains a separate review and activation step, so a
WooCommerce product may not immediately appear on the storefront.

## Request protection

Browser POST routes require the exact DEV storefront origin. Admin routes remain
behind the Caddy Basic Auth boundary and return no-store responses. Order list
responses omit delivery addresses; addresses are fetched only after the operator
selects an order detail. Product intake uses generated random job ids and
parameterized SQLite writes. Product status exposes only a validated candidate
for a matching product-intake job.

## Validation

81 focused order/admin, operator, draft-worker, and intake tests pass. Python
compilation and diff checks pass. Immutable DEV API release
`da1d2095361a3559b798584a21286ebb703cde1b` is active. Runtime health reports
`DEV`, `product_management=RUNNING`, `operator_bridge=RUNNING`,
`codex_website_drafts=ENABLED`, and `poller=EXTERNAL`. The local admin page
returns 200 and includes the review form, exact-name registration confirmation,
and all five media roles. External unauthenticated access returns 401. No
WooCommerce product/order write or PROD change occurred. Rollback files are
stored at `AIControlCenterRuntime/dev-order/backups/product-intake-20261018-152525`.


## Admin cancellation, refunds, and exchanges

The order detail exposes a guarded cancellation only while fulfillment is
NOT_SHIPPED. An unpaid cancellation uses the existing serialized Woo stock
restoration receipt. A paid cancellation requires a separately approved RETURN
case before stock restoration; that action does not transfer funds or change
the payment state. The operator records the full KRW refund only after the
external transfer has actually completed and an evidence reference is supplied.

A shipped order cannot be cancelled. A refund case can be approved while the
order is in progress, but physical receipt and inspection remain delivery-gated.
Only the existing return inspection workflow restores stock, and only after a
bound provider receipt. Unknown writes remain frozen for read-only reconciliation.

An administrator may create and approve a size-exchange case while shipment is
in progress. The selected target must be a currently available variation.
Approval is case approval only; physical return, inventory movement, and
replacement shipment are not automated or represented as completed by this
release. Partial refunds and partial returns are unsupported.

The API routes remain DEV-only behind the existing Basic Auth edge and enforce
same-origin POSTs. No real order or money transfer is performed by the tests.


## Admin aftersales DEV activation

The guarded order actions were validated by 49 focused regression tests,
Python compilation, inline JavaScript syntax validation, and whitespace checks.
Immutable DEV API release 031ad09cc60887063283d2cf98e93147e6c85fa8 is active.
Read-only checks confirmed DEV health, the internal admin page (HTTP 200), and
external unauthenticated admin access (HTTP 401). The release rollback snapshot
is stored in AIControlCenterRuntime/dev-order/backups/admin-aftersales-20261019-061700.
No real order action, payment/refund transfer, or PROD change was performed.
