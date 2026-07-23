# Shopping Platform Context Map

## Status

- Control Plane: AIControlCenter
- CMS: WordPress
- Commerce engine: WooCommerce
- Worker: Ubuntu
- Sprint 1: Read-only

## Logical Flow

```text
Homepage / Dashboard / AI Agent / n8n
                    |
                    v
        AIControlCenter Shopping API
                    |
                    v
      Governance and Application Layers
                    |
                    v
            Domain Port Interfaces
                    |
          +---------+---------+
          |                   |
          v                   v
 WordPress Adapter     WooCommerce Adapter
          |                   |
          v                   v
 Headless CMS API      Commerce REST API
```

## Dependency Direction

```text
API
→ Application
→ Domain and Ports
← Adapters
```

Domain and application modules must not import WordPress or WooCommerce SDK types.

Vendor payloads remain inside adapter DTOs and are translated into canonical Shopping models.

## Permitted Relationships

- Dashboard calls AIControlCenter Shopping APIs.
- n8n calls approved AIControlCenter workflow APIs.
- AIControlCenter calls WordPress through `CmsReadPort`.
- AIControlCenter calls WooCommerce through `CommerceReadPort`.
- Governance policy is evaluated before operation dispatch.
- Audit evidence is owned by AIControlCenter.

## Prohibited Relationships

- Dashboard directly calling WordPress business logic.
- n8n directly performing WooCommerce Production writes.
- WordPress plugins accessing AIControlCenter databases.
- AIControlCenter directly accessing external databases.
- Adapters making platform policy decisions.
- Ubuntu hosting Shopping state or business logic.

## Anti-Corruption Layer

The adapter layer isolates external identifiers, vendor status values, pagination, authentication, errors, optional fields, and API version differences.

Only canonical `shopping.v1` models cross from adapters into the application layer.
