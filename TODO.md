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
