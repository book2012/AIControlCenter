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

<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:START -->
## Mac Control Plane Runtime Status

            The Mac mini now runs the AIControlCenter
            read-only Shadow API under a headless,
            non-root system LaunchDaemon.

            - Supervisor:
              `system/com.aicontrolcenter.api.shadow`
            - Application user: `kyouhan`
            - Process state: `running`
            - Endpoint: `http://127.0.0.1:18100`
            - Health contract: HTTP `200`
            - Mutating request contract: HTTP `405`
            - Runtime:
              `/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/venvs/0f1b4c5d8aba`
            - Automatic restart:
              `1661 → 1975`
            - GUI login required: `false`
            - Ubuntu Control Plane replaced: `false`
            - Secret migration completed: `false`

            Current production milestone:
            Headless Reboot Recovery Gate.

            - Generated: `2026-07-14T03:31:53+00:00`
- Branch: `sprint/mac-control-plane-foundation`
- Commit: `db4d93a2652a704dfa9a7e149623064adb961504`
- Runtime commit: `db4d93a2652a`
<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:END -->

<!-- AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:START -->
## Mac Headless Control Plane Status

            The AIControlCenter Shadow API recovered
            automatically after a full system reboot
            without requiring a GUI login.

            - Supervisor:
              `system/com.aicontrolcenter.api.shadow`
            - Listener: `127.0.0.1:18100`
            - Mode: `shadow-read-only`
            - Headless reboot recovery: `passed`
            - Ubuntu production cutover: `not started`

            - Verified: `2026-07-14T04:11:33+00:00`
- Commit: `aadb42089642a17f54825b850626bd43d5e22015`
- Runtime: `/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/venvs/aadb42089642`
- Pre-reboot PID: `875`
- Post-reboot PID: `567`
- Process user: `kyouhan`
- Health HTTP: `200`
- Write probe HTTP: `405`
<!-- AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:END -->

<!-- AICONTROLCENTER:SHADOW_OBSERVATION:START -->
## 24-Hour Shadow Observation

The Mac Control Plane is configured for a read-only
24-hour Shadow observation.

- Sample interval: `300 seconds`
- Storage:
  `/var/log/aicontrolcenter/shadow-observation.jsonl`
- Production cutover: `blocked pending observation`
- Observation configured: `2026-07-14T04:19:41+00:00`
<!-- AICONTROLCENTER:SHADOW_OBSERVATION:END -->
