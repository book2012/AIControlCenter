# Project History

AIControlCenter became the Brain.

Ubuntu became an optional Worker.

Implemented

- BrainAgent
- Provider Manager
- Telegram
- Dashboard
- Conversation Memory
- SQLite
- Command Router

## Sprint 21-22

Scheduler Foundation completed.

Memory Manager completed.

AIControlCenter now has:

- Heartbeat
- Scheduled Job Registry
- Background Scheduler
- Conversation Memory
- Working Memory
- Long-term Memory
- Memory API

<!-- AI_SHOPPING_PLATFORM_START -->
## AI Shopping Platform Service Layer

AI Shopping Platform development started after the infrastructure
platform reached production-ready status.

Shopping is implemented as a service layer inside AIControlCenter.

The architectural ownership is:

- WordPress provides the shopping homepage and CMS
- WooCommerce provides the commerce engine
- AIControlCenter owns Shopping business logic and AI workflow
- AI Agent generates content and performs approved updates
- n8n executes external automation
- Mac mini M4 is the final production Control Plane
- Ubuntu remains an infrastructure worker

Development currently runs in a virtual environment.

The same source code will later be deployed to Mac mini M4 using
production-specific configuration.
<!-- AI_SHOPPING_PLATFORM_END -->

<!-- SHOPPING_M4_START -->

## Shopping Platform M4 History

AI Shopping Platform was introduced as a service layer on top of the completed AI Home Datacenter Platform.

During M4:

- WordPress and WooCommerce were deployed in the Ubuntu virtual validation environment.
- AIControlCenter remained the sole business-logic and orchestration layer.
- WooCommerce was connected through a read-only Adapter.
- External HTTP development access was established through ipTIME DDNS and port forwarding.
- Public TLS using the ipTIME hostname was rejected by the parent-domain CAA policy.
- Production HTTPS was deferred until a user-owned domain is available.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## Shopping Platform M5 History

M5 introduced the first external AI Shopping Storefront.

The Storefront was implemented as a modular WordPress Presentation Plugin.

WordPress displays Featured Products, categories, search results, price filters, stock filters, pagination, and product images.

AIControlCenter continues to own product selection, search validation, Commerce Adapter access, and future recommendation logic.

The implementation was validated through the external ipTIME DDNS development address while Production HTTPS remains deferred to a user-owned domain.
<!-- SHOPPING_M5_END -->

<!-- AI_SHOPPING_STOREFRONT_V016_ADR -->
## ADR — AI Shopping Storefront v0.16.0 Baseline

Date: 2026-07-13

Decision:

Orange Coco v6 is the canonical Shopping Storefront presentation layer.

The WordPress plugin remains a presentation adapter and does not own
shopping business logic. Product detail pages retrieve product data
through the AIControlCenter Shopping API.

HTTP contract:

- Existing products return HTTP 200.
- Missing products return HTTP 404.

Rationale:

This preserves the headless architecture and keeps business logic
inside the single AIControlCenter Control Plane.

<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:START -->
## 2026-07-14 — Non-root LaunchDaemon Milestone

            The Mac Control Plane Shadow Runtime completed
            its non-root LaunchDaemon and automatic restart
            production gates.

            The earlier LaunchAgent design was rejected after
            reboot testing demonstrated that a GUI bootstrap
            domain was unavailable in the headless operating
            environment.

            The replacement system LaunchDaemon:

            - starts without a GUI login
            - runs the application as `kyouhan`
            - binds only to `127.0.0.1:18100`
            - returns HTTP `200` from `/health`
            - blocks mutating requests with HTTP `405`
            - uses a commit-specific Python runtime
            - uses secure root-owned installation files
            - recovered automatically:
              `1661 → 1975`

            Ubuntu remained unchanged and continues operating
            until Mac Shadow observation and rollback gates
            are complete.

            - Generated: `2026-07-14T03:31:53+00:00`
- Branch: `sprint/mac-control-plane-foundation`
- Commit: `db4d93a2652a704dfa9a7e149623064adb961504`
- Runtime commit: `db4d93a2652a`
<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:END -->

<!-- AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:START -->
## 2026-07-14 — Headless Recovery

            The Mac Control Plane recovered its read-only
            AIControlCenter API following a full reboot
            without a GUI login.

            The recovered service retained:

            - non-root application execution
            - commit-specific Runtime selection
            - localhost-only networking
            - read-only Shadow enforcement
            - system LaunchDaemon supervision

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
## 2026-07-14 — Shadow Observation Sprint

The Mac Control Plane entered its 24-hour read-only
Shadow observation phase after Headless Reboot Recovery.

No production cutover was performed.

Configured: `2026-07-14T04:19:41+00:00`
<!-- AICONTROLCENTER:SHADOW_OBSERVATION:END -->

<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## 2026-07-16 — Mac Control Plane Completed

The Mac mini M4 Control Plane completed its
foundation and operational validation program.

Milestones:

- Headless system LaunchDaemon recovery
- Non-root AIControlCenter execution
- Commit-specific Runtime enforcement
- `23.535`-hour Shadow observation
- `283/283` successful observations
- Canonical manager reconciliation
- Transactional apply and rollback
- launchd settle policy
- Final canonical apply
- Final restart:
  `19761 → 19842`
- Health HTTP `200`
- Write protection HTTP `405`
- Localhost-only listener `127.0.0.1:18100`

The Control Plane implementation is complete.
Ubuntu remains a stateless infrastructure worker.
Production write cutover is intentionally deferred.
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->
