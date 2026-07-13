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
