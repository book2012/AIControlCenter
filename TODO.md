# TODO

## Deployment Package Lifecycle

- [x] DPL-04B Mac-only sandbox adapter
- [x] DPL-04C durable audit architecture decision
- [ ] DPL-04D

M2 is not complete. The persistent audit adapter is not implemented and
production activation is `NOT_AUTHORIZED`.

Sprint 16

- Doctor

Sprint 17

- Logs

Sprint 18

- Backup Verify

Sprint 19

- Worker Health

Sprint 20

- Backup Execute

## Sprint 21

- [ ] Scheduler
- [ ] Heartbeat
- [ ] Job Registry
- [ ] Scheduler API
- [ ] Job Runner
- [ ] Scheduler Tests

## Sprint 23

- [ ] Knowledge Registry
- [ ] Markdown Loader
- [ ] Knowledge Search
- [ ] Knowledge API
- [ ] Telegram /knowledge
- [ ] BrainAgent Knowledge Context

<!-- AI_SHOPPING_PLATFORM_START -->
## AI Shopping Platform

### Current

- Complete Shopping Control Plane Production Gate
- Run full regression test suite
- Commit Shopping bootstrap
- Implement Commerce Catalog Port
- Implement Mock Product Catalog

### High

- Build WordPress and WooCommerce virtual environment
- Implement WooCommerce read-only adapter
- Add authentication
- Add secrets validation
- Add approval workflow
- Add audit logging

### Medium

- AI Product Generator
- AI SEO Writer
- AI Product Description
- AI Category Generator
- n8n automation
- Shopping Dashboard

### Technical Debt

- [ ] TECH-002 Replace `datetime.utcnow()` with timezone-aware UTC timestamps

- Review duplicated router registrations in core/api/app.py
- [ ] TECH-003 Review FastAPI and Starlette TestClient compatibility
- Handle dependency changes in a dedicated regression Sprint
<!-- AI_SHOPPING_PLATFORM_END -->

## API Quality

- Completed duplicate router registration cleanup
- Added route uniqueness regression protection
- FastAPI TestClient deprecation warning remains a separate dependency task

## Shopping Catalog

- Completed Mock Product Catalog
- Completed product list and detail APIs
- Next: WordPress and WooCommerce virtual environment
- Next: WooCommerce read-only catalog adapter

## Shopping Catalog

- Completed Mock Product Catalog
- Completed product list and detail APIs
- Next: WordPress and WooCommerce virtual environment
- Next: WooCommerce read-only catalog adapter

## Shopping Catalog

- Completed Mock Product Catalog
- Completed product list and detail APIs
- Next: WordPress and WooCommerce virtual environment
- Next: WooCommerce read-only catalog adapter

<!-- SHOPPING_M4_START -->

## Shopping Platform Next Tasks

- Complete M4 Production Gate
- Commit M4 implementation and documentation
- Build Shopping Homepage
- Add product search and filtering
- Add Shopping Dashboard summary
- Design AI Product Generator
- Implement draft and approval workflow
- Acquire or connect a user-owned domain
- Configure Production HTTPS
- Validate ARM64 deployment on Mac mini M4
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## Shopping Platform Next Tasks

- Complete M5 Git closeout
- Define AI Product Draft schema
- Implement AI Product Generator in read-only draft mode
- Add approval state machine
- Add audit event model
- Design controlled WooCommerce write gate
- Add Shopping Dashboard Storefront status
- Acquire user-owned Production domain
- Configure public HTTPS
- Validate Mac mini M4 ARM64 deployment
<!-- SHOPPING_M5_END -->

<!-- AI_SHOPPING_STOREFRONT_V016_TODO -->
## Current Production Tasks

- Push `feature/shopping-platform-bootstrap`
- Review and merge the storefront baseline
- Create the v0.16.0 release candidate tag after merge
- Build Mac mini Production Control Plane
- Migrate AIControlCenter from Ubuntu development runtime
- Reconfigure the production WordPress URL
- Add production HTTPS and operational monitoring

<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## Mac Control Plane

Status: **Complete**

- [x] Headless reboot recovery
- [x] 24-hour Shadow observation
- [x] Canonical manager reconciliation
- [x] Transactional apply and rollback
- [x] launchd settle policy
- [x] Final apply validation
- [x] Final restart validation
- [x] Documentation closeout


### PI-001 Dashboard Shadow API Integration

- [x] Dashboard Control Plane JSON contract
- [x] Shadow read-only enforcement
- [x] Immutable Runtime metadata
- [x] Runtime metadata schema validation
- [x] Metadata-gated Runtime activation
- [x] Production Runtime commit verification
- [x] Health endpoint HTTP 200
- [x] Dashboard endpoint HTTP 200
- [x] Dashboard write probe HTTP 405

## Next Sprint — AIControlCenter Platform

### P0

- [ ] Consolidate AIControlCenter REST contracts
- [x] Connect Dashboard to the Mac Control Plane
- [ ] Connect Homepage to Dashboard APIs
- [ ] Define Ubuntu Worker read-only JSON APIs
- [ ] Add Worker health monitoring
- [ ] Add Backup Verify monitoring

### P1

- [ ] Connect n8n read-only workflows
- [ ] Add Notion project synchronization
- [ ] Define Production write approval Gate
- [ ] Define Production cutover and rollback runbooks

Production writes remain disabled until monitoring
and validation are stable.
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->

<!-- AICONTROLCENTER:PI-002:START -->
## PI-002 Follow-up Tasks

### Completed

- [x] Define Ubuntu worker read-only JSON API contract
- [x] Add Worker health monitoring
- [x] Add Production Dashboard worker integration
- [x] Add structured worker failure continuity
- [x] Validate system LaunchDaemon and immutable runtime

### Next Sprint

- [ ] Configure the dedicated SSH key for non-interactive LaunchDaemon access
- [ ] Verify host-key configuration for `192.168.1.7`
- [ ] Validate `/opt/aihomedatacenter/scripts/commands/worker-health-json.sh` remotely
- [ ] Confirm healthy worker JSON in `GET /dashboard`
- [ ] Replace deprecated `datetime.utcnow()` usage
- [ ] Review Starlette and httpx compatibility warnings
<!-- AICONTROLCENTER:PI-002:END -->

<!-- AICONTROLCENTER:PI-003:START -->
## PI-003 Closure and PI-004 Priorities

### PI-003 Completed

- [x] Ubuntu boot recovery validation
- [x] Immich automatic activation
- [x] Nextcloud automatic activation
- [x] Mac standalone health validation
- [x] Optional worker failure continuity

### PI-004 P0

- [ ] Inventory all Mac mini services and ports
- [ ] Validate AIControlCenter after Mac reboot
- [ ] Deploy and validate Mac Homepage
- [ ] Validate Ollama and AI provider health
- [ ] Validate n8n deployment status
- [ ] Define service manifest and ownership
- [ ] Automate install, update, restart and rollback

### Ubuntu Backlog

- [ ] BACKLOG-U01 Dedicated SSH identity
- [ ] BACKLOG-U02 Healthy Ubuntu telemetry
- [ ] BACKLOG-U03 Detailed storage monitoring
- [ ] BACKLOG-U04 Backup verification
- [ ] BACKLOG-U05 Worker lifecycle automation
<!-- AICONTROLCENTER:PI-003:END -->

<!-- AICONTROLCENTER:PI-004:START -->
## PI-004 Closure and PI-005 Priorities

### PI-004 Completed

- [x] Mac service inventory
- [x] Mac standalone service manifest
- [x] Homepage Production contract alignment
- [x] LaunchDaemon reboot recovery
- [x] Production Gate and evidence

### PI-005 P0

- [ ] Service manifest schema validation
- [ ] Reusable deployment command interface
- [ ] Ollama native macOS supervisor contract
- [ ] Ollama health and model inventory API
- [ ] Deployment rollback validation
<!-- AICONTROLCENTER:PI-004:END -->

<!-- AICONTROLCENTER:PI-005:START -->
## PI-005

- [x] Close Mac Service Deployment Platform baseline.
- [x] Keep all deployment execution disabled.
- [x] Preserve Ollama as a replaceable Mac-only runtime.

## Next Priority

- [ ] PI-006: approved Ollama installation and system LaunchDaemon deployment.
- [ ] Add Ollama health and model inventory adapter to AIControlCenter.
<!-- AICONTROLCENTER:PI-005:END -->

<!-- PI-009:START -->
## PI-009 Remaining Operational Tasks

- [x] Implement governance operations domain.
- [x] Implement append-only SQLite adapter.
- [x] Implement application projection service.
- [x] Implement GET-only operations API.
- [x] Implement fail-soft Dashboard panel.
- [x] Complete targeted and full regression.
- [x] Verify production database content hash is unchanged.
- [x] Prepare Production Activation Gate.
- [x] Prepare Notion handoff document.
- [ ] Synchronize handoff into Notion.
- [ ] Obtain explicit production migration approval.
- [ ] Obtain explicit scheduler activation approval.
- [ ] Perform post-activation operational validation.
- [ ] Confirm rollback procedure and observation window.
<!-- PI-009:END -->

<!-- PI-009-OPERATIONS-FINAL:BEGIN -->
## PI-009 Close Checklist

- [x] Production operation schema migrated
- [x] Production database backup verified
- [x] Manual operation validated
- [x] Production UTC clock implemented
- [x] JSON-first runner implemented
- [x] Per-operation lock implemented
- [x] Automatic retry disabled
- [x] Automatic catch-up disabled
- [x] Automatic remediation disabled
- [x] Automatic restore disabled
- [x] Full regression passed
- [x] Git implementation state clean
- [x] Documentation updated

## PI-010 Next Operational Work

- [ ] Define explicit operation cadence
- [ ] Review disabled launchd definitions
- [ ] Approve scheduler installation
- [ ] Activate under controlled gate
- [ ] Observe initial scheduled executions
- [ ] Verify unload and rollback procedure
<!-- PI-009-OPERATIONS-FINAL:END -->

<!-- PI-010-HEADLESS-PRODUCTION-CLOSE-2026-07-23 -->
## PI-010 Completion

- [x] Explicit governance cadence
- [x] JSON one-shot runner
- [x] Headless Production scheduler
- [x] Dedicated governance audit snapshot capability
- [x] Dedicated SQLite online backup verifier
- [x] Production run_succeeded validation
- [x] Append-only audit correlation
- [x] Database and crontab rollback backups
- [x] Uninstall and reinstall rollback validation
- [x] MappingProxy-safe serialization
- [x] Full regression
- [x] Canonical documentation close

## Next

- [ ] Start Shopping Platform Foundation
- [ ] Define WordPress and WooCommerce read-only adapters
- [ ] Define AIControlCenter shopping domain boundaries

<!-- BEGIN AICONTROLCENTER SPF-002 TODO -->
## Shopping Platform Foundation Sprint 1

Completed:

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture Foundation

Next:

- [ ] SPF-003 Shopping package and read-only port skeleton

Queued:

- [ ] SPF-004 Canonical JSON Schema v1
- [ ] SPF-005 Deny-by-default capability registry
- [ ] SPF-006 Read adapter contracts
- [ ] SPF-007 Adapter health monitoring
- [ ] SPF-008 Read-only snapshot retrieval
- [ ] SPF-009 Validation and schema drift detection
- [ ] SPF-010 Regression and operational close

Sprint tasks completed: 2 of 10
Sprint tasks remaining: 8
Shopping write operations enabled: No
<!-- END AICONTROLCENTER SPF-002 TODO -->

<!-- SPF-003:START -->
## Current Shopping Task State

- [x] SPF-003 — Import-safe package and read-only port foundation
- [ ] SPF-004 — Canonical JSON Schema v1

SPF-003 validation: 6 targeted tests and 747 full regression tests passed.

Implementation commit: `fd52aad1d9af9d056d80d8f7d6170605ea0d11b2`.
<!-- SPF-003:END -->


<!-- AICONTROLCENTER-SPF-004-CLOSED -->
## Shopping Platform Foundation Task State

- [x] SPF-004 Canonical JSON Schema v1
- [ ] SPF-005 Capability Registry — deny by default

SPF-004 closure validation:

- [x] 15 canonical contracts registered
- [x] local-only registry loading
- [x] fail-closed validation
- [x] targeted suite: 6 passed
- [x] full regression: 753 passed
- [x] production unchanged
- [x] writes disabled

<!-- SPF-005-CLOSE:BEGIN -->
## Shopping Platform Foundation

- [x] Close SPF-005 Capability Registry deny-by-default.
- [x] Verify 11 READ capabilities and 9 reserved WRITE capability identifiers.
- [x] Verify fail-closed unknown, write, mismatch, malformed decision, and policy exception behavior.
- [x] Pass 22 targeted tests and 775 full regression tests.
- [ ] Implement SPF-006 Read Adapter Contracts.
- [ ] Keep all Shopping write operations disabled.
- [ ] Preserve Ubuntu as a stateless infrastructure worker.
<!-- SPF-005-CLOSE:END -->

<!-- SPF-006-CLOSE:BEGIN -->
## Shopping Platform Foundation

- [x] Close SPF-006 Read Adapter Contracts.
- [x] Preserve CommerceReadPort and CmsReadPort as authoritative interfaces.
- [x] Verify Commerce/CMS capability isolation.
- [x] Verify vendor-neutral import and dependency boundaries.
- [x] Pass 28 targeted tests.
- [x] Pass 803 full regression tests.
- [ ] Implement SPF-007 Adapter Health Monitoring.
- [ ] Keep Shopping WRITE operations disabled.
- [ ] Keep Ubuntu stateless and free of Shopping business logic.
<!-- SPF-006-CLOSE:END -->

<!-- SPF-007-CLOSE:BEGIN -->
## Shopping Platform Foundation

- [x] Close SPF-007 Adapter Health Monitoring.
- [x] Establish vendor-neutral health states and failure taxonomy.
- [x] Enforce fail-closed timeout and dependency behavior.
- [x] Reject raw vendor error metadata.
- [x] Implement deterministic stateless health aggregation.
- [x] Pass 34 targeted health tests.
- [x] Pass 837 full regression tests.
- [ ] Implement SPF-008 Read-only Snapshots.
- [ ] Keep Shopping WRITE operations disabled.
- [ ] Keep Ubuntu stateless and free of Shopping business logic.
<!-- SPF-007-CLOSE:END -->

<!-- SPF-008-CLOSE:BEGIN -->
## Shopping Platform Foundation

- [x] Close SPF-008 Read-only Snapshots.
- [x] Implement deterministic canonical snapshot normalization.
- [x] Enforce immutable snapshot read models.
- [x] Enforce authorization before repository access.
- [x] Verify fail-closed authorization behavior.
- [x] Verify no persistence, vendor refresh, or write surface.
- [x] Pass 35 targeted snapshot tests.
- [x] Pass 872 full regression tests.
- [ ] Implement SPF-009 Validation and Schema Drift.
- [ ] Keep Shopping WRITE operations disabled.
- [ ] Keep Ubuntu stateless and free of Shopping business logic.
<!-- SPF-008-CLOSE:END -->

<!-- AICONTROLCENTER:SPF-009:CLOSED -->
## SPF-009 Validation and Schema Drift Closure

- [x] Close SPF-009 runtime JSON Schema validation.
- [x] Close SPF-009 conservative schema drift classification.
- [x] Enforce authorization-before-schema-discovery.
- [x] Preserve `discover_schema(*, context, adapter_name)` as the authoritative read contract.
- [x] Validate fail-closed, sanitization, immutability and isolation behavior.
- [x] Pass 58 targeted tests and 930 full-regression tests with 5 deselected.
- [ ] Execute SPF-010 final production-readiness and operational closure.

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
- SPF-010 final closure: COMPLETE.
- Foundation remaining tasks: 0.
- Next planning task: define post-Foundation read-only integration scope before any mutation capability.

<!-- BEGIN AICONTROLCENTER:SRI-03 -->
## Active — SRI-03 External Read Integration

### Completed

- [x] Canonical WooCommerce read wrapper
- [x] Canonical normalization and validation
- [x] GET-only bounded read transport
- [x] Caddy runtime validation
- [x] Mac LAN ingress validation
- [x] External WAN HTTP 80 validation
- [x] DDNS and public IPv4 validation
- [x] Authoritative ipTIME CAA blocker analysis

### Controlled Production DNS

- [ ] Inventory a platform-controlled domain and DNS provider
- [ ] Select the canonical Shopping production hostname
- [ ] Configure or validate the production A record
- [ ] Keep AAAA absent until IPv6 ingress is validated
- [ ] Validate CAA issuance policy
- [ ] Validate staging TLS
- [ ] Perform one controlled Production TLS issuance

### SRI-03 closure

- [ ] Make Caddy reboot-safe
- [ ] Confirm the WooCommerce upstream
- [ ] Create a dedicated WooCommerce READ-only credential
- [ ] Execute one production canonical GET
- [ ] Validate canonical schema output
- [ ] Run Shopping regression
- [ ] Run full regression
- [ ] Verify Git status and exact scope
- [ ] Finalize README CHANGELOG MASTER ROADMAP PROJECT_HISTORY and TODO
- [ ] Produce Notion handoff
- [ ] Commit and push SRI-03 closure
<!-- END AICONTROLCENTER:SRI-03 -->

<!-- SRI-06B-R1:TODO -->
## Post-SRI Execution Queue

### DPL preparation

- Define deployment package architecture and immutable artifact contract.
- Define Codex task templates with scope, acceptance criteria, tests and rollback rules.
- Preserve Host Caddy as the sole public edge.
- Preserve protected credentials outside Git.

### Operational hardening

- Implement reusable recovery and forward-reconciliation modules in AIControlCenter.
- Add persisted evidence schema validators.
- Add scheduled read-only Health, Schema, Snapshot and Drift execution.
- Add route ownership tests for /healthz and WordPress fallback.

### Restrictions

- No Shopping business write until a separately approved write sprint.
- No AI workload or application business logic on Ubuntu.
- No architecture change through Codex without Architect approval.
<!-- END SRI-06B-R1 -->

<!-- AICONTROLCENTER:DPL-01:START -->
## Active — DPL Deployment Package

The earlier `Active — SRI-03 External Read Integration` section is historical
and superseded. SRI is COMPLETE at
`ba6fdb6a69ee9398b44fdd0810102b078c38c7f8`; its final recorded regression
baseline is `984 passed, 5 deselected`.

### DPL-01

- [x] Inventory deployment and platform artifacts.
- [x] Record ownership and architecture decisions.
- [x] Register DPL-B01 through DPL-B06.
- [x] Define DPL-01 through DPL-08.
- [x] Preserve production-write and activation prohibition.

### Complete — DPL-02 / M1

- [x] Define canonical versioned DPL package/report JSON Schemas and registry.
- [x] Implement read-only inventory, validation, readiness, GET composition,
  and audit-ready evidence.
- [x] Exclude `UbuntuWorkerClient.execute`.
- [x] Activate no Ubuntu adapter.
- [x] Define one canonical Host Caddy to Commerce ingress contract.
- [x] Deny POST, PUT, PATCH, and DELETE across DPL API routes.

### Next — DPL-03

- [ ] Enforce read/plan/apply package and dependency separation.

Production activation remains NOT AUTHORIZED.
<!-- AICONTROLCENTER:DPL-01:END -->

## DPL-04 Closed / M2 Next Action

- [x] Close DPL-04A, DPL-04B, DPL-04C and DPL-04D.
- [x] Accept M2 readiness from the canonical passing fixture.
- [ ] Obtain separate operator authorization for a controlled non-production
      sandbox pilot.
- [ ] Implement persistent SQLite deployment audit before broader mutable
      deployment.

M2 activation has not started. Production activation is not authorized.
