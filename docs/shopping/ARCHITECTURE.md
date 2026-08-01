# AI Shopping Platform Architecture

## Purpose

AI Shopping Platform is a service domain inside AIControlCenter.

It is not a traditional WordPress shopping site implementation.

## Responsibility Model

### WordPress

- Shopping homepage
- Product presentation
- Category presentation
- Blog
- Landing pages
- CMS

### WooCommerce

- Products
- Orders
- Customers
- Inventory
- Coupons
- Payment and commerce state

### AIControlCenter

- Shopping business logic
- Shopping API
- AI workflows
- Approval policies
- Recommendations
- Pricing analysis
- Automation policies
- Audit status
- Operational validation

### AI Agent

- Product draft generation
- SEO draft generation
- Product description generation
- Category recommendation
- Review summary generation
- Approved update execution

### n8n

- External workflow execution
- Email
- Notifications
- Webhooks
- Scheduled integrations

## Runtime Model

Current runtime: Virtual development environment

Production target: Mac mini M4

The same application code must be used in development and production.

Environment differences must be configuration-only.

## Worker Boundary

Ubuntu remains an infrastructure worker.

Shopping business logic, AI logic and application state must not be
implemented on Ubuntu.

## Safe Update Workflow

AI draft
to policy validation
to human approval
to controlled WooCommerce REST update
to WordPress presentation
to audit event

## Initial Safety Mode

- Read-only
- Approval required
- AI execution disabled
- Automation disabled

<!-- SHOPPING_M4_START -->

## M4 Architecture

AIControlCenter
    |
    +-- ShoppingSettings
    |
    +-- ShoppingService
    |
    +-- Adapter Factory
            |
            +-- MockCommerceCatalogAdapter
            |
            +-- WooCommerceRESTAdapter
                    |
                    +-- WordPress and WooCommerce

### URL Separation

- Canonical signing URL: external WordPress URL
- Internal connection URL: localhost WordPress port
- External development UI: http://bokstory.iptime.org:58088
- Internal REST connection: http://127.0.0.1:8088

### Security

- WooCommerce API Key is read-only.
- Secret files are excluded from Git.
- systemd runtime Secret permissions are 600 root:root.
- Production requires a user-owned domain and HTTPS.
- iptime.org CAA policy prevents certificate issuance for the current DDNS hostname.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## M5 Storefront Architecture

WooCommerce
    |
    v
WooCommerceRESTAdapter
    |
    v
ShoppingService
    |
    +-- Featured Products
    +-- Search
    +-- Categories
    +-- Image URL normalization
    |
    v
AIControlCenter REST API
    |
    v
AI Shopping Storefront Plugin
    |
    +-- API Client
    +-- Cache
    +-- Shortcodes
    +-- Renderer
    +-- CSS
    |
    v
WordPress Presentation Layer

### WordPress Responsibilities

- User input rendering
- Input sanitization
- API request forwarding
- Short-lived response cache
- HTML and CSS rendering
- Error fallback messages

### Forbidden WordPress Responsibilities

- Product recommendation decisions
- Price calculation
- Inventory policies
- AI provider calls
- Order automation
- Approval workflows
<!-- SHOPPING_M5_END -->

<!-- SHOP-00-CLOSEOUT:BEGIN -->
## SHOP-00 Shopping Platform Reprioritization

SHOP-00 is closed.

Repository inventory and regression validation confirmed that the
existing Shopping Platform Foundation and Shopping External Read
Integration are already part of the current branch history.

Existing capabilities designated for reuse:

- WooCommerce external read adapter
- WooCommerce transport and normalization
- WordPress CMS adapter
- normalized product snapshot JSON contracts
- read authorization and deny-by-default policy
- schema validation and drift monitoring
- adapter health monitoring
- nine read-only Shopping API routes
- Orange Coco storefront

The former SHOP-01 WooCommerce Read Adapter scope is therefore
`CLOSED_BY_EXISTING_SRI`.

The first incomplete product capability is:

`SHOP-01_PRODUCT_MANAGEMENT_READ_MODEL_AND_DASHBOARD`

Architecture invariants:

- Storefront and management Dashboard are separate surfaces.
- Dashboard consumes AIControlCenter APIs only.
- Dashboard does not call WooCommerce directly.
- WooCommerce remains the Commerce Engine.
- WordPress remains the CMS.
- AIControlCenter owns business workflow and normalized management
  views.
- SHOP-01 is read-only.
- Product draft, approval and controlled write remain separate tasks.
- No Shopping business logic is placed on Ubuntu.
- Production writes remain `NOT_AUTHORIZED`.


Management read path:

Dashboard
→ AIControlCenter Dashboard API
→ Shopping management read model
→ existing Shopping snapshot queries
→ existing WooCommerce read adapter

The management read model may aggregate and present existing Shopping
contracts but may not become a second source of product truth.
<!-- SHOP-00-CLOSEOUT:END -->

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

<!-- SHOP-01E3C-SECURE-RUNTIME:BEGIN -->
## SHOP-01E3C Secure WooCommerce Read Runtime

AIControlCenter now provides a reusable secure runtime loader for the
existing WooCommerce read-only credential file.

The loader validates:

- a regular non-symlink credential file
- current-user ownership
- file mode `0600`
- direct parent mode `0700`
- exact credential keys
- read-only WooCommerce API permission

Credential values are not copied into Git, LaunchAgent plist files or
the process environment.

Runtime selection uses the non-secret profile:

`AICONTROLCENTER_SHOPPING_PROFILE=woocommerce_read_only`

The profile is not enabled persistently by this task. Persistent
LaunchAgent activation requires a separate operational authorization.

The canonical WooCommerce target currently has zero products and one
product category. This is a valid empty Commerce Engine state, not an
adapter failure.

The next active task is:

`SHOP-02A_PRODUCT_DRAFT_WORKFLOW_ARCHITECTURE`
<!-- SHOP-01E3C-SECURE-RUNTIME:END -->

## SHOP-02A Aggregate

ProductDraft is an AIControlCenter-owned proposal made of immutable revisions derived from WooCommerce snapshots. Validation is deterministic, approval is human-only and revision-bound, and deployment intent is non-executable. `DEPLOYED` is intentionally absent. WooCommerce remains source of truth and Ubuntu owns no state or logic.
