# Shopping Platform Testing

## Current Test File

tests/test_shopping_api.py

## Current Coverage

- Shopping health endpoint
- Shopping readiness endpoint
- Shopping capabilities endpoint
- Read-only defaults
- Unsupported write mode
- Disabled Shopping service behavior

## Targeted Test Command

.venv/bin/python -m pytest tests/test_shopping_api.py -q

## Full Regression Test Command

.venv/bin/python -m pytest -q

## Production Gate

A Shopping Sprint is complete only when:

- Python compilation passes
- Targeted tests pass
- Full regression tests pass
- Required OpenAPI routes exist
- Safe defaults are validated
- Documentation is updated
- Git diff check passes
- Git working tree is clean after commit

## Known Warning

FastAPI TestClient currently reports a Starlette deprecation warning.

This warning does not currently fail tests.

Dependency changes must be handled in a separate regression Sprint.

<!-- SHOPPING_M4_START -->

## M4 Testing

Required Shopping tests:

.venv/bin/python -m pytest   tests/test_shopping_api.py   tests/test_shopping_catalog.py   tests/test_shopping_categories.py   tests/test_shopping_settings.py   tests/test_shopping_factory.py   tests/test_woocommerce_adapter.py   -q

Production Gate:

.venv/bin/python -m pytest -m "not integration" -q

Tests must not inherit live WooCommerce settings.
API unit tests explicitly use the Mock adapter.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## M5 Testing

### Shopping Tests

.venv/bin/python -m pytest   tests/test_shopping_api.py   tests/test_shopping_catalog.py   tests/test_shopping_categories.py   tests/test_shopping_featured.py   tests/test_shopping_search.py   tests/test_shopping_settings.py   tests/test_shopping_factory.py   tests/test_woocommerce_adapter.py   -q

### Full Non-integration Suite

.venv/bin/python -m pytest -m "not integration" -q

### PHP Syntax Validation

docker exec shopping-wordpress php -l   /var/www/html/wp-content/plugins/ai-shopping-storefront/ai-shopping-storefront.php

All files in the plugin includes directory must also pass php -l.

### External Validation

- Storefront HTTP 200
- Search form exists
- Search result section exists
- Product image or Placeholder exists
- No recent PHP Fatal or Parse Error
<!-- SHOPPING_M5_END -->

<!-- SHOP-01D-CLOSEOUT:BEGIN -->
## SHOP-01 Product Management Read Model and Dashboard

SHOP-01 is closed.

Completed capabilities:

- deterministic Shopping management read model
- product and inventory summary
- normalized operator-facing product list
- health, readiness, capability and integration projection
- optional `shopping_management` Dashboard dependency
- `GET /dashboard.shopping_management` JSON projection
- deterministic `UNAVAILABLE` failure envelope
- internal error-detail suppression
- source and result mutation isolation
- existing Dashboard compatibility
- default-configuration read-only operational observation

Architecture boundaries remain unchanged:

- WooCommerce remains the Commerce Engine.
- WordPress remains the CMS.
- AIControlCenter owns management projections and workflow logic.
- The Dashboard does not import WooCommerce adapters.
- No local product truth was created.
- No Shopping mutation route was added.
- Production writes remain `NOT_AUTHORIZED`.

The next active task is:

`SHOP-02A_PRODUCT_DRAFT_WORKFLOW_ARCHITECTURE`
<!-- SHOP-01D-CLOSEOUT:END -->

<!-- SHOP-01E2-COMPATIBILITY-ADAPTER:BEGIN -->
## SHOP-01E2 Shopping Product Compatibility Adapter

The default Mock catalog returned the legacy `Product` contract while
the management read model required the canonical product projection.

A dedicated application adapter now translates the existing
`ShoppingService` result into the canonical management contract.

Explicit mappings:

- `id` to `product_id`
- `image_url` to `image_urls`
- `Decimal` price to a JSON number

Missing SKU, inventory quantity, URL and updated timestamp values
remain null. The adapter does not synthesize unknown Commerce data.

The canonical management contract was not weakened. The Dashboard
continues to have no direct WooCommerce dependency.

The next task is:

`SHOP-01E3_WOOCOMMERCE_READ_ONLY_CONFIGURATION`
<!-- SHOP-01E2-COMPATIBILITY-ADAPTER:END -->
