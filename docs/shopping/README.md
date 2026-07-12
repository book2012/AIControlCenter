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
