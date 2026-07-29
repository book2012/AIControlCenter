# Roadmap

## M2-P2 Closure and M2-P3

M2-P2 is CLOSED after exactly one controlled test-owned activation below a
pytest temporary root. Fail-closed permit reservation, deterministic typed
operation ordering and replay denial are validated. Persistent host activation
is NOT STARTED, persistent SQLite audit is NOT IMPLEMENTED and Production
activation remains `NOT_AUTHORIZED`. Next: M2-P3 Pilot Evidence and Rollback
Validation.

## M2-P1 Closure and M2-P2

M2-P1 Controlled Non-Production Sandbox Pilot Authorization is CLOSED. Pilot
authorization policy is AVAILABLE; pilot activation is NOT STARTED. Persistent
SQLite audit is NOT IMPLEMENTED and Production activation remains
`NOT_AUTHORIZED`. Next: M2-P2 Controlled Sandbox Pilot Activation and Evidence.

## DPL-04C Closure

DPL-04C is complete. The Mac Control Plane owns durable deployment audit, with
pure canonical event and hash-chain contracts behind a replaceable port. The
future append-only SQLite adapter is selected but not implemented. DPL-04A,
DPL-04B and DPL-04C are closed; DPL-04D is ready. M2 remains incomplete and
production activation is `NOT_AUTHORIZED`.

## DPL-04B Closure

DPL-04B is complete. The Mac-only adapter can materialize deterministic
manifest and evidence JSON only under an explicit, confined non-production
sandbox root. Default composition remains deny-only; command execution,
durable audit and production activation remain prohibited. DPL-04C is next.

## DPL-04A Closure

DPL-04A is complete. Typed executor contracts and ports are limited to
non-production Mac Control Plane targets and use a deny-only default
composition. No concrete real executor or production activation is authorized.
DPL-04B is next.

## DPL-03 Closure

DPL-03A through DPL-03D are complete subject to repository validation.
DPL-03D is simulation-only and does not authorize or perform production
deployment. M2 remains incomplete; DPL-04 is the next separately gated
milestone.

## Complete

- Core Runtime
- Dashboard
- BrainAgent
- Telegram
- Conversation Memory
- SQLite
- Command Router

## Current

Doctor

## Next

Logs

Backup Verify

Worker Health

Backup Execute

Homepage

Mac mini Production

## Sprint 21

- [ ] Brain Scheduler
- [ ] Heartbeat
- [ ] Job Registry
- [ ] Scheduler API
- [ ] Job Runner

## Sprint 22

- [x] Memory Manager
- [x] Working Memory
- [x] Long-term Memory
- [x] Memory API
- [x] Telegram Memory Commands

## Sprint 23

- [ ] Knowledge Registry
- [ ] Markdown Loader
- [ ] Knowledge Search
- [ ] Knowledge API
- [ ] Telegram /knowledge
- [ ] BrainAgent Knowledge Context

<!-- AI_SHOPPING_PLATFORM_START -->
## AI Shopping Platform Roadmap

### S0 Control Plane Baseline

Status: In Progress

- Shopping domain bootstrap
- Health API
- Readiness API
- Capabilities API
- Virtual environment tests
- Documentation
- Git Production Gate

### S1 Read-only Product Catalog

- Commerce Catalog Port
- Mock Product Adapter
- Product list API
- Product detail API
- Pagination
- Schema validation

### S2 WordPress and WooCommerce Virtual Environment

- WordPress container
- WooCommerce installation
- Test catalog
- REST API credentials
- AIControlCenter read-only adapter

### S3 AI Product Workflow

- Product generator
- SEO writer
- Product description generator
- Category generator
- Human approval
- Audit history

### S4 Controlled Publishing

- Authentication
- Authorization
- Idempotency
- Controlled WooCommerce writes
- Rollback
- Audit logging

### S5 Shopping Homepage

- WordPress theme
- Homepage
- Category pages
- Product pages
- Shopping Assistant integration

### S6 Production Hardening

- ARM64 validation
- Mac mini deployment
- Restart recovery
- Monitoring
- Backup
- Runbook
<!-- AI_SHOPPING_PLATFORM_END -->

<!-- SHOPPING_M4_START -->

## Shopping Platform Roadmap

### M4 — Live WooCommerce Control Plane

- [x] Shopping domain bootstrap
- [x] WordPress runtime
- [x] WooCommerce runtime
- [x] Product API
- [x] Category API
- [x] Integration API
- [x] Adapter Factory
- [x] systemd Secret integration
- [ ] Final Production Gate and Git closeout

### M5 — Shopping Experience

- [ ] Shopping Homepage
- [ ] Product detail experience
- [ ] Shopping Dashboard widgets
- [ ] Search and filtering

### M6 — AI Commerce

- [ ] AI Product Generator
- [ ] AI SEO Writer
- [ ] AI Category Generator
- [ ] AI Price Recommendation
- [ ] Approval workflow

### Production Blocker

A user-owned domain is required for public HTTPS.
The current ipTIME DDNS hostname cannot receive a certificate because of its parent-domain CAA policy.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## Shopping Platform Service Roadmap

### M5 — AI Shopping Storefront Foundation

- [x] Featured Products API
- [x] Product Search API
- [x] Category Navigation
- [x] Price Filters
- [x] Stock Filter
- [x] Pagination
- [x] Product Image Support
- [x] Placeholder Fallback
- [x] WordPress Presentation Plugin
- [x] External Storefront
- [ ] Final Documentation and Git Closeout

### M6 — AI Product Generation

- [ ] Product Draft Model
- [ ] AI Product Generator
- [ ] AI Description Writer
- [ ] AI SEO Writer
- [ ] AI Category Suggestion
- [ ] Approval Workflow
- [ ] Controlled WooCommerce Write
- [ ] Audit Log

### M7 — Shopping Operations

- [ ] Order Read Integration
- [ ] Customer Read Integration
- [ ] Inventory Monitoring
- [ ] Shopping Dashboard
- [ ] Notifications
- [ ] n8n Automation
<!-- SHOPPING_M5_END -->

<!-- AI_SHOPPING_STOREFRONT_V016_ROADMAP -->
## Shopping Platform Baseline

Status: Completed

Completed:

- Orange Coco Storefront
- Shopping API integration
- Category, search and product APIs
- Product detail page
- Responsive homepage
- HTTP 404 contract
- Git baseline commit

Next:

- Mac mini Production Control Plane
- WordPress and WooCommerce migration
- AIControlCenter launchd runtime
- Production domain and HTTPS
- Wishlist and checkout improvements
- AI recommendation and product creation

<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:START -->
## Mac Control Plane Roadmap

            ### Completed

            - [x] Mac Foundation Gate
            - [x] Git and SSH control
            - [x] Runtime Contract
            - [x] Python 3.12 production runtime
            - [x] Full Test Suite
            - [x] Read-only Health Gate
            - [x] Shadow read-only ASGI layer
            - [x] LaunchAgent architecture evaluation
            - [x] LaunchAgent rejected for headless production
            - [x] Non-root system LaunchDaemon
            - [x] Secure plist and runner ownership
            - [x] Automatic restart validation
            - [x] Localhost-only listener validation
            - [x] Health HTTP `200`
            - [x] Write probe HTTP `405`

            ### Current Sprint

            - [ ] Headless reboot recovery
            - [ ] Verify service before GUI login
            - [ ] Verify PID change after reboot
            - [ ] Verify process user `kyouhan`
            - [x] Verify Runtime commit preservation

            ### Next Sprint

            - [ ] 24-hour Shadow observation
            - [ ] CPU and memory baseline
            - [ ] restart-count monitoring
            - [ ] log-growth monitoring
            - [ ] Ubuntu Worker JSON read-only connection
            - [x] Mac Dashboard Shadow connection
            - [ ] Cutover and rollback runbook

            - Generated: `2026-07-14T03:31:53+00:00`
- Branch: `sprint/mac-control-plane-foundation`
- Commit: `db4d93a2652a704dfa9a7e149623064adb961504`
- Runtime commit: `db4d93a2652a`
<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:END -->

<!-- AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:START -->
## Mac Control Plane Roadmap Update

            - [x] Non-root LaunchDaemon
            - [x] Automatic restart
            - [x] Headless reboot recovery
            - [x] Health HTTP 200
            - [x] Write protection HTTP 405
            - [x] Localhost-only listener
            - [ ] Reconcile manager installer with plist
            - [ ] Complete 24-hour Shadow observation
            - [ ] Validate Ubuntu Worker JSON APIs
            - [ ] Complete cutover and rollback runbooks

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
## Shadow Observation Sprint

- [x] Headless reboot recovery
- [x] Read-only observer architecture
- [x] JSON Lines observation contract
- [x] Five-minute sampling definition
- [ ] Complete 24-hour observation window
- [ ] Review CPU and RSS baseline
- [ ] Review PID transitions
- [ ] Review log growth
- [ ] Approve or reject production cutover

Configured: `2026-07-14T04:19:41+00:00`
<!-- AICONTROLCENTER:SHADOW_OBSERVATION:END -->

<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## Mac Control Plane Foundation

Status: **Complete**

- [x] Commit-specific Runtime
- [x] Non-root system LaunchDaemon
- [x] Headless reboot recovery
- [x] Read-only Shadow API
- [x] Localhost-only listener
- [x] 24-hour observation
- [x] Canonical installation manager
- [x] Transactional apply
- [x] Transactional rollback
- [x] launchd settle policy
- [x] Final apply validation
- [x] Final restart validation
- [x] Documentation closeout

### Next Program Phase

- [ ] AIControlCenter REST API consolidation
- [x] Dashboard integration
- [ ] Homepage integration
- [ ] Ubuntu Worker read-only JSON APIs
- [ ] n8n read-only workflows
- [ ] Production cutover design and approval
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->

### PI-001 Dashboard Shadow API Integration

- [x] Dashboard Control Plane JSON contract
- [x] Immutable Runtime metadata
- [x] Runtime metadata schema validation
- [x] Metadata-gated Runtime activation
- [x] `GET /health` returns HTTP `200`
- [x] `GET /dashboard` returns HTTP `200`
- [x] `POST /dashboard` returns HTTP `405`
- [x] Runtime commit matches Git HEAD

Production Runtime: `ba8d2c977257`

<!-- AICONTROLCENTER:PI-002:START -->
### PI-002 Ubuntu Worker Health JSON Adapter

Status: **Complete — Structured Monitoring Gate**

- [x] Define worker health JSON schema
- [x] Implement bounded SSH transport
- [x] Implement Ubuntu health JSON adapter
- [x] Add Production worker configuration
- [x] Add structured failure continuity
- [x] Connect `ubuntu-main` to the Production Dashboard
- [x] Validate immutable runtime deployment
- [x] Validate system LaunchDaemon operation
- [x] Validate Health and Dashboard HTTP `200`
- [x] Validate full regression suite
- [ ] Configure dedicated SSH identity for the service process
- [ ] Validate successful remote worker telemetry

Next milestone: Ubuntu Worker Healthy Telemetry.
<!-- AICONTROLCENTER:PI-002:END -->

<!-- AICONTROLCENTER:PI-003:START -->
### PI-003 Ubuntu Worker Minimum Closure

Status: **Complete**

- [x] Confirm Ubuntu is an optional worker
- [x] Confirm Docker boot activation
- [x] Confirm Immich automatic recovery
- [x] Confirm Nextcloud automatic recovery
- [x] Confirm `unless-stopped` restart policies
- [x] Power off Ubuntu after validation
- [x] Validate Mac Control Plane standalone operation
- [x] Validate Health HTTP `200`
- [x] Validate Dashboard HTTP `200`
- [x] Validate structured optional-worker failure

### PI-004 Mac Standalone Production Baseline

Status: **Next**

- [ ] Inventory Mac mini services
- [ ] Validate Mac reboot recovery
- [ ] Define service deployment manifest
- [ ] Deploy Homepage on the Mac mini
- [ ] Validate local AI runtime and provider health
- [ ] Validate automation service deployment
- [ ] Add install, update and rollback automation
<!-- AICONTROLCENTER:PI-003:END -->

<!-- AICONTROLCENTER:PI-004:START -->
### PI-004 Mac Standalone Production Baseline

Status: **Complete**

- [x] Inventory Mac services
- [x] Create Mac Production service manifest
- [x] Confirm Homepage as embedded API
- [x] Align Homepage optional-worker contract
- [x] Validate immutable runtime deployment
- [x] Validate Mac reboot recovery
- [x] Run full test suite
- [x] Generate Production evidence

### PI-005 Mac Service Deployment Platform

Status: **Next**

- [ ] Define reusable service manifest schema
- [ ] Define install, update, restart and rollback interfaces
- [ ] Deploy Ollama as a managed Mac service
- [ ] Integrate Ollama health and model inventory
- [ ] Define n8n deployment contract
- [ ] Define OpenClaw adapter boundary
<!-- AICONTROLCENTER:PI-004:END -->

<!-- AICONTROLCENTER:PI-005:START -->
## PI-005 — Complete

- [x] Service manifest schema
- [x] JSON manifest validator
- [x] Read-only deployment plan
- [x] Mac service inspector
- [x] Desired/actual deployment diff
- [x] Ollama managed-service design
- [x] Dry-run and rollback plan
- [x] Installation approval gate
- [x] Full test and Production evidence

Next: PI-006 approved Ollama native deployment.
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
## PI-007 — Approved Model Lifecycle Monitoring and Governance

Status: **Production Complete — Final Documentation Commit Pending**

Completed milestones:

- architecture and ownership boundary
- canonical default-deny registry
- read-only registry loader
- governance evaluator
- read-only governance API
- full test suite and immutable runtime deployment
- Production operational validation
- rollback-readiness validation

Deferred beyond PI-007:

- approved model onboarding
- model download or deletion workflows
- write-operation authorization
- resource enforcement
- automated remediation
- model lifecycle audit UI

Any write-capable model lifecycle feature requires a separate Product Increment
and explicit Production approval.
<!-- AICONTROLCENTER:PI-007:END -->

## PI-008 — COMPLETE

Model Governance Audit and Dashboard Integration has completed the Production gate.

Completed scope:

- audit schema and immutable snapshots
- SQLite append-only persistence
- comparison and query services
- read-only API
- Dashboard integration
- runtime provenance
- Git-independent Production runner
- Production deployment
- rollback compatibility
- documentation closure

Next production milestone:

PI-009 should focus on operational observability for governance audit history, bounded Dashboard latency, backup verification, and alerting while preserving the read-only-first policy.

Write operations remain out of scope until monitoring, audit history, backup, and operational alerting are stable.

<!-- PI-009:START -->
## PI-009 Roadmap Status

### Completed

- Domain and event contracts.
- SQLite persistence adapter.
- Application service and projections.
- GET-only API integration.
- Fail-soft Dashboard integration.
- Regression and database-safety validation.
- Repository documentation handoff.

### Pending Production Gate

- Review and approve production migration.
- Review and approve scheduler activation.
- Synchronize the PI-009 Notion handoff.
- Execute post-activation operational validation.
- Confirm rollback readiness.

PI-010 must not depend on activated PI-009 scheduling until these
production gates are complete.
<!-- PI-009:END -->

<!-- PI-009-OPERATIONS-FINAL:BEGIN -->
## PI-009 Completion and PI-010 Transition

### PI-009 — Governance Operations

- [x] Domain contracts
- [x] SQLite append-only repository
- [x] Application dispatch service
- [x] Read-only API and Dashboard projection
- [x] Production schema migration
- [x] Verified Production backup
- [x] Manual operation validation
- [x] Production UTC clock adapter
- [x] JSON-first one-shot runner
- [x] Full regression
- [x] Documentation close

### PI-010 — Controlled Scheduler Policy and Activation

- [ ] Approve explicit cadence for each operation
- [ ] Render disabled launchd definitions
- [ ] Validate temporary plist artifacts
- [ ] Obtain explicit installation approval
- [ ] Install and activate under controlled gate
- [ ] Observe the first operation executions
- [ ] Validate audit projection and logs
- [ ] Document unload and rollback procedures
<!-- PI-009-OPERATIONS-FINAL:END -->

<!-- PI-010-HEADLESS-PRODUCTION-CLOSE-2026-07-23 -->
## PI-010 — Governance Operations Scheduling

Status: CLOSED — 2026-07-23

Completed explicit cadence, JSON one-shot execution, dedicated governance runtime capabilities, headless Production scheduling, authoritative run_succeeded validation, rollback protection, regression, and documentation close.

Next milestone: Shopping Platform Foundation.

<!-- BEGIN AICONTROLCENTER SPF-002 ROADMAP -->
## Shopping Platform Foundation

Status: In Progress

| Task | Scope | Status |
| --- | --- | --- |
| SPF-001 | Repository and branch baseline | CLOSED |
| SPF-002 | Architecture and ownership foundation | CLOSED |
| SPF-003 | Package and read-only port skeleton | NEXT |
| SPF-004 | Canonical JSON Schema v1 | QUEUED |
| SPF-005 | Deny-by-default capability registry | QUEUED |
| SPF-006 | Read adapter contracts | QUEUED |
| SPF-007 | Adapter health monitoring | QUEUED |
| SPF-008 | Read-only snapshot retrieval | QUEUED |
| SPF-009 | Validation and schema drift detection | QUEUED |
| SPF-010 | Regression and operational close | QUEUED |

Write progression:
Monitoring → Validation → Reconciliation → Approval → Dry Run → Canary Write → Production Write.
<!-- END AICONTROLCENTER SPF-002 ROADMAP -->

<!-- SPF-003:START -->
## Shopping Platform Foundation Progress — 2026-07-23

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture foundation
- [x] SPF-003 Package and read-only port skeleton
- [ ] SPF-004 Canonical JSON Schema v1
- [ ] SPF-005 Capability registry deny-by-default
- [ ] SPF-006 Read adapter contracts
- [ ] SPF-007 Adapter health monitoring
- [ ] SPF-008 Read-only snapshots
- [ ] SPF-009 Validation and schema drift
- [ ] SPF-010 Regression, operational validation, and documentation closure

SPF-003 implementation commit: `fd52aad1d9af9d056d80d8f7d6170605ea0d11b2`.
<!-- SPF-003:END -->


<!-- AICONTROLCENTER-SPF-004-CLOSED -->
## Shopping Platform Foundation Progress

Completed:

- SPF-001 Repository and branch baseline
- SPF-002 Architecture foundation
- SPF-003 Package and read-only port skeleton
- SPF-004 Canonical JSON Schema v1

Next production task:

- **SPF-005 Capability Registry — deny by default**

Remaining after SPF-004:

- SPF-005 Capability Registry
- SPF-006 Read Adapter Contracts
- SPF-007 Adapter Health Monitoring
- SPF-008 Read-Only Snapshots
- SPF-009 Validation and Schema Drift
- SPF-010 Regression, Operational Validation and Documentation Closure

An internal read-only Homepage Preview is now architecturally unblocked, but it must remain fixture or controlled read-only until the required adapter and monitoring gates are complete.

<!-- SPF-005-CLOSE:BEGIN -->
## Shopping Platform Foundation Progress

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture foundation
- [x] SPF-003 Package and read-only port skeleton
- [x] SPF-004 Canonical JSON Schema v1
- [x] SPF-005 Capability Registry deny-by-default
- [ ] SPF-006 Read Adapter Contracts
- [ ] SPF-007 Adapter Health Monitoring
- [ ] SPF-008 Read-only Snapshots
- [ ] SPF-009 Validation and Schema Drift
- [ ] SPF-010 Regression, Operational Validation, and Documentation Closure

Current completion: **5/10 — 50%**.

Next production milestone: SPF-006 establishes replaceable read adapter contracts without enabling Shopping writes.
<!-- SPF-005-CLOSE:END -->

<!-- SPF-006-CLOSE:BEGIN -->
## Shopping Platform Foundation Progress

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture foundation
- [x] SPF-003 Package and read-only port skeleton
- [x] SPF-004 Canonical JSON Schema v1
- [x] SPF-005 Capability Registry deny-by-default
- [x] SPF-006 Read Adapter Contracts
- [ ] SPF-007 Adapter Health Monitoring
- [ ] SPF-008 Read-only Snapshots
- [ ] SPF-009 Validation and Schema Drift
- [ ] SPF-010 Regression, Operational Validation, and Documentation Closure

Current completion: **6/10 — 60%**.

Next production milestone: SPF-007 introduces observable adapter health and controlled live read integration without enabling Shopping writes.
<!-- SPF-006-CLOSE:END -->

<!-- SPF-007-CLOSE:BEGIN -->
## Shopping Platform Foundation Progress

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture foundation
- [x] SPF-003 Package and read-only port skeleton
- [x] SPF-004 Canonical JSON Schema v1
- [x] SPF-005 Capability Registry deny-by-default
- [x] SPF-006 Read Adapter Contracts
- [x] SPF-007 Adapter Health Monitoring
- [ ] SPF-008 Read-only Snapshots
- [ ] SPF-009 Validation and Schema Drift
- [ ] SPF-010 Regression, Operational Validation, and Documentation Closure

Current completion: **7/10 — 70%**.

Next production milestone: SPF-008 introduces controlled read-only snapshot boundaries without enabling Shopping writes or moving application state to Ubuntu.
<!-- SPF-007-CLOSE:END -->

<!-- SPF-008-CLOSE:BEGIN -->
## Shopping Platform Foundation Progress

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture foundation
- [x] SPF-003 Package and read-only port skeleton
- [x] SPF-004 Canonical JSON Schema v1
- [x] SPF-005 Capability Registry deny-by-default
- [x] SPF-006 Read Adapter Contracts
- [x] SPF-007 Adapter Health Monitoring
- [x] SPF-008 Read-only Snapshots
- [ ] SPF-009 Validation and Schema Drift
- [ ] SPF-010 Regression, Operational Validation, and Documentation Closure

Current completion: **8/10 — 80%**.

Next production milestone: SPF-009 validates canonical contracts and detects schema drift without enabling Shopping writes or moving application state to Ubuntu.
<!-- SPF-008-CLOSE:END -->

<!-- AICONTROLCENTER:SPF-009:CLOSED -->
## SPF-009 Validation and Schema Drift Closure

- [x] SPF-009 — Validation and Schema Drift.
  - Runtime validator CLOSED.
  - Drift classifier CLOSED.
  - Authorization-first read-only schema drift monitoring CLOSED.
  - Negative/isolation/full regression CLOSED at 930 passed, 5 deselected.
- [ ] SPF-010 — Regression, operational validation and documentation closure.
- Foundation progress after SPF-009: **9/10 = 90%**.

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
- Foundation roadmap milestone: COMPLETE.
- Next production milestone: post-Foundation read-only external integration and monitoring.
- Write enablement is not part of Foundation closure and requires a future explicit milestone.

<!-- BEGIN AICONTROLCENTER:SRI-03 -->
## SRI — Shopping External Read Integration

### Current sprint — SRI-03

SRI-03 implements the real external WooCommerce READ path while AIControlCenter remains the single Control Plane.

### Next milestone — Controlled Production DNS

1. Inventory a platform-controlled domain and DNS provider.
2. Select the canonical Shopping production hostname.
3. Configure or validate the A record against the current public IPv4.
4. Keep AAAA absent until IPv6 ingress is validated.
5. Validate CAA permits the selected public CA.
6. Reconfirm external HTTP ingress.
7. Validate staging TLS.
8. Perform one controlled Production TLS issuance.
9. Make Caddy reboot-safe with certificate storage continuity.
10. Connect the real WooCommerce upstream.
11. Create a dedicated WooCommerce READ-only credential.
12. Execute one canonical production GET.
13. Run Shopping and full regression suites.
14. Complete Git documentation and Notion closure.

### Following milestones

- SRI-04 — WordPress CMS real READ adapter
- SRI-05 — Health Schema Snapshot and Drift operational integration
- SRI-06 — Final regression and operational closure

After SRI closes the next program is DPL — Deployment Package.
<!-- END AICONTROLCENTER:SRI-03 -->

<!-- SRI-06B-R1:ROADMAP -->
## SRI Closure and Next Program

### Shopping External Read Integration

- SRI-01 external integration inventory: CLOSED.
- SRI-02 production read policy: CLOSED.
- SRI-03 WooCommerce production READ integration: CLOSED.
- SRI-04 WordPress CMS production READ integration: CLOSED.
- SRI-05 Health, Schema, Snapshot and Drift integration: CLOSED.
- SRI-06 regression, documentation, Git and handoff closure: final release baseline.

### Next program

DPL, Deployment Package, is the next production program.
DPL consumes the SRI architecture without moving business logic or application state to Ubuntu.
Codex performs implementation under Architect-owned specifications and acceptance gates.
<!-- END SRI-06B-R1 -->

<!-- AICONTROLCENTER:DPL-01:START -->
## DPL — Deployment Package Program

- [x] DPL-01 — Inventory, ownership, architecture decisions, blockers and
  sprint plan.
- [x] DPL-02 — Versioned package/report JSON Schemas and registry; read-only
  inventory, validation, diff, dry-run, readiness and audit.
- [ ] DPL-03 — Enforced read/plan/apply package and dependency separation.
- [ ] DPL-04 — Launchd-native Mac inventory and health inspection.
- [ ] DPL-05 — Canonical Host Caddy, Colima, Compose and Commerce ingress
  validation.
- [ ] DPL-06 — Typed Ubuntu read-only action contract and deny-by-default
  policy; activation separately gated.
- [ ] DPL-07 — Immutable evidence, compatibility and release-candidate
  validation.
- [ ] DPL-08 — Regression, operational documentation and production
  authorization review.

### Production milestones

1. Read-only contract milestone: DPL-02 schemas and reports accepted.
2. Architecture boundary milestone: DPL-03 dependency rules enforced.
3. Mac readiness milestone: DPL-04 and DPL-05 pass without mutation.
4. Optional worker contract milestone: DPL-06 typed allowlist accepted.
5. Release candidate milestone: DPL-07 evidence and compatibility pass.
6. Authorization milestone: DPL-08 review completes.

No milestone itself authorizes production activation. Apply and production
writes require a separate explicit authorization.
<!-- AICONTROLCENTER:DPL-01:END -->

## DPL-04 Closure and Next Milestone

DPL-04A through DPL-04D are CLOSED and DPL-04 is CLOSED.
M2 is `READINESS_ACCEPTED`; activation is `ACTIVATION_NOT_STARTED`.
M2-P1 is CLOSED and pilot authorization policy is AVAILABLE. The next milestone
is M2-P2 Controlled Sandbox Pilot Activation and Evidence. Persistent SQLite
audit implementation is required before any broader mutable deployment.
Production activation remains `NOT_AUTHORIZED`.
