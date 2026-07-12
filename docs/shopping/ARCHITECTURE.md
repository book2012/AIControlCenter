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
