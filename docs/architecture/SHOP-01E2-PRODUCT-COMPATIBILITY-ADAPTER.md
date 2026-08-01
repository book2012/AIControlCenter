# SHOP-01E2 — Product Compatibility Adapter

## Status

IMPLEMENTED

## Problem

`ShoppingService.list_products()` returned legacy product fields:

- `id`
- `image_url`
- `Decimal` price

The management projection required:

- `product_id`
- `image_urls`
- JSON-safe price values

## Decision

Introduce `ShoppingServiceManagementSourceAdapter` in the Shopping
application layer.

## Mapping

- `id` → `product_id`
- `image_url` → `image_urls`
- `Decimal` → JSON number

Unknown SKU, inventory, URL and timestamp values remain null.

## Boundaries

The adapter:

- performs no network operation
- performs no persistence
- imports no WooCommerce implementation
- creates no product truth
- exposes no write method
- does not weaken the canonical management contract

## Next Task

`SHOP-01E3_WOOCOMMERCE_READ_ONLY_CONFIGURATION`
