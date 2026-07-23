# Shopping Platform Ownership Matrix

## Status

This document defines system-of-record and ownership boundaries.

## Ownership Matrix

| Resource | System of record | Platform owner | Sprint 1 access |
| --- | --- | --- | --- |
| platform_policy | AIControlCenter | AIControlCenter | read_write |
| operational_approval | AIControlCenter | AIControlCenter | read_write |
| audit_event | AIControlCenter | AIControlCenter | append_only |
| canonical_product_schema | AIControlCenter | AIControlCenter | define_only |
| published_cms_content | WordPress | WordPress | read_only |
| commerce_product | WooCommerce | WooCommerce | read_only |
| price | WooCommerce | WooCommerce | read_only |
| inventory | WooCommerce | WooCommerce | read_only |
| order | WooCommerce | WooCommerce | read_only_minimum_data |
| customer_commerce_record | WooCommerce | WooCommerce | read_only_pii_minimized |
| recommendation | AIControlCenter | AIControlCenter | compute_no_publish |
| shopping_workflow_state | AIControlCenter | AIControlCenter | internal_only |
| adapter_identity_mapping | AIControlCenter | AIControlCenter | read_model |

## Ownership Rules

### AIControlCenter

AIControlCenter owns governance, authorization, approvals, audit events, schemas, recommendation state, workflow state, notifications, automation, and deployment control.

### WordPress

WordPress owns published CMS content as an external storage engine.

WordPress does not own Shopping governance, recommendation policy, authorization, or workflow orchestration.

### WooCommerce

WooCommerce owns commerce records such as products, prices, inventory, orders, and commerce customer records.

WooCommerce does not own platform policy, approvals, recommendations, audit governance, or customer automation policy.

### Ubuntu

Ubuntu may provide stateless infrastructure and inactive backup copies.

Ubuntu must not own Shopping business logic, live application state, authorization, workflow state, or Production Shopping databases.

## Data Minimization

Customer and order projections must exclude data not required for approved read-only use cases.

The platform must not persist passwords, payment tokens, raw credentials, webhook secrets, unnecessary addresses, unnecessary messages, or unbounded vendor payloads.
