# SHOP_ORDER_001C-A — Canonical Product Resolution

## Status

Repository-only implementation candidate. No create-order API or provider write
is activated.

## Identity correction

The public Shopping catalog contract uses bounded string product/variant IDs.
WooCommerce happens to expose numeric provider IDs as decimal strings, while
the mock/dev catalog uses IDs such as `mock-001`. Therefore the customer
OrderCreateCommand now carries canonical string catalog references only.

Provider numeric IDs are not caller authority.

## Trusted resolution

`OrderCreateCatalogResolver` is injected into OrderCreateService after the
durable operation claim and before any provider write. The concrete
`ShoppingServiceOrderCatalogResolver` reuses the existing read-only Shopping
catalog and fails closed unless:

- the returned product identity exactly matches the command reference,
- the product is in stock,
- the catalog source is WooCommerce,
- the product provider ID is a non-zero decimal string,
- an optional variation exists, is available, and has a non-zero decimal ID.

The resolver emits a server-owned `ResolvedOrderCreateCommand` containing both
the canonical references and trusted provider numeric IDs. The future writer
receives only that resolved form. Snapshot verification compares provider
numeric line identity/quantity against this trusted resolution.

Resolver failure occurs before provider write and is terminal for that consumed
idempotency key; no external write is attempted.

## Explicit exclusions

No WooCommerce POST, write credential, route, session composition, WordPress
change, runtime mutation, Production DB mutation or Production activation is
part of 001C-A.

Next: 001C-B binds the existing trusted CustomerSessionBoundary to internal
OrderCreateAuthority and exercises an isolated route/application composition
with an inert/fake writer only.

## Idempotency digest

The command digest represents only immutable customer order intent: customer ID, canonical product/variation/quantity lines, and the idempotency key. Server observability evidence (`correlation_id`, `audit_reference`, and request timestamp) is deliberately excluded from the digest so a same-session retry of the same order intent can replay even when a new request receives fresh server-side observability references. The original evidence remains immutable in the durable ledger row created by the first claim.
