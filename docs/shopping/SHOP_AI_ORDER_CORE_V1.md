# SHOP_AI Commerce Order Core v1

## Status

Architecture-frozen implementation candidate.

This milestone introduces the AIControlCenter-owned read-only
commerce order domain boundary.

It does not activate WooCommerce networking.

## Architecture

`Customer / Agent`
→ `AIControlCenter`
→ `OrderService`
→ `OrderReadPort`
→ provider adapter.

AIControlCenter owns:

- order domain contracts
- order query boundaries
- order business orchestration
- future authorization and audit policy

WooCommerce remains the commerce engine.

WordPress remains the CMS.

Ubuntu owns no order business logic and no application state.

## Read-only scope

Enabled contracts:

- `LIST_ORDERS`
- `READ_ORDER`

Not enabled:

- create order
- update order
- delete order
- payment mutation
- fulfillment mutation
- refund mutation
- WooCommerce network access
- WooCommerce credential access

## Provider boundary

WooCommerce payloads are normalized at the adapter boundary.

The business layer receives only bounded `OrderSnapshot` objects.

The projection includes:

- provider order ID
- opaque provider reference
- order number
- provider status
- currency
- opaque customer reference
- bounded line items
- totals
- created/updated timestamps
- provider version

Billing, shipping, provider metadata, arbitrary JSON and the raw
provider response do not cross the domain boundary.

## Money

Provider monetary strings are normalized to `Decimal`.

Negative and non-finite values fail closed.

## Privacy

Customer data is intentionally minimized.

The first version exposes only an opaque provider customer
reference and does not expose customer names, email addresses,
phone numbers, billing addresses or shipping addresses.

## Production gate

This candidate is not production activation.

Before closeout:

1. focused tests must pass,
2. exact candidate patch must be frozen,
3. full SHOP_AI regression must pass,
4. the existing dirty worktree must remain byte-preserved,
5. code must be committed,
6. canonical documentation must be updated,
7. the branch must be pushed normally.
