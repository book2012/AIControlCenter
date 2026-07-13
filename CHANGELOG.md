# CHANGELOG

## v0.9.0

Added

- Telegram Brain
- Telegram Polling
- Command Router
- Status Action
- Provider Fallback
- Conversation Memory
- SQLite
- Storage Registry
- Backup Registry

## Unreleased

### Planned

- Brain Scheduler
- Internal Heartbeat
- Job Registry
- Scheduler API
- Automation Foundation


## Scheduler Foundation

- Heartbeat
- Job Registry
- Scheduler Loop
- Job Runner
- Scheduler API
- Background Service

## Sprint 21-22

Added:

- Scheduler Heartbeat
- Job Registry
- Scheduler Loop
- Job Runner
- Scheduler API
- Telegram /scheduler
- Background Scheduler Service
- MemoryManager
- Working Memory
- Long-term Memory
- Memory API
- Telegram /memory
- Memory Search
- BrainAgent Memory Context

## Knowledge Layer

- Knowledge Registry
- Markdown Loader
- Knowledge Index
- Knowledge Search
- Telegram /knowledge
- Knowledge API
- BrainAgent Knowledge Context

## Planner Agent

- PlannerAgent
- Planner API
- Telegram /plan
- PlanStore
- Plan Review

## Automation Engine

- AutomationExecutor
- SafeExecutionPolicy
- AutomationQueue
- Automation API
- Telegram /automation
- Scheduler integration

## Homepage Integration

- HomepageStatusService
- /homepage/status API
- Telegram /homepage command

## Production Hardening

- systemd Services
- Service Health
- Configuration Validation
- Graceful Shutdown
- Operations Manual

## v1.0.0

### Added

- Production-ready AIControlCenter Brain platform
- FastAPI control plane
- OpenAI and Google provider support
- Provider fallback
- BrainAgent and status actions
- Scheduler and background jobs
- Conversation, working, and long-term memory
- Knowledge indexing and search
- Planner Agent
- Safe Automation Engine
- Telegram operations interface
- Homepage status API
- systemd and launchd deployment templates
- Installation, update, and readiness automation

### Architecture

- Mac mini M4 is the final Brain runtime
- Ubuntu remains an optional storage and backup Worker
- AIControlCenter operates standalone without Ubuntu

<!-- AI_SHOPPING_PLATFORM_START -->
## 2026-07-12 AI Shopping Platform Bootstrap

### Added

- AIControlCenter Shopping domain
- Shopping health endpoint
- Shopping readiness endpoint
- Shopping capabilities endpoint
- Shopping configuration
- Shopping API schemas
- Shopping tests
- Shopping architecture documentation
- Shopping API documentation
- Shopping testing documentation
- Shopping deployment documentation
- Shopping runbook

### Safety

- Catalog writes disabled by default
- AI execution disabled by default
- Automation execution disabled by default
- Human approval required by default
- Production target set to Mac mini M4

### Validation

- Shopping targeted tests passing
- Existing API regression tests passing
- Shopping route smoke tests passing
<!-- AI_SHOPPING_PLATFORM_END -->

## 2026-07-12 API Router Cleanup

### Fixed

- Removed duplicate FastAPI router registrations
- Removed duplicate OpenAPI operation identifiers
- Added API route uniqueness regression tests

### Validation

- Shopping API routes remain available
- OpenAPI operation identifiers are unique
- Full regression suite passes

## 2026-07-12 Read-only Mock Product Catalog

### Added

- Product domain model
- Commerce Catalog Port
- Mock Commerce Catalog Adapter
- Paginated product list API
- Product detail API
- Product not-found response
- Product catalog unit and API tests

### Safety

- Product catalog remains read-only
- No WooCommerce write operations
- No AI execution
- No automation execution

## 2026-07-12 Read-only Mock Product Catalog

### Added

- Product domain model
- Commerce Catalog Port
- Mock Commerce Catalog Adapter
- Paginated product list API
- Product detail API
- Product not-found response
- Product catalog unit and API tests

### Safety

- Product catalog remains read-only
- No WooCommerce write operations
- No AI execution
- No automation execution

## 2026-07-12 Read-only Mock Product Catalog

### Added

- Product domain model
- Commerce Catalog Port
- Mock Commerce Catalog Adapter
- Paginated product list API
- Product detail API
- Product not-found response
- Product catalog unit and API tests

### Safety

- Product catalog remains read-only
- No WooCommerce write operations
- No AI execution
- No automation execution

<!-- SHOPPING_M4_START -->

## Shopping Platform M4 — Unreleased

### Added

- WooCommerce REST Adapter
- HTTP OAuth 1.0a development authentication
- HTTPS Basic Authentication support
- Adapter Factory
- Environment-driven Catalog Adapter selection
- Shopping Integration Status API
- Product Catalog API
- Product Detail API
- Category API
- WordPress and MariaDB Docker Compose runtime
- systemd Shopping EnvironmentFile support
- Shopping deployment and operations documentation

### Fixed

- Duplicate API Router registration
- WordPress Healthcheck variable escaping
- WordPress WORDPRESS_CONFIG_EXTRA Parse Errors
- Test environment leakage from live Shopping settings
- Canonical WooCommerce signing URL and internal connection URL separation

### Security

- WooCommerce API integration is read-only
- Secret files excluded from Git
- systemd runtime Secret permissions restricted
- Public HTTPS deferred until a user-owned domain is available
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## Shopping Platform M5 — Unreleased

### Added

- Featured Products API
- Product Search API
- Category, price, and stock filters
- Search pagination
- Product image URL contract
- WooCommerce representative image mapping
- Image placeholder fallback
- Modular AI Shopping Storefront Plugin
- WordPress AIControlCenter API client
- WordPress Presentation Cache
- Storefront shortcode
- Responsive Storefront CSS
- External AI Shopping page

### Fixed

- Storefront Renderer search UI integration
- Search API client query serialization
- Boolean stock parameter serialization
- WooCommerce image mapping tests
- Test helper contract inconsistencies
- Trailing whitespace and blank-line issues

### Security

- Storefront does not receive WooCommerce credentials
- WordPress calls read-only AIControlCenter endpoints
- Search input is sanitized
- Rendered output is escaped
- Business Logic remains in AIControlCenter
<!-- SHOPPING_M5_END -->

## [2026-07-13] Commit 19 - Homepage Curated Sections

### Added
- Homepage curated shopping sections
- NEW ARRIVALS
- BEST SELLERS
- TOP
- DRESS
- OUTER
- BAG
- SALE

### Changed
- Renderer supports multi-section homepage
- Homepage sections powered by Shopping Search API
- Homepage displays up to 8 products per section

<!-- AI_SHOPPING_STOREFRONT_V016_CHANGELOG -->
## 2026-07-13 — AI Shopping Storefront v0.16.0

### Added

- API-driven product detail route
- Product detail renderer and template
- Orange Coco Home v5 icons and hero asset
- Related product presentation

### Changed

- Established Orange Coco v6 as the canonical storefront UI
- Updated the storefront plugin to version 0.16.0
- Improved front-page structure and responsive layout

### Fixed

- Missing products now return HTTP 404
- Product status is set before WordPress headers render

### Removed

- Legacy `orange-coco-final.css`
- Legacy `orange-coco-final.js`
- Unused Home v4 and Home v5 CSS files
- Duplicate original hero image

### Git

- Feature commit: `a4d6098`
