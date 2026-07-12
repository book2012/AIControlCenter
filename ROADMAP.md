# Roadmap

## Complete

- Core Runtime
- Dashboard
- BrainAgent
- Telegram
- Conversation Memory
- SQLite
- Command Router

## Current

Doctor

## Next

Logs

Backup Verify

Worker Health

Backup Execute

Homepage

Mac mini Production

## Sprint 21

- [ ] Brain Scheduler
- [ ] Heartbeat
- [ ] Job Registry
- [ ] Scheduler API
- [ ] Job Runner


## Sprint 22

- [x] Memory Manager
- [x] Working Memory
- [x] Long-term Memory
- [x] Memory API
- [x] Telegram Memory Commands

## Sprint 23

- [ ] Knowledge Registry
- [ ] Markdown Loader
- [ ] Knowledge Search
- [ ] Knowledge API
- [ ] Telegram /knowledge
- [ ] BrainAgent Knowledge Context

<!-- AI_SHOPPING_PLATFORM_START -->
## AI Shopping Platform Roadmap

### S0 Control Plane Baseline

Status: In Progress

- Shopping domain bootstrap
- Health API
- Readiness API
- Capabilities API
- Virtual environment tests
- Documentation
- Git Production Gate

### S1 Read-only Product Catalog

- Commerce Catalog Port
- Mock Product Adapter
- Product list API
- Product detail API
- Pagination
- Schema validation

### S2 WordPress and WooCommerce Virtual Environment

- WordPress container
- WooCommerce installation
- Test catalog
- REST API credentials
- AIControlCenter read-only adapter

### S3 AI Product Workflow

- Product generator
- SEO writer
- Product description generator
- Category generator
- Human approval
- Audit history

### S4 Controlled Publishing

- Authentication
- Authorization
- Idempotency
- Controlled WooCommerce writes
- Rollback
- Audit logging

### S5 Shopping Homepage

- WordPress theme
- Homepage
- Category pages
- Product pages
- Shopping Assistant integration

### S6 Production Hardening

- ARM64 validation
- Mac mini deployment
- Restart recovery
- Monitoring
- Backup
- Runbook
<!-- AI_SHOPPING_PLATFORM_END -->

<!-- SHOPPING_M4_START -->

## Shopping Platform Roadmap

### M4 — Live WooCommerce Control Plane

- [x] Shopping domain bootstrap
- [x] WordPress runtime
- [x] WooCommerce runtime
- [x] Product API
- [x] Category API
- [x] Integration API
- [x] Adapter Factory
- [x] systemd Secret integration
- [ ] Final Production Gate and Git closeout

### M5 — Shopping Experience

- [ ] Shopping Homepage
- [ ] Product detail experience
- [ ] Shopping Dashboard widgets
- [ ] Search and filtering

### M6 — AI Commerce

- [ ] AI Product Generator
- [ ] AI SEO Writer
- [ ] AI Category Generator
- [ ] AI Price Recommendation
- [ ] Approval workflow

### Production Blocker

A user-owned domain is required for public HTTPS.
The current ipTIME DDNS hostname cannot receive a certificate because of its parent-domain CAA policy.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## Shopping Platform Service Roadmap

### M5 — AI Shopping Storefront Foundation

- [x] Featured Products API
- [x] Product Search API
- [x] Category Navigation
- [x] Price Filters
- [x] Stock Filter
- [x] Pagination
- [x] Product Image Support
- [x] Placeholder Fallback
- [x] WordPress Presentation Plugin
- [x] External Storefront
- [ ] Final Documentation and Git Closeout

### M6 — AI Product Generation

- [ ] Product Draft Model
- [ ] AI Product Generator
- [ ] AI Description Writer
- [ ] AI SEO Writer
- [ ] AI Category Suggestion
- [ ] Approval Workflow
- [ ] Controlled WooCommerce Write
- [ ] Audit Log

### M7 — Shopping Operations

- [ ] Order Read Integration
- [ ] Customer Read Integration
- [ ] Inventory Monitoring
- [ ] Shopping Dashboard
- [ ] Notifications
- [ ] n8n Automation
<!-- SHOPPING_M5_END -->
