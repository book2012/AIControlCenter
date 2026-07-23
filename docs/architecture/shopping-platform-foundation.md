# Shopping Platform Foundation

## Status

- Milestone: Shopping Platform Foundation
- Control Plane: AIControlCenter
- Package root: `core/shopping`
- Sprint 1 mode: Read-only
- Production writes: Disabled
- Product writes: Disabled
- Customer writes: Disabled
- Order writes: Disabled

## Purpose

The Shopping Platform is a business platform owned by AIControlCenter.

It is not a WordPress plugin, a WooCommerce customization layer, or an Ubuntu application.

AIControlCenter owns governance, policy, authorization, audit, workflow, recommendations, notifications, customer automation, and deployment control.

WordPress is a headless CMS. WooCommerce is a replaceable commerce engine.

## Architectural Principles

1. AIControlCenter is the single Shopping Control Plane.
2. WordPress is a headless CMS only.
3. WooCommerce is a replaceable commerce engine only.
4. External systems integrate through adapters and REST/JSON contracts.
5. Ubuntu remains a stateless infrastructure worker.
6. Monitoring precedes validation.
7. Validation precedes reconciliation.
8. Reconciliation precedes approved write operations.
9. Sprint 1 exposes no product, customer, or order write capability.
10. Direct WordPress and WooCommerce database access is prohibited.

## Package Layout

- `core/shopping/domain`
- `core/shopping/application`
- `core/shopping/ports`
- `core/shopping/adapters`
- `core/shopping/contracts`
- `core/shopping/governance`
- `core/shopping/observability`

## Bounded Contexts

| Context | Owner | Sprint 1 mode |
| --- | --- | --- |
| shopping_governance | AIControlCenter | active |
| catalog | AIControlCenter | read_only |
| commerce_projection | AIControlCenter | read_only |
| content | AIControlCenter | read_only |
| order_intelligence | AIControlCenter | read_only_minimum_data |
| customer_intelligence | AIControlCenter | read_only_pii_minimized |
| recommendation | AIControlCenter | compute_only_no_publish |
| workflow | AIControlCenter | read_only_workflow |
| notification | AIControlCenter | monitoring_only |
| observability | AIControlCenter | active |

## Adapter Boundaries

### Active Sprint 1 Ports

- `CommerceReadPort`
- `CmsReadPort`
- `AdapterHealthPort`
- `SchemaDiscoveryPort`
- `SnapshotRepositoryPort`
- `PolicyDecisionPort`
- `AuditPort`

### Prohibited Sprint 1 Ports

- `CommerceWritePort`
- `CmsWritePort`
- `ProductionWebhookWritePort`

## Sprint 1 Non-Goals

- Product create, update, or delete
- Price or inventory updates
- Customer create, update, or delete
- Order create or status update
- Automatic publishing
- Direct WordPress database access
- Direct WooCommerce database access
- Direct n8n Production writes
- Ubuntu Shopping state or business logic
