# SHOP-01C — Dashboard JSON Integration

## Status

IMPLEMENTED

## Decision

Expose the Shopping management read model through the existing
`GET /dashboard` JSON projection.

## Response Section

`shopping_management`

## Success State

The section contains:

- service status
- catalog and inventory summary
- normalized products
- health
- readiness
- capability state
- integration state

## Failure State

Shopping dependency failures return a deterministic read-only
`UNAVAILABLE` envelope.

The Dashboard itself remains available.

## Boundaries

The integration adds:

- no new route
- no new frontend framework
- no product persistence
- no WooCommerce adapter import
- no Shopping mutation method
- no Ubuntu responsibility

## Next Task

`SHOP-01D_VALIDATION_AND_CLOSEOUT`
