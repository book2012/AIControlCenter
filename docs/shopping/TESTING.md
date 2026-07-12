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
