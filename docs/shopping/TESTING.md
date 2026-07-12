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
