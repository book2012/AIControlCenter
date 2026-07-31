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

<!-- SHOPPING_M4_START -->

## M4 Shopping API

### Endpoints

- GET /shopping/health
- GET /shopping/readiness
- GET /shopping/capabilities
- GET /shopping/integrations
- GET /shopping/products
- GET /shopping/products/{product_id}
- GET /shopping/categories

### Product Query Parameters

- page: minimum 1
- page_size: 1 to 100

### Adapter Selection

- SHOPPING_CATALOG_ADAPTER=mock
- SHOPPING_CATALOG_ADAPTER=woocommerce

### Read-only Policy

M4 exposes catalog read operations only.
Product, category, order, customer, pricing, and inventory writes remain disabled.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## M5 Storefront APIs

### Featured Products

GET /shopping/featured-products

Query:

- limit: 1 to 20

Response includes:

- items
- total
- available_catalog_total
- limit
- strategy

Current deterministic strategy:

in_stock_first

### Product Search

GET /shopping/search

Query parameters:

- q
- category
- minimum_price
- maximum_price
- in_stock
- page
- page_size

AIControlCenter validates price ranges and pagination.

### Image Field

Product responses include:

image_url

The value is null when WooCommerce has no representative image.
<!-- SHOPPING_M5_END -->

<!-- SHOP-01B-MANAGEMENT-READ-MODEL:BEGIN -->
## SHOP-01B Shopping Management Read Model

SHOP-01B adds a pure read-only application projection for
operator-facing product management data.

The projection consumes the existing `ShoppingService` boundary and
produces deterministic JSON-safe output containing:

- service health
- readiness
- read/write capability state
- adapter integration state
- catalog totals
- in-stock and out-of-stock counts
- inventory quantity totals
- normalized product list fields

The module performs no network calls, persistence, product mutation,
WooCommerce imports or Dashboard registration.

The Product Management Dashboard remains a projection of WooCommerce
truth through AIControlCenter. It is not a second product database.

The next task is `SHOP-01C_DASHBOARD_JSON_INTEGRATION`.
<!-- SHOP-01B-MANAGEMENT-READ-MODEL:END -->

<!-- SHOP-01C-DASHBOARD-INTEGRATION:BEGIN -->
## SHOP-01C Dashboard JSON Integration

The existing `GET /dashboard` projection now includes an optional
`shopping_management` section.

The section is generated through the completed Shopping management
read model and remains read-only.

Failure isolation rules:

- Shopping configuration failure does not fail the Dashboard.
- Shopping catalog failure does not fail the Dashboard.
- Internal exception details are never exposed.
- An unavailable Shopping dependency returns a deterministic
  `UNAVAILABLE` envelope.
- Existing Dashboard behavior is preserved when no Shopping
  projection is injected.

The Dashboard imports no WooCommerce adapter and creates no local
product truth.

The next task is `SHOP-01D_VALIDATION_AND_CLOSEOUT`.
<!-- SHOP-01C-DASHBOARD-INTEGRATION:END -->

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
