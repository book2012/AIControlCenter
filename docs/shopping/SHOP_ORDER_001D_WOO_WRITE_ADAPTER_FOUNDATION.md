# SHOP_ORDER_001D — WooCommerce Write Adapter Foundation

## Status

Repository-only intercepted adapter candidate. It prepares the WooCommerce
order-create request but contains no HTTP/network implementation and no
credential-file loader.

## Provider request contract

The adapter accepts only a server-owned `ResolvedOrderCreateCommand`. The
prepared request is:

- provider: WooCommerce,
- method: POST,
- path: `/wp-json/wc/v3/orders`,
- no query parameters,
- bounded timeout,
- canonical JSON body.

The body contains only:

- explicit safe status `pending`,
- trusted numeric product ID, optional trusted numeric variation ID, quantity,
- one non-secret AIControlCenter command-digest metadata marker.

It does not contain caller price/subtotal/total/tax/currency, billing/shipping
address, email/phone, payment method, transaction ID, coupons, `set_paid`,
or provider customer ID. WooCommerce computes commerce totals from its own
catalog/business engine.

## Credential and transport boundary

Credential and transport are separate injected ports. Credential repr/str are
redacted. The prepared request contains no secret. Defaults are unavailable,
so constructing the adapter cannot perform a write.

The transport result carries an explicit disposition:

- `NOT_APPLIED`: transport/provider proves no write; maps to definitive failure,
- `APPLIED`: response must pass strict normalization and operation binding,
- `UNKNOWN`: maps to ambiguous failure and therefore durable UNKNOWN_OUTCOME.

Unexpected transport exceptions are ambiguous, not retryable.

## Response contract

An applied response must be HTTP 201, retain the exact command-digest metadata
marker, remain `pending`, and have provider customer_id `0` in this foundation.
It is normalized through the existing bounded WooCommerce OrderSnapshot
normalizer. Missing/malformed response fields, unexpected status/customer, or
operation-binding mismatch are treated as ambiguous because a provider order
may already exist.

## Explicit exclusions

No network transport implementation, write secret file, live Woo credential,
provider request, default app activation, WordPress mutation, Production DB
change, deployment or Production activation is part of 001D.

Next: validate this adapter through the existing OrderCreateService and durable
UNKNOWN_OUTCOME ledger using only intercepted fake transport. A real HTTP
transport and authenticated non-PROD write remain separately gated.
## Canonical implementation evidence

- Implementation: `d419eb932917c18a2dbd60acdb98e6b8847242e6`.
- Order/write focused regression: **146 passed, 1 warning**.
- Existing customer/session security regression: **244 passed, 1 warning**.
- Python compile, zero-network, no-secret-loader and default-app isolation: PASS.
- No credential materialization or provider network invocation occurred.
