# AI Shopping Platform

## Status

Development Environment: Virtual

Production Target: Mac mini M4

Current Mode: Read-only

## Purpose

AI Shopping Platform is a production service layer running inside
AIControlCenter.

It is not implemented as WordPress business logic.

## Responsibilities

### WordPress

- Shopping homepage
- Product and category presentation
- Content management
- Blog and landing pages

### WooCommerce

- Products
- Orders
- Customers
- Inventory
- Coupons
- Commerce and payment state

### AIControlCenter

- Shopping business logic
- API control plane
- AI product workflow
- Approval workflow
- Recommendation
- Pricing analysis
- Automation policy
- Audit and operational status

### AI Agent

- Product draft generation
- SEO draft generation
- Product description generation
- Category recommendation
- Review summaries
- Approved update execution

### n8n

- External automation
- Notifications
- Email
- Webhook execution
- Scheduled workflows

## Safety Model

The initial platform is read-only.

AI and automation execution are disabled by default.

Write operations will be introduced only after:

1. Read-only monitoring is stable.
2. API contracts are tested.
3. Approval workflow is implemented.
4. Audit logging is implemented.
5. Rollback is validated.

<!-- SHOPPING_M4_START -->

## M4 — Live WooCommerce Control Plane

Status: Implementation complete. Production Gate closeout in progress.

### Runtime

- Control Plane: AIControlCenter
- CMS: WordPress
- Commerce Engine: WooCommerce
- Development runtime: Ubuntu virtual validation environment
- Production target: Mac mini M4
- External development URL: http://bokstory.iptime.org:58088
- Commerce write mode: Read-only

### Implemented

- Shopping domain
- Product list API
- Product detail API
- Category API
- Integration status API
- Mock Commerce Adapter
- WooCommerce REST Adapter
- Adapter Factory
- Environment-driven Adapter selection
- HTTP OAuth 1.0a development authentication
- HTTPS Basic Authentication support
- systemd EnvironmentFile integration
- Docker Compose WordPress and MariaDB runtime

### Architecture Rule

WordPress and WooCommerce do not own AI or business logic.
AIControlCenter remains the single Shopping Control Plane.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## M5 — AI Shopping Storefront Foundation

Status: Implementation complete. Production Gate and Git closeout in progress.

### Implemented

- Featured Products API
- Product Search API
- Category navigation
- Minimum and maximum price filters
- Stock availability filter
- Search pagination
- Product image URL support
- Image placeholder fallback
- Modular WordPress Presentation Plugin
- WordPress shortcode
- AIControlCenter API client
- WordPress transient cache
- External Storefront page

### Storefront URL

http://bokstory.iptime.org:58088/ai-shopping/

### Architecture Rule

AIControlCenter owns product selection, search, filtering, validation, and future recommendation logic.

WordPress only renders AIControlCenter responses.
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


Next implementation:

`SHOP-01_PRODUCT_MANAGEMENT_READ_MODEL_AND_DASHBOARD`
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
