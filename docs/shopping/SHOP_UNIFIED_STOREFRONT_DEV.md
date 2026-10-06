# DEV unified storefront order and after-sales UX

## Scope
DEV customer commerce is now presented inside the agachichi storefront instead of separate order and return pages. The governed order/phone/checkout/after-sales APIs remain isolated under the existing internal DEV routes; only the customer-facing presentation is unified.

## Product detail flow
Five allowlisted DEV storefront products render an in-page commerce panel on `/homepage/storefront/product/{demo_id}`. The panel lazy-loads authoritative WooCommerce variants and stock from `GET /__order-dev/chat/embed/{demo_id}`, then reuses the existing guest-chat JavaScript for inquiry, cart, phone verification, Korean address search, delivery review and explicit order confirmation.

Non-orderable demo products remain preview-only and do not receive the commerce panel. The homepage and search keep their existing catalog presentation and expose a `내 주문` navigation entry.

## Customer after-sales flow
`/homepage/storefront/my-orders` is the customer-facing order history, return and size-exchange page. It reuses the existing phone verification/session boundary and the existing after-sales APIs. The legacy `/dev-order/my-orders` route now redirects to the storefront path.

Return and size-exchange eligibility remains server-authoritative: operator-confirmed order, recorded delivery completion, within 14 days, no active case, and available replacement variation for size exchange. Attachments remain private JPEG/PNG/WebP files with the existing limits.

## Architecture
- Homepage owns customer presentation only.
- AIControlCenter order runtime remains authority for phone verification, checkout preparation, order confirmation, customer after-sales and Telegram/operator workflow.
- WooCommerce remains authoritative for catalog/variant/stock facts.
- No payment refund, carrier booking or PROD mutation is introduced.

## Validation before live activation
- Storefront integration regression: 132 passed.
- Guest/order/after-sales/admin regression: 41 passed.
- Existing isolated real Chrome guest order E2E still passed with no external provider calls and no PROD mutation.
- JavaScript syntax, Python compile and `git diff --check` passed.

## Customer routes
- Storefront: `/homepage/storefront`
- Product: `/homepage/storefront/product/{demo_id}`
- My orders / return / exchange: `/homepage/storefront/my-orders`

Legacy customer-facing DEV order routes remain compatibility redirects only; internal `__order-dev` APIs remain private implementation boundaries.
