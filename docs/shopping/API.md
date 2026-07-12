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

## Product Catalog Endpoints

GET /shopping/products

Query parameters:

- page
- page_size

The endpoint returns paginated product records and total count.

GET /shopping/products/{product_id}

The endpoint returns one product record.

Unknown product identifiers return HTTP 404.

The current implementation uses MockCommerceCatalogAdapter.

The API contract will remain stable when the adapter is replaced by
WooCommerceRESTCatalogAdapter.

## Product Catalog Endpoints

GET /shopping/products

Query parameters:

- page
- page_size

The endpoint returns paginated product records and total count.

GET /shopping/products/{product_id}

The endpoint returns one product record.

Unknown product identifiers return HTTP 404.

The current implementation uses MockCommerceCatalogAdapter.

The API contract will remain stable when the adapter is replaced by
WooCommerceRESTCatalogAdapter.

## Product Catalog Endpoints

GET /shopping/products

Query parameters:

- page
- page_size

The endpoint returns paginated product records and total count.

GET /shopping/products/{product_id}

The endpoint returns one product record.

Unknown product identifiers return HTTP 404.

The current implementation uses MockCommerceCatalogAdapter.

The API contract will remain stable when the adapter is replaced by
WooCommerceRESTCatalogAdapter.
