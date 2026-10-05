# SHOP_ORDER_001C-B — Session-Bound Isolated Order API

## Status

Repository-only isolated composition candidate. The default FastAPI app does
not register this router.

## Trusted request path

`POST /shopping/owned-orders` candidate:

`canonical HTTPS Origin`
→ `__Host-aicc_customer` credential
→ existing `CustomerSessionBoundary.authenticate`
→ existing CSRF verification
→ internal `OrderCreateAuthority`
→ server-built `OrderCreateCommand`
→ durable ledger / canonical catalog resolver
→ injected inert/fake writer in tests.

No new authentication, cookie, session, CSRF or credential mechanism is
introduced.

## Closed client body

The request accepts only:

- canonical product ID,
- optional canonical variation ID,
- quantity,
- idempotency key.

The client cannot submit customer/session identity, price, total, tax,
currency, coupon/discount truth, billing/shipping/contact data, payment state,
provider IDs, correlation IDs, audit IDs or timestamps.

Customer/session identity comes from the existing authenticated session.
Correlation, audit and time evidence are generated server-side.

## Replay

The command digest excludes per-request observability evidence. Therefore a
same-session retry of the same idempotency key and customer intent may return
the durable prior result without another writer invocation even though the
new HTTP request receives new server correlation/audit/time evidence.

## Activation boundary

The router is intentionally not imported or included by `core.api.app`.
`get_order_create_service()` fails closed unless explicitly overridden.
Tests compose only an isolated FastAPI app, temporary SQLite ledger, read-only
catalog resolver and fake writer.

No WooCommerce write endpoint, write credential, runtime wiring, WordPress
change, Production database mutation, deployment or Production activation is
part of 001C-B.
## Canonical implementation evidence

- 001C-A: `caa2ca8f2815fb6e408c5e67552b9004bbad6ec8`.
- 001C-B: `9bd5e61a4cc25b53303b1e588bccede4a2ebcb16`.
- Order/API focused validation: **103 passed, 1 warning**.
- Existing customer/session security validation: **244 passed, 1 warning**.
- Python compile and default-app/write-secret isolation checks: PASS.
- No default route activation or provider write occurred.
