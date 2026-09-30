# SHOP_AI WooCommerce Order Read Bridge v1

## Status

Implementation candidate.

This milestone connects the AIControlCenter `OrderReadPort`
boundary to the existing WooCommerce read stack without creating
a second HTTP transport, credential loader, retry authority or
provider authorization path.

## Existing provider contract

The repository already exposes:

`WooCommerceCommerceReadAdapter.get_order_summary(
    context,
    order_id
)`

The existing adapter owns the established external-read policy
boundary for:

`GET /wp-json/wc/v3/orders/{id}`

The current existing stack does not expose an equivalent
`list_orders` provider contract and the frozen external-read
policy does not expose a list-orders route.

Therefore this milestone enables only `READ_ORDER`.

`LIST_ORDERS` remains part of the Order Core domain contract but
fails closed at this provider bridge until an explicit existing
provider-list contract is introduced and reviewed.

## Architecture

`OrderService`
→ `OrderReadPort`
→ `WooCommerceExistingStackOrderReadBridge`
→ existing WooCommerce read stack.

The bridge owns no:

- HTTP client
- network authority
- credential loading
- retry authority
- provider writes

## Projection boundary

The existing WooCommerce order-summary result is passed through an
explicit injected projector before entering Order Core.

The projector must return an `OrderSnapshot`.

The bridge verifies:

- exact `OrderSnapshot` type
- provider is `woocommerce`
- provider order ID matches the requested order ID

Mismatches fail closed.

This avoids coupling Order Core directly to the legacy commerce
summary model.

## Operations

Enabled by this bridge:

- `READ_ORDER`

Provider-disabled:

- `LIST_ORDERS`

Not enabled:

- create order
- update order
- delete order
- payment mutation
- refund mutation
- fulfillment mutation

## Safety

Invalid order identifiers are rejected before the existing provider
stack is invoked.

The bridge contains no WooCommerce credential values or credential
resolution logic.

No provider network request is performed by this milestone's
candidate or focused tests.

## Next gate

After focused candidate validation:

1. freeze the exact patch,
2. apply the bridge to the real repository,
3. run the SHOP_AI file-isolated regression gate,
4. commit the code,
5. compose the bridge with the existing read-only runtime,
6. obtain one bounded non-production `READ_ORDER` live observation,
7. close canonical documentation,
8. push normally.
