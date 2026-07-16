# AIControlCenter

AIControlCenter is the Brain of the AI Home Datacenter.

## Brain
- Mac mini M4
- AI Agents
- FastAPI
- Telegram
- Provider Manager
- BrainAgent
- Command Router

## Optional Worker
- Ubuntu
- Docker
- Storage
- Backup
- Immich
- Nextcloud
- Plex

## Telegram Commands

/status
/storage
/backup
/tasks
/help
/ask <message>

## Current Status

Core Platform is operational.

Next Sprint

- Doctor
- Logs
- Backup Verify
- Worker Health

<!-- AI_SHOPPING_PLATFORM_START -->
## AI Shopping Platform

AI Shopping Platform is a service layer inside AIControlCenter.

Current status:

- Development environment: Virtual
- Production target: Mac mini M4
- Frontend and CMS: WordPress
- Commerce engine: WooCommerce
- Business logic: AIControlCenter
- AI operations: AI Agent
- Automation execution: n8n
- Current write mode: Read-only

Shopping documentation:

- docs/shopping/README.md
- docs/shopping/ARCHITECTURE.md
- docs/shopping/API.md
- docs/shopping/TESTING.md
- docs/shopping/DEPLOYMENT.md
- docs/shopping/RUNBOOK.md
<!-- AI_SHOPPING_PLATFORM_END -->

<!-- SHOPPING_M4_START -->

## AI Shopping Platform — M4

AI Shopping Platform is integrated as an AIControlCenter service layer.

Implemented capabilities:

- WordPress CMS runtime
- WooCommerce Commerce Engine
- Read-only product and category APIs
- Mock and WooCommerce Adapter selection
- systemd runtime configuration
- Git-excluded Secret management
- External HTTP development access

Production HTTPS remains blocked until a user-owned domain is available.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## AI Shopping Platform — M5 Storefront

AI Shopping Platform now provides an external Storefront powered by AIControlCenter.

Implemented:

- Featured Products
- Product Search
- Category Filter
- Price Filter
- Stock Filter
- Pagination
- Product Image and Placeholder
- Modular WordPress Presentation Plugin
- External Storefront page

Storefront:

http://bokstory.iptime.org:58088/ai-shopping/

WordPress remains the Presentation Layer.
AIControlCenter owns all Shopping business logic.
<!-- SHOPPING_M5_END -->

---

## Orange Coco Homepage

The storefront now renders curated homepage sections.

- NEW ARRIVALS
- BEST SELLERS
- TOP
- DRESS
- OUTER
- BAG
- SALE

Homepage collections are rendered from AIControlCenter Shopping API.

<!-- AI_SHOPPING_STOREFRONT_V016_BASELINE -->
## AI Shopping Storefront v0.16.0

The AI Shopping Storefront is a presentation adapter for the
AIControlCenter Shopping API.

Runtime assets:

- `assets/storefront.css`
- `assets/orange-coco-v6.css`
- `assets/storefront-ui.js`

Product detail contract:

- Existing product: `GET /product/{id}/` returns HTTP 200
- Missing product: `GET /product/{id}/` returns HTTP 404
- Product data is supplied by AIControlCenter
- WordPress owns presentation, not shopping business logic

Runtime validation:

- WordPress PHP 8.3
- Homepage HTTP 200
- Product detail HTTP 200
- Missing product HTTP 404

<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## Mac Control Plane Production Baseline

The Mac mini M4 is the always-on Brain and the
single AIControlCenter Control Plane.

Current validated baseline:

- Branch: `sprint/mac-control-plane-foundation`
- Commit: `1e102c001c28108bee9583294abee77ce7d43643`
- Runtime commit: `1e102c001c28`
- Runtime: `/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/venvs/1e102c001c28`
- Supervisor:
  `system/com.aicontrolcenter.api.shadow`
- Application user: `kyouhan`
- Listener: `127.0.0.1:18100`
- Health contract: HTTP `200`
- Mutating request contract: HTTP `405`
- Mode: `shadow-read-only`
- GUI login required: `false`
- Transactional canonical apply: implemented
- Transactional rollback: implemented
- launchd bootout settle policy: 2 seconds
- Final restart: `19761 → 19842`

Shadow observation:

- Duration: `23.535` hours
- Samples: `283/283` passed
- Failed samples: `0`
- Success ratio: `100.0%`
- PID transitions: `0`
- Observation SHA-256:
  `a1c79121ff04699d0ee717d72aa158e81c954fe84387c0689a1c5c08fb83519d`
- Summary SHA-256:
  `c980df46e94b40b0b72086a55501f2cad4f748ad98d4f6ec7ceea9c15a02c8de`

Control Plane implementation is complete.
Production write cutover remains blocked pending
an explicit Production approval.
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->

## Dashboard Shadow Control Plane

AIControlCenter exposes a read-only Control Plane status contract through the Mac mini Shadow API.

Runtime endpoint:

- Listener: `127.0.0.1:18100`
- Health: `GET /health`
- Dashboard: `GET /dashboard`
- Write requests: rejected with HTTP `405`

The Dashboard response includes:

- Control Plane service identity
- Shadow operating mode
- Read-only enforcement state
- Local listener address
- Commit-specific Runtime metadata
- Runtime metadata validation status

Runtime identity is loaded from an immutable `metadata.json` file generated during the commit-specific Runtime build.

Dashboard requests do not execute Git, `launchctl`, or shell commands.

Runtime activation is allowed only after:

1. Dependency installation succeeds.
2. Application import succeeds.
3. The test suite succeeds.
4. Runtime metadata is generated.
5. Runtime metadata schema validation succeeds.

Current validated PI-001 Runtime:

- Commit: `ba8d2c9772577863c3c040d01654c4f011e2d45e`
- Short commit: `ba8d2c977257`
- Health status: HTTP `200`
- Dashboard status: HTTP `200`
- Write probe: HTTP `405`
