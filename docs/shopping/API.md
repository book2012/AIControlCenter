# Shopping API

## Base Path

/shopping

## Current Endpoints

GET /shopping/health

Returns the Shopping Platform runtime status.

GET /shopping/readiness

Returns whether the Shopping Platform is safely configured and ready.

GET /shopping/capabilities

Returns currently enabled Shopping capabilities.

## Current Safe Capabilities

- Catalog read enabled
- Catalog write disabled
- AI execution disabled
- Automation execution disabled
- Human approval required

## Planned Read-only Endpoints

GET /shopping/products

GET /shopping/products/{product_id}

GET /shopping/integrations

GET /shopping/sync/status

POST /shopping/sync/validate

## Write Policy

Write endpoints must not be enabled until authentication, approval,
audit logging, idempotency and rollback controls are implemented.
