# MASTER

## Completed

- Brain Runtime
- FastAPI
- Provider Manager
- OpenAI
- Google
- BrainAgent
- Telegram
- Command Router
- Storage Registry
- Backup Registry
- Task Registry

## Current Sprint

Doctor Service

## Next

Logs

Backup Verify

Worker Health

Backup Execute

## Current Sprint

Sprint 21

Brain Scheduler

Current Focus

- Internal Scheduler
- Heartbeat
- Job Registry
- Automation Foundation

<!-- AI_SHOPPING_PLATFORM_START -->
## Current Program

Project: AI Shopping Platform

Status: Active Development

Current Sprint: Shopping Control Plane Bootstrap

Development runtime: Virtual Environment

Production target: Mac mini M4

Current implementation:

- Shopping domain
- Shopping health API
- Shopping readiness API
- Shopping capabilities API
- Safe read-only defaults
- Shopping test suite
- Shopping documentation

Architecture ownership:

- WordPress owns presentation and CMS
- WooCommerce owns commerce records
- AIControlCenter owns business and AI logic
- n8n executes automation
- Ubuntu remains an infrastructure worker
<!-- AI_SHOPPING_PLATFORM_END -->

<!-- SHOPPING_M4_START -->

## Shopping Platform M4 Status

Milestone: Live WooCommerce Control Plane

State:

- Architecture implemented
- WordPress and MariaDB runtime healthy
- WooCommerce REST Adapter implemented
- Product and Category APIs implemented
- Runtime Adapter selection implemented
- Read-only policy enforced
- Documentation and Git Gate in progress

Next service milestone: Shopping Homepage and AI Product Generation.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## Shopping Platform M5 Status

Milestone:

AI Shopping Storefront Foundation

State:

- Featured Product API implemented
- Product Search API implemented
- Product image contract implemented
- Storefront Plugin active
- External Storefront reachable
- Search and filters connected to AIControlCenter
- M5 Production Gate and Git closeout in progress

Next milestone:

M6 AI Product Generation and Approval Foundation
<!-- SHOPPING_M5_END -->

---

## Commit 19

Status: Complete

Implemented

- Homepage Renderer
- Homepage Curated Sections
- NEW / BEST / TOP / DRESS / OUTER / BAG / SALE
- Shopping Search API Integration
- Multi-section Storefront Rendering

UI Progress

95%

<!-- AI_SHOPPING_STOREFRONT_V016_MASTER -->
## Shopping Platform Baseline

Version: AI Shopping Storefront v0.16.0

Status: Feature Complete / Production Validation Passed

Git baseline:

- Commit: `a4d6098`
- Branch: `feature/shopping-platform-bootstrap`

Validated:

- Orange Coco v6 storefront
- AIControlCenter Shopping API integration
- Product detail page
- Homepage HTTP 200
- Product detail HTTP 200
- Missing product HTTP 404
- PHP 8.3 syntax validation
- JavaScript syntax validation

Next production milestone:

- Mac mini Production Control Plane migration

<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## Mac Control Plane Baseline

Status: **Implementation Complete**

- Final commit: `1e102c001c28108bee9583294abee77ce7d43643`
- Runtime commit: `1e102c001c28`
- Service:
  `system/com.aicontrolcenter.api.shadow`
- Application user: `kyouhan`
- Health: HTTP `200`
- Write protection: HTTP `405`
- Listener: `127.0.0.1:18100`
- Final restart: `19761 → 19842`
- Observation:
  `283/283` successful samples
- Observation duration:
  `23.535` hours
- Transactional apply: complete
- Transactional rollback: complete
- Production write cutover: not approved

Next program milestone:

AIControlCenter Platform Integration using the
completed Mac Control Plane baseline.
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->

## PI-001 Production Baseline

Status: COMPLETE

Validated on: 2026-07-16

Production Runtime:

- Commit: `ba8d2c9772577863c3c040d01654c4f011e2d45e`
- Short commit: `ba8d2c977257`
- Listener: `127.0.0.1:18100`
- Runtime mode: shadow
- Runtime metadata: available
- Runtime metadata schema: version 1

Operational validation:

- `GET /health`: HTTP `200`
- `GET /dashboard`: HTTP `200`
- `POST /dashboard`: HTTP `405`
- Shadow API read-only policy: enforced
- Runtime commit matches Git HEAD
- Runtime activation gated by metadata validation

Architecture status:

- Mac mini remains the always-on Control Plane.
- AIControlCenter remains the single orchestration layer.
- Ubuntu remains a stateless infrastructure worker.
- Dashboard requests do not execute Git, launchctl or shell commands.
- Runtime identity is consumed through immutable JSON metadata.

Next Production Milestone:

- Complete PI-001 documentation closeout.
- Merge the feature branch after final review.
- Define the next read-only Control Plane integration.

<!-- AICONTROLCENTER:PI-002:START -->
## PI-002 Production Status

Status: **Production Gate Passed**

Completed:

- Ubuntu worker health JSON contract
- Read-only SSH adapter
- Production worker configuration
- Dashboard worker monitoring
- Structured optional failure continuity
- system LaunchDaemon environment integration
- Immutable runtime validation
- Full regression validation

Production state:

- Mac mini owns orchestration and monitoring.
- Ubuntu remains an optional stateless worker.
- Worker unavailability does not interrupt the Control Plane.
- Production writes remain disabled.

Next operational milestone:

- Establish successful dedicated-key SSH health collection from the LaunchDaemon.
<!-- AICONTROLCENTER:PI-002:END -->

<!-- AICONTROLCENTER:PI-003:START -->
## PI-003 Production Status

Status: **Complete**

Primary platform milestone:

- Mac mini standalone Production Control Plane

Ubuntu status:

- Optional infrastructure extension
- May remain powered off
- Immich and Nextcloud recover automatically after Ubuntu boot
- Detailed Ubuntu integration deferred

Production result:

- AIControlCenter operates independently of Ubuntu.
- Optional worker failure does not interrupt the platform.
- Mac mini service deployment is now the primary program focus.
<!-- AICONTROLCENTER:PI-003:END -->

<!-- AICONTROLCENTER:PI-004:START -->
## PI-004 Production Status

Status: **Complete**

Current Production baseline:

- Mac mini standalone Control Plane
- AIControlCenter system LaunchDaemon
- immutable commit-specific runtime
- embedded Homepage API
- Ubuntu optional and powered-off permitted
- reboot recovery validated

Next milestone: PI-005 Mac Service Deployment Platform.
<!-- AICONTROLCENTER:PI-004:END -->

<!-- AICONTROLCENTER:PI-005:START -->
## PI-005 Status

**Complete — Mac Service Deployment Platform baseline**

Production evidence confirms the full test suite and all PI-005 JSON gates passed with deployment execution disabled.

Next production milestone: approved native Ollama deployment on the Mac mini.
<!-- AICONTROLCENTER:PI-005:END -->
