# SHOP-01B — Shopping Management Read Model

## Status

IMPLEMENTED

## Decision

Create a deterministic read-only application projection between the
existing Shopping service and the existing Dashboard JSON API.

## Inputs

- Shopping health
- Shopping readiness
- Shopping capabilities
- Shopping integration status
- paginated normalized products

## Outputs

- read-only operating mode
- aggregate product and inventory summary
- deterministic product list
- health and readiness state
- capability and adapter state

## Boundaries

The module does not:

- import WooCommerce adapters
- perform network calls
- persist data
- create local product truth
- expose an API route
- register with Dashboard
- provide product mutation methods

## Next Task

`SHOP-01C_DASHBOARD_JSON_INTEGRATION`
