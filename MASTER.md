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

<!-- AICONTROLCENTER:PI-006:START -->
## PI-006 — Approved Ollama Native Deployment Complete

PI-006 established Ollama 0.32.1 as an approved native macOS runtime on the Mac mini M4 Control Plane.

Production baseline:

- AIControlCenter remains the single Control Plane.
- Ollama is a replaceable local model runtime and owns no platform business logic.
- Ubuntu remains a stateless infrastructure worker and runs no AI workloads.
- Ollama service: `system/com.aicontrolcenter.ollama`
- Ollama endpoint: `127.0.0.1:11434`
- AIControlCenter service: `system/com.aicontrolcenter.api.shadow`
- AIControlCenter endpoint: `127.0.0.1:18100`
- Read-only API: `GET /api/services/ollama`
- Production runtime: `3679588b760c`
- Rollback runtime: `7cb2e7a400a6`
- Model inventory: `0`
- AIControlCenter and Ollama listeners: loopback-only
- Operational gate: passed
- Git state at operational validation: clean

Validation:

- Full suite: 481 passed, 5 deselected, 423 warnings.
- AIControlCenter health: ONLINE.
- Ollama health: ONLINE.
- Runtime metadata gate: passed.
- Deployment summary validation code: 0.

Production evidence:

`~/Library/Application Support/AIControlCenter/runtime/evidence/pi-006/api-release-3679588b760c-20260720T235541Z`

Safety corrections completed during PI-006:

- Isolated mocked Ollama binary targets from `/opt/homebrew/bin/ollama`.
- Separated Homebrew user operations from privileged system operations.
- Restored and correctly registered the Ollama API router inside `create_app`.
- Distinguished the active system LaunchDaemon architecture from the legacy GUI LaunchAgent manager.
- Revalidated the final operational gate using a Python assertion after a pasted shell assertion was damaged.

Deferred technical debt:

- Replace deprecated `datetime.utcnow()` usage with timezone-aware UTC values.
- Resolve remaining Python, Starlette, and dependency deprecation warnings.
- Approve model acquisition, checksum, retention, resource, and removal policies before downloading a model.
<!-- AICONTROLCENTER:PI-006:END -->

<!-- AICONTROLCENTER:PI-007:START -->
## PI-007 Status

Status: **Production Complete — Documentation Closure Pending**

PI-007 delivered approved model lifecycle monitoring and governance under the
AIControlCenter control plane.

Production identifiers:

- source commit:
  `39fe04e3330e398f38567efa58bddb39b9893756`
- active runtime: `39fe04e3330e`
- rollback runtime: `3679588b760c`
- endpoint: `GET /api/governance/models`
- policy: default `DENY`
- write boundary: disabled
- approved models: `0`
- observed models: `0`
- violations: `0`

Architecture, implementation, focused tests, full tests, immutable deployment,
Production validation, and rollback-readiness validation are complete.
<!-- AICONTROLCENTER:PI-007:END -->

## PI-008 Completion Record

Status: COMPLETE

Title: Model Governance Audit and Dashboard Integration

Production milestone:

- active source commit: `b9ad351a7241e521c8964218f59724fcb04db93c`
- active runtime release: `b9ad351a7241`
- rollback runtime release: `0352e396f329`
- Production runner: metadata-based and Git-independent
- Production closure gate: passed

Delivered:

- immutable governance audit snapshots
- append-only SQLite persistence
- audit comparison
- read-only query service
- GET-only API
- Dashboard integration
- runtime provenance
- rollback-independent runner contract

Validation:

- full test suite: `636 passed, 5 deselected`
- health endpoint: passed
- Ollama endpoint: passed
- governance endpoint: passed
- audit endpoints: passed
- Dashboard endpoint: passed
- OpenAPI write-method validation: passed
- SQLite append-only validation: passed
- process identity validation: passed
- rollback compatibility validation: passed
- Git clean: passed

<!-- PI-009:START -->
## PI-009 Master Status

**State:** Implementation Complete / Production Activation Pending

Implementation commit:

`e1d46099427321a3ba7a150aad589320c8f1261a`

Validation:

- targeted: 17 passed;
- full regression: 710 passed, 5 deselected, 427 warnings;
- Git status: clean;
- Production DB modified: no;
- Write API: disabled;
- Dashboard policy: panel-local fail-soft.

Remaining gates:

1. External Notion synchronization.
2. Explicit Production migration authorization.
3. Explicit scheduler activation authorization.
4. Post-activation observation and rollback validation.
<!-- PI-009:END -->

<!-- PI-009-OPERATIONS-FINAL:BEGIN -->
## Current Production Milestone

PI-009 Governance Operations: CLOSED

Completed:

- operation domain and application contracts
- append-only SQLite operation event storage
- Production schema migration and verified backup
- manual backup verification operation
- Production UTC clock adapter
- JSON-first one-shot operation runner
- full regression and Git-clean implementation gate

Final implementation commit:

    d1072aa35fb5034c1097923fd7f6d7643132460b

Operational state:

- runner available
- scheduler inactive
- LaunchAgents not installed
- cadence policy deferred
- Production database protected

Next Production milestone:

PI-010 Controlled Scheduler Policy and Activation

This section is the repository-backed Notion handoff
source. External Notion synchronization is not performed
by this Git task.
<!-- PI-009-OPERATIONS-FINAL:END -->

<!-- PI-010-HEADLESS-PRODUCTION-CLOSE-2026-07-23 -->
## PI-010 Status

Status: CLOSED

Production governance scheduling is active on the Mac mini Control Plane through the managed AIControlCenter user crontab adapter.

Production execution, semantic capability evidence, append-only audit correlation, backup protection, rollback, regression, Git cleanliness, and documentation gates passed.

Next Production milestone: Shopping Platform Foundation.

<!-- BEGIN AICONTROLCENTER SPF-002 MASTER -->
## Current Production Milestone

Milestone: Shopping Platform Foundation

- PI-010: CLOSED
- SPF-001: CLOSED
- SPF-002: CLOSED
- Architecture commit: `9e4476abfe53cad9b19c0c5c472028f6c91f82e5`
- Regression baseline: 741 passed, 5 deselected, 427 warnings
- Production governance scheduler: Active
- Governance database quick check: Passing
- Shopping writes: Disabled
- Ubuntu Shopping state and business logic: Prohibited

Next task: SPF-003 Shopping package and read-only port skeleton.
<!-- END AICONTROLCENTER SPF-002 MASTER -->

<!-- SPF-003:START -->
## SPF-003 Closure Record

- Status: CLOSED
- Milestone: Shopping Platform Foundation
- Scope: package boundaries, compatibility migration, provisional contracts, seven read-only ports, and validation
- Implementation commit: `fd52aad1d9af9d056d80d8f7d6170605ea0d11b2`
- Targeted validation: 6 passed
- Full regression: 747 passed with 5 deselected
- Production modified: false
- Ubuntu modified: false
- Write operations enabled: false
- Next task: **SPF-004 — Canonical JSON Schema v1**
<!-- SPF-003:END -->


<!-- AICONTROLCENTER-SPF-004-CLOSED -->
## Shopping Platform Foundation Status — SPF-004

SPF-004 Canonical JSON Schema v1: **CLOSED**

Authoritative state:

- Shopping Sprint completed tasks: 4/10
- Shopping Sprint remaining tasks: 6/10
- canonical contract schemas: 15
- schema resources: 17
- schema assets including registry: 18
- targeted schema tests: 6 passed
- full regression: 753 passed
- production modified: false
- Ubuntu modified: false
- Shopping writes enabled: false

Implementation commit: `7a436a62fbaa2c176e877297d88b810b255f2776`

Next task: **SPF-005 Capability Registry — deny by default**.

<!-- SPF-005-CLOSE:BEGIN -->
## Shopping Platform Foundation Status — SPF-005 CLOSED

Current sprint progress: **5/10 tasks complete**.

Closed:
- SPF-001 Repository and branch baseline
- SPF-002 Architecture foundation
- SPF-003 Package and read-only port skeleton
- SPF-004 Canonical JSON Schema v1
- SPF-005 Capability Registry deny-by-default

SPF-005 production invariants:
- AIControlCenter owns capability governance.
- Default authorization behavior is DENY.
- Shopping WRITE capabilities are not executable.
- Ubuntu remains a stateless infrastructure worker.
- WordPress and WooCommerce do not own platform authorization or business logic.

Next task: **SPF-006 Read Adapter Contracts**.

Remaining Shopping Platform Foundation work: **5/10 tasks**.
<!-- SPF-005-CLOSE:END -->

<!-- SPF-006-CLOSE:BEGIN -->
## Shopping Platform Foundation Status — SPF-006 CLOSED

Current sprint progress: **6/10 tasks complete — 60%**.

Closed:
- SPF-001 Repository and branch baseline
- SPF-002 Architecture foundation
- SPF-003 Package and read-only port skeleton
- SPF-004 Canonical JSON Schema v1
- SPF-005 Capability Registry deny-by-default
- SPF-006 Read Adapter Contracts

Current production invariants:
- AIControlCenter owns all Shopping business logic and governance.
- Adapters remain replaceable and vendor-neutral at the platform boundary.
- WordPress and WooCommerce do not own platform-wide authorization or business logic.
- Ubuntu remains a stateless infrastructure worker.
- Shopping WRITE operations remain disabled.

Next task: **SPF-007 Adapter Health Monitoring**.

Remaining Shopping Platform Foundation work: **4/10 tasks**.
<!-- SPF-006-CLOSE:END -->

<!-- SPF-007-CLOSE:BEGIN -->
## Shopping Platform Foundation Status — SPF-007 CLOSED

Current sprint progress: **7/10 tasks complete — 70%**.

Closed:
- SPF-001 Repository and branch baseline
- SPF-002 Architecture foundation
- SPF-003 Package and read-only port skeleton
- SPF-004 Canonical JSON Schema v1
- SPF-005 Capability Registry deny-by-default
- SPF-006 Read Adapter Contracts
- SPF-007 Adapter Health Monitoring

Current production invariants:
- AIControlCenter remains the single Shopping control plane.
- Adapter health is monitoring data, not authorization.
- Health normalization and aggregation remain read-only and stateless.
- WordPress and WooCommerce do not own platform-wide business logic.
- Live vendor transport remains disabled.
- Ubuntu remains a stateless infrastructure worker.
- Shopping WRITE operations remain disabled.

Next task: **SPF-008 Read-only Snapshots**.

Remaining Shopping Platform Foundation work: **3/10 tasks**.
<!-- SPF-007-CLOSE:END -->

<!-- SPF-008-CLOSE:BEGIN -->
## Shopping Platform Foundation Status — SPF-008 CLOSED

Current sprint progress: **8/10 tasks complete — 80%**.

Closed:
- SPF-001 Repository and branch baseline
- SPF-002 Architecture foundation
- SPF-003 Package and read-only port skeleton
- SPF-004 Canonical JSON Schema v1
- SPF-005 Capability Registry deny-by-default
- SPF-006 Read Adapter Contracts
- SPF-007 Adapter Health Monitoring
- SPF-008 Read-only Snapshots

Current production invariants:
- AIControlCenter remains the single Shopping control plane.
- Snapshot queries remain read-only.
- Snapshot creation and persistence remain disabled.
- Authorization occurs before snapshot repository access.
- WordPress and WooCommerce do not own platform-wide business logic.
- Ubuntu remains a stateless infrastructure worker.
- Shopping WRITE operations remain disabled.

Next task: **SPF-009 Validation and Schema Drift**.

Remaining Shopping Platform Foundation work: **2/10 tasks**.
<!-- SPF-008-CLOSE:END -->

<!-- AICONTROLCENTER:SPF-009:CLOSED -->
## SPF-009 Validation and Schema Drift Closure

- Project state: SPF-009 CLOSED, Shopping Platform Foundation **9/10**.
- Implementation commit: `3fa21878e72cdb9608a728a1c676e70fb70b5717`.
- Runtime schema validation and schema drift monitoring are read-only control-plane capabilities owned by AIControlCenter.
- Validation gate: 58 targeted tests passed; full regression 930 passed and 5 deselected.
- Production mutation: false.
- Ubuntu application state: false.
- Write operations enabled: false.
- Next production milestone: SPF-010 final regression, operational and documentation closure.

<!-- AICONTROLCENTER:SPF-010:CLOSED -->
## SPF-010 Closure — Shopping Platform Foundation

- Status: CLOSED
- Shopping Platform Foundation: 10/10 (100%)
- Production Readiness Gate: PASSED for the read-only Foundation.
- AIControlCenter remains the single Control Plane on Mac mini M4.
- Ubuntu Server remains a stateless infrastructure worker only.
- AI workloads, business logic, and application state remain outside Ubuntu.
- Production write operations remain disabled.
- Automatic schema adoption and automatic schema migration remain disabled.
- Any future mutation or write capability requires a separate sprint and explicit production gate.
- Shopping regression: 233 passed.
- Full regression: 930 or more passed, 5 deselected, 0 failed, 0 errors.
- Read-only operational smoke validation: PASSED.
- Release blockers at final audit: 0.
- Master project status: SPF-010 CLOSED.
- Shopping Platform Foundation status: COMPLETE.
- Next phase must preserve read-only-first governance and adapter boundaries.

<!-- BEGIN AICONTROLCENTER:SRI-03 -->
## Shopping External Read Integration — Authoritative State

**Program:** SRI — Shopping External Read Integration
**Branch:** `feature/shopping-external-read-integration`

### Progress

- SRI-01 — CLOSED
- SRI-02 — CLOSED
- SRI-03 — IN PROGRESS
- SRI-04 — PENDING
- SRI-05 — PENDING
- SRI-06 — PENDING

**Program closure:** 2/6 CLOSED

### SRI-03 completed

- Canonical WooCommerce read wrapper
- Canonical normalization and schema validation
- GET-only bounded read transport
- Caddy runtime validation
- Mac LAN ingress validation
- External WAN HTTP 80 validation
- DDNS and public IPv4 validation
- Authoritative parent CAA root-cause confirmation

### Current blocker

Controlled Production DNS and trusted HTTPS are required before the first real canonical WooCommerce production READ.

### Safety state

- Shopping writes: DISABLED
- Production ACME on `bokstory.iptime.org`: STOPPED
- Ubuntu business logic changes: NONE

### Next production milestone

Trusted HTTPS on a platform-controlled production hostname followed by one controlled canonical WooCommerce READ.
<!-- END AICONTROLCENTER:SRI-03 -->

<!-- SRI-06B-R1:MASTER -->
## Production Contracts Established by SRI

### Platform invariants

- AIControlCenter is the single Control Plane.
- Mac mini M4 owns orchestration, AI, business logic and application state.
- Ubuntu remains a stateless infrastructure worker.
- External components integrate through replaceable adapters and APIs.

### External READ governance

- Read-only monitoring precedes validation and write operations.
- Persisted JSON evidence is authoritative.
- Credential values must not appear in Git, console output or evidence.
- Generic monitoring owns orchestration and domain logic remains in its domain.

### Production write gate

No production write is authorized by SRI.
Future writes require explicit architecture review, authorization, audit evidence, rollback design and production validation.

### Codex execution governance

- AI Home Datacenter Architect remains architecture and production authority.
- Codex is an implementation executor.
- Codex must preserve approved scope, run tests and update documentation.
- Codex must not change architecture or infrastructure ownership implicitly.
<!-- END SRI-06B-R1 -->
