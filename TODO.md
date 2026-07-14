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

- Review duplicated router registrations in core/api/app.py
- Review FastAPI TestClient deprecation warning
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

<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:START -->
## Mac Control Plane Next Tasks

            ### P0 — Production Gates

            - [ ] Run Headless Reboot Recovery Gate
            - [ ] Confirm LaunchDaemon before GUI login
            - [ ] Confirm post-reboot PID change
            - [ ] Confirm process user `kyouhan`
            - [ ] Confirm Health HTTP `200`
            - [ ] Confirm write probe HTTP `405`
            - [ ] Confirm listener remains localhost-only
            - [ ] Confirm Runtime matches Git HEAD

            ### P1 — Shadow Observation

            - [ ] Collect 24-hour Health results
            - [ ] Collect CPU and memory metrics
            - [ ] Collect restart count
            - [ ] Measure stdout and stderr log growth
            - [ ] Define warning budget
            - [ ] Replace deprecated `datetime.utcnow()`

            ### P2 — Integration

            - [ ] Connect Ubuntu Worker JSON APIs read-only
            - [ ] Connect Mac Dashboard to Shadow API
            - [ ] Validate n8n read-only workflows
            - [ ] Write Cutover runbook
            - [ ] Write rollback runbook
            - [ ] Update Notion project status

            - Generated: `2026-07-14T03:31:53+00:00`
- Branch: `sprint/mac-control-plane-foundation`
- Commit: `db4d93a2652a704dfa9a7e149623064adb961504`
- Runtime commit: `db4d93a2652a`
<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:END -->

<!-- AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:START -->
## Next Production Tasks

            ### P0

            - [ ] Update `manage-shadow-daemon.py`
              to reproduce the canonical plist
            - [ ] Add installer regression tests
            - [ ] Begin 24-hour Shadow observation
            - [ ] Validate log rotation and growth limits

            ### P1

            - [ ] Connect Ubuntu Worker JSON APIs read-only
            - [ ] Validate Dashboard Shadow integration
            - [ ] Complete cutover runbook
            - [ ] Complete rollback runbook
            - [ ] Update Notion project status

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
## Shadow Observation Tasks

### P0

- [ ] Collect at least 276 samples
- [ ] Reach a minimum 23.5-hour window
- [ ] Maintain at least 99.5% successful samples
- [ ] Confirm no public listener exposure
- [ ] Confirm no root application process
- [ ] Generate final observation report

### P1

- [ ] Reconcile `manage-shadow-daemon.py`
- [ ] Validate Ubuntu Worker JSON APIs
- [ ] Complete cutover and rollback runbooks
- [ ] Update Notion

Configured: `2026-07-14T04:19:41+00:00`
<!-- AICONTROLCENTER:SHADOW_OBSERVATION:END -->
