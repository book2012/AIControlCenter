# SHOP-00 — Shopping Platform Reprioritization

## Status

CLOSED

## Decision

Reuse the existing Shopping Platform Foundation and Shopping External
Read Integration.

Do not implement another WooCommerce read adapter.

The first incomplete vertical capability is the Product Management Read
Model and Dashboard.

## Existing Capability Baseline

- WooCommerce external read: complete
- normalized product JSON: complete
- schema and health observability: complete
- Shopping read API: complete
- Storefront: present
- Product management Dashboard: absent
- Product draft implementation: absent; documentation only
- Human approval implementation: absent; documentation only
- Shopping mutation API routes: none
- Controlled WooCommerce write: not authorized

## Service Boundaries

WordPress owns CMS content.

WooCommerce owns products, pricing, inventory, customers and orders.

AIControlCenter owns normalized management views, policy,
orchestration, approval workflow and future AI-enhanced business logic.

The Storefront is customer-facing.

The Product Management Dashboard is operator-facing.

## Next Task

`SHOP-01_PRODUCT_MANAGEMENT_READ_MODEL_AND_DASHBOARD`

SHOP-01 is read-only and must reuse the existing Dashboard framework,
Shopping API contracts and WooCommerce read adapter.
