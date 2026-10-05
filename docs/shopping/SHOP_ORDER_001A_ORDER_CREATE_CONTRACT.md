# SHOP_ORDER_001A — Order Create Contract Foundation

## Status

Repository-only implementation candidate.

This milestone introduces a closed AIControlCenter-owned order-create command,
an explicit provider-neutral write port, and claim-before-write application
orchestration. It does not enable a provider writer or any runtime mutation.

## Architecture

Future path:

`trusted customer/session authority`
→ `AIControlCenter OrderCreateCommand`
→ `durable operation coordinator`
→ `OrderCreateService`
→ `OrderCreatePort`
→ `separately reviewed WooCommerce writer`.

The 001A code stops before the last two production-capable boundaries: there is
no concrete WooCommerce writer and the only coordinator is explicitly
`production_safe = False` for tests.

## Closed customer intent

The customer command contains only:

- opaque existing `CustomerId`,
- canonical product ID, optional variation ID, and quantity,
- idempotency key,
- correlation ID,
- audit reference,
- UTC request time.

The client has no authority to submit:

- price, subtotal, total, tax or currency,
- coupon or discount truth,
- billing/shipping address, email or phone,
- payment credentials or payment state,
- provider metadata or raw WooCommerce JSON.

Those facts must be resolved later from trusted server-side authorities.

## Idempotency and failure semantics

The operation key is claimed before a future provider writer is invoked.

- exact completed replay returns the prior result without invoking the writer,
- same key with another immutable command digest is rejected,
- in-flight duplicate is rejected,
- provider/contract failure becomes terminal and is not automatically retried.

The in-memory coordinator is test-only and is not a Production durability
mechanism. Production activation requires a durable Mac Control Plane ledger
and explicit unknown-outcome/reconciliation semantics before network writes.

## Explicit exclusions

001A adds no:

- WooCommerce POST/PUT/PATCH/DELETE,
- WooCommerce write credentials,
- API or Agent create-order tool activation,
- cart or checkout route,
- payment/refund/fulfillment mutation,
- WordPress change,
- database migration,
- Colima/Caddy/runtime change,
- Production activation.

## Next gate

After focused and regression validation, 001B should design the durable order
operation ledger and trusted customer/session authorization binding. A concrete
WooCommerce writer remains later and separately gated.
