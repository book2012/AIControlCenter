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
