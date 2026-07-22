# TODO

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
