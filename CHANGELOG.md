# CHANGELOG

## 2026-07-29 — M3-A1C SQLite Backup, Restore and Recovery

- Added immutable backup, restore, manifest, receipt, finding and recovery
  report contracts.
- Added explicit-path SQLite online backup, separate-target restore and
  deterministic complete-ledger validation.
- Added fail-closed tamper, idempotency, path, compatibility and dependency
  validation plus deployment and operations documentation.
- Used only pytest temporary databases; no operational database, backup
  schedule or restore was created or performed.
- Persistent writer activation is not started and Production activation is
  `NOT_AUTHORIZED`. Next: M3-A2 Durable Permit and Replay State.

## 2026-07-29 — M3-A1B Append-Only SQLite Audit Writer

- Added a separate existing-file-only SQLite writer with serialized append,
  full-chain validation, deterministic receipts and idempotent retry.
- Enforced preconfigured WAL, schema/index/trigger validation, read-back
  verification and rollback on failure without creation, migration or repair.
- Closed M3-A1B using only pytest temporary databases; no operational database
  or Production write was created or enabled.
- Next: M3-A1C Backup, Restore and Recovery Validation.

## 2026-07-29 — M3-A1A SQLite Read-Only Integrity Foundation

- Added explicit Mac application-state path policy and deterministic,
  canonical, read-only SQLite integrity reports.
- Added schema, metadata, integrity, sequence, hash-chain, privacy and
  Production-authorization inspection without append behavior.
- Closed M3-A1A with zero operational databases, writes, migrations, repairs,
  commands, network access, Ubuntu changes or Production activations.
- Next: M3-A1B Append-Only SQLite Audit Writer.

## 2026-07-29 — M2-P3 Pilot Evidence and Rollback Validation

- Added immutable deterministic evidence and rollback contracts.
- Added fail-closed validation, evidence-derived planning and an injected
  rollback port with replay denial.
- Validated exactly one rollback in a pytest-owned temporary sandbox.
- Closed M2 without persistent-host, Production, Ubuntu, network, command,
  database or audit writes.

## 2026-07-29 — M2-P2 Controlled Sandbox Pilot Activation

- Added immutable activation contracts, deterministic canonical receipts and a
  dependency-injected activation service.
- Added fixed typed operation ordering and fail-closed one-use permit
  reservation with replay denial after success or failure.
- Validated exactly one controlled pilot in a pytest-owned temporary sandbox.
- Added six safe fixtures plus failure, binding, safety, boundary and
  compatibility coverage.
- Closed M2-P2 without persistent host activation, durable audit persistence,
  Ubuntu access or Production authorization.

## 2026-07-29 — M2-P1 Controlled Sandbox Pilot Authorization

### Added

- Immutable pilot request, operator approval, decision, permit, validation
  report and restriction contracts.
- Deterministic default-deny authorization service with exact DPL-03C and
  DPL-04D evidence binding, typed safe operations, separation of duties and a
  bounded one-use permit.
- Six secret-free fixtures and operator/deployment authorization guidance.

### Status and safety

DPL-04 is CLOSED, M2 readiness is ACCEPTED and M2-P1 is CLOSED. Pilot
authorization policy is AVAILABLE; pilot activation is NOT STARTED. No
executor, adapter, persistent audit/nonce, sandbox artifact, network, Ubuntu,
service, API write or activation operation was performed. Persistent SQLite
audit is NOT IMPLEMENTED and Production activation remains `NOT_AUTHORIZED`.
Next: M2-P2 Controlled Sandbox Pilot Activation and Evidence.

## 2026-07-29 — DPL-04C Durable Audit Architecture Decision

- Added immutable audit event, envelope, append, integrity and read-only query
  contracts plus the replaceable `DurableAuditPort`.
- Defined deterministic canonical JSON identities and tamper-evident hash-chain
  verification without persistence.
- Accepted a future Mac-only append-only SQLite adapter; no database, migration,
  audit write, nonce write or production activation was added.
- Closed DPL-04C and marked DPL-04D ready while M2 remains incomplete.

## 2026-07-29 — DPL-04B Mac-Only Sandbox Adapter

- Added an explicit-root, non-production `MacSandboxAdapter` implementing the
  DPL-04A executor port for safe sandbox verification, preparation and
  evidence collection.
- Added canonical immutable JSON materialization, same-root atomic replacement,
  digest read-back, deterministic/idempotent results and strict symlink/path,
  secret and executable-payload rejection.
- Preserved zero commands, network, Ubuntu, repository and production writes;
  durable audit and production activation remain unavailable.

## 2026-07-29 — DPL-04A Typed Non-Production Executor Ports

- Added schema-validated executor capability, request, validation-report and
  result contracts plus typed executor, capability-provider and policy ports.
- Restricted ownership to the Mac Control Plane and environments to
  development, test and staging; production and Ubuntu ownership are rejected.
- Added a typed operation allowlist and deny-only default composition without a
  concrete real executor, API route, runtime command or production write.

## 2026-07-29 — DPL-03D Simulation-Only Apply Composition

- Added deterministic non-production simulation, a process-local replay
  guard, typed fake executor, and versioned receipt/report contracts.
- Closed DPL-03 without real deployment, API, production, Ubuntu, network,
  subprocess, or persistent-state capability. M2 remains open.

## 2026-07-16 — PI-001 Dashboard Shadow API Integration

### Added

- Added the Dashboard Control Plane JSON contract.
- Added immutable runtime metadata with schema validation.
- Added commit-specific runtime metadata generation.
- Added runtime metadata to the Dashboard response.
- Added metadata-gated runtime activation.

### Validated

- `GET /health` returns HTTP 200.
- `GET /dashboard` returns HTTP 200.
- `POST /dashboard` returns HTTP 405.
- Runtime commit matches Git HEAD.
- Shadow API remains read-only on `127.0.0.1:18100`.


<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## 2026-07-16 — Mac Control Plane Baseline

### Added

- Commit-specific Mac Runtime
- Non-root system LaunchDaemon
- Canonical launchd manager and executor
- Transactional canonical apply
- Transactional rollback
- launchd bootout settle policy
- Restart and recovery validation
- Read-only Shadow API monitoring

### Validation

- Final commit: `1e102c001c28108bee9583294abee77ce7d43643`
- Runtime: `1e102c001c28`
- Observation:
  `283/283` samples passed
- Observation duration:
  `23.535` hours
- Health: HTTP `200`
- Write protection: HTTP `405`
- Listener: `127.0.0.1:18100`
- Final restart:
  `19761 → 19842`

### Safety

- AIControlCenter runs as `kyouhan`.
- Installed plist and runner remain root-owned.
- The API remains localhost-only.
- Mutating requests remain blocked.
- Production write cutover remains disabled.
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->

## v0.9.0

Added

- Telegram Brain
- Telegram Polling
- Command Router
- Status Action
- Provider Fallback
- Conversation Memory
- SQLite
- Storage Registry
- Backup Registry

## Unreleased

### Planned

- Brain Scheduler
- Internal Heartbeat
- Job Registry
- Scheduler API
- Automation Foundation

## Scheduler Foundation

- Heartbeat
- Job Registry
- Scheduler Loop
- Job Runner
- Scheduler API
- Background Service

## Sprint 21-22

Added:

- Scheduler Heartbeat
- Job Registry
- Scheduler Loop
- Job Runner
- Scheduler API
- Telegram /scheduler
- Background Scheduler Service
- MemoryManager
- Working Memory
- Long-term Memory
- Memory API
- Telegram /memory
- Memory Search
- BrainAgent Memory Context

## Knowledge Layer

- Knowledge Registry
- Markdown Loader
- Knowledge Index
- Knowledge Search
- Telegram /knowledge
- Knowledge API
- BrainAgent Knowledge Context

## Planner Agent

- PlannerAgent
- Planner API
- Telegram /plan
- PlanStore
- Plan Review

## Automation Engine

- AutomationExecutor
- SafeExecutionPolicy
- AutomationQueue
- Automation API
- Telegram /automation
- Scheduler integration

## Homepage Integration

- HomepageStatusService
- /homepage/status API
- Telegram /homepage command

## Production Hardening

- systemd Services
- Service Health
- Configuration Validation
- Graceful Shutdown
- Operations Manual

## v1.0.0

### Added

- Production-ready AIControlCenter Brain platform
- FastAPI control plane
- OpenAI and Google provider support
- Provider fallback
- BrainAgent and status actions
- Scheduler and background jobs
- Conversation, working, and long-term memory
- Knowledge indexing and search
- Planner Agent
- Safe Automation Engine
- Telegram operations interface
- Homepage status API
- systemd and launchd deployment templates
- Installation, update, and readiness automation

### Architecture

- Mac mini M4 is the final Brain runtime
- Ubuntu remains an optional storage and backup Worker
- AIControlCenter operates standalone without Ubuntu

<!-- AI_SHOPPING_PLATFORM_START -->
## 2026-07-12 AI Shopping Platform Bootstrap

### Added

- AIControlCenter Shopping domain
- Shopping health endpoint
- Shopping readiness endpoint
- Shopping capabilities endpoint
- Shopping configuration
- Shopping API schemas
- Shopping tests
- Shopping architecture documentation
- Shopping API documentation
- Shopping testing documentation
- Shopping deployment documentation
- Shopping runbook

### Safety

- Catalog writes disabled by default
- AI execution disabled by default
- Automation execution disabled by default
- Human approval required by default
- Production target set to Mac mini M4

### Validation

- Shopping targeted tests passing
- Existing API regression tests passing
- Shopping route smoke tests passing
<!-- AI_SHOPPING_PLATFORM_END -->

## 2026-07-12 API Router Cleanup

### Fixed

- Removed duplicate FastAPI router registrations
- Removed duplicate OpenAPI operation identifiers
- Added API route uniqueness regression tests

### Validation

- Shopping API routes remain available
- OpenAPI operation identifiers are unique
- Full regression suite passes

## 2026-07-12 Read-only Mock Product Catalog

### Added

- Product domain model
- Commerce Catalog Port
- Mock Commerce Catalog Adapter
- Paginated product list API
- Product detail API
- Product not-found response
- Product catalog unit and API tests

### Safety

- Product catalog remains read-only
- No WooCommerce write operations
- No AI execution
- No automation execution

## 2026-07-12 Read-only Mock Product Catalog

### Added

- Product domain model
- Commerce Catalog Port
- Mock Commerce Catalog Adapter
- Paginated product list API
- Product detail API
- Product not-found response
- Product catalog unit and API tests

### Safety

- Product catalog remains read-only
- No WooCommerce write operations
- No AI execution
- No automation execution

## 2026-07-12 Read-only Mock Product Catalog

### Added

- Product domain model
- Commerce Catalog Port
- Mock Commerce Catalog Adapter
- Paginated product list API
- Product detail API
- Product not-found response
- Product catalog unit and API tests

### Safety

- Product catalog remains read-only
- No WooCommerce write operations
- No AI execution
- No automation execution

<!-- SHOPPING_M4_START -->

## Shopping Platform M4 — Unreleased

### Added

- WooCommerce REST Adapter
- HTTP OAuth 1.0a development authentication
- HTTPS Basic Authentication support
- Adapter Factory
- Environment-driven Catalog Adapter selection
- Shopping Integration Status API
- Product Catalog API
- Product Detail API
- Category API
- WordPress and MariaDB Docker Compose runtime
- systemd Shopping EnvironmentFile support
- Shopping deployment and operations documentation

### Fixed

- Duplicate API Router registration
- WordPress Healthcheck variable escaping
- WordPress WORDPRESS_CONFIG_EXTRA Parse Errors
- Test environment leakage from live Shopping settings
- Canonical WooCommerce signing URL and internal connection URL separation

### Security

- WooCommerce API integration is read-only
- Secret files excluded from Git
- systemd runtime Secret permissions restricted
- Public HTTPS deferred until a user-owned domain is available
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## Shopping Platform M5 — Unreleased

### Added

- Featured Products API
- Product Search API
- Category, price, and stock filters
- Search pagination
- Product image URL contract
- WooCommerce representative image mapping
- Image placeholder fallback
- Modular AI Shopping Storefront Plugin
- WordPress AIControlCenter API client
- WordPress Presentation Cache
- Storefront shortcode
- Responsive Storefront CSS
- External AI Shopping page

### Fixed

- Storefront Renderer search UI integration
- Search API client query serialization
- Boolean stock parameter serialization
- WooCommerce image mapping tests
- Test helper contract inconsistencies
- Trailing whitespace and blank-line issues

### Security

- Storefront does not receive WooCommerce credentials
- WordPress calls read-only AIControlCenter endpoints
- Search input is sanitized
- Rendered output is escaped
- Business Logic remains in AIControlCenter
<!-- SHOPPING_M5_END -->

## [2026-07-13] Commit 19 - Homepage Curated Sections

### Added
- Homepage curated shopping sections
- NEW ARRIVALS
- BEST SELLERS
- TOP
- DRESS
- OUTER
- BAG
- SALE

### Changed
- Renderer supports multi-section homepage
- Homepage sections powered by Shopping Search API
- Homepage displays up to 8 products per section

<!-- AI_SHOPPING_STOREFRONT_V016_CHANGELOG -->
## 2026-07-13 — AI Shopping Storefront v0.16.0

### Added

- API-driven product detail route
- Product detail renderer and template
- Orange Coco Home v5 icons and hero asset
- Related product presentation

### Changed

- Established Orange Coco v6 as the canonical storefront UI
- Updated the storefront plugin to version 0.16.0
- Improved front-page structure and responsive layout

### Fixed

- Missing products now return HTTP 404
- Product status is set before WordPress headers render

### Removed

- Legacy `orange-coco-final.css`
- Legacy `orange-coco-final.js`
- Unused Home v4 and Home v5 CSS files
- Duplicate original hero image

### Git

- Feature commit: `a4d6098`

<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:START -->
## Unreleased — Mac Control Plane

            ### Added

            - Non-root system LaunchDaemon supervisor
            - Root-owned LaunchDaemon plist
            - Root-owned immutable runner installation
            - JSON-first supervisor status and lifecycle
            - Read-only Shadow API on `127.0.0.1:18100`

            ### Changed

            - Replaced the GUI-dependent LaunchAgent
              production design with a system LaunchDaemon.
            - Defined normal running state as port `18100`
              being owned by the active LaunchDaemon PID.
            - Restricted port-release validation to
              uninstall and bootout operations.

            ### Verified

            - Application user: `kyouhan`
            - Health response: HTTP `200`
            - Mutating request response: HTTP `405`
            - Localhost-only listener
            - Runtime and Git commit match
            - Secure plist and runner ownership
            - Automatic restart: `1661 → 1975`
            - Full Test Suite:
              313 passed, 5 deselected

            ### Pending

            - Headless reboot recovery
            - 24-hour Shadow observation
            - Ubuntu Worker read-only integration

            - Generated: `2026-07-14T03:31:53+00:00`
- Branch: `sprint/mac-control-plane-foundation`
- Commit: `db4d93a2652a704dfa9a7e149623064adb961504`
- Runtime commit: `db4d93a2652a`
<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:END -->

<!-- AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:START -->
## Unreleased — Headless Recovery

            ### Added

            - GUI-independent system LaunchDaemon recovery
            - Headless reboot recovery JSON Gate
            - System log path:
              `/var/log/aicontrolcenter`

            ### Fixed

            - Replaced GUI-dependent supervision
            - Recovered from launchd bootstrap error 5
            - Verified non-root process ownership
            - Verified Runtime and Git commit alignment

            ### Pending

            - Manager installer reconciliation
            - 24-hour Shadow observation
            - Production cutover decision

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
## Unreleased — Shadow Observation

### Added

- Five-minute Shadow observer
- JSON Lines operational telemetry
- CPU and RSS collection
- Runtime and Git commit validation
- Health and write-protection probes
- Observation summary Gate

### Pending

- Complete the 24-hour observation window
- Reconcile the canonical LaunchDaemon installer
- Production cutover approval

Configured: `2026-07-14T04:19:41+00:00`
<!-- AICONTROLCENTER:SHADOW_OBSERVATION:END -->

<!-- AICONTROLCENTER:PI-002:START -->
## 2026-07-17 — PI-002 Ubuntu Worker Health JSON Adapter

### Added

- Versioned Ubuntu worker health JSON contract
- Bounded SSH worker transport
- Ubuntu worker health adapter
- Production worker configuration selection
- Structured worker monitoring errors
- Dashboard worker health JSON integration
- Production worker environment loader
- Immutable runtime Production Gate evidence

### Changed

- `GET /dashboard` now monitors `ubuntu-main` by default.
- The canonical runner validates worker environment ownership, group and mode.
- The worker environment contract is `root:staff 640`.

### Verified

- Implementation commit: `39dc5c3db72c9ac1592fc3920012aba3eacd23cd`
- Runtime commit matched the implementation Git HEAD.
- system LaunchDaemon ran as `kyouhan:staff`.
- `GET /health` returned HTTP `200`.
- `GET /dashboard` returned HTTP `200`.
- Dashboard returned one `ubuntu-main` worker object.
- Worker errors were returned as structured JSON.
- Full regression: `412 passed, 5 deselected`.

### Pending

- Configure the dedicated SSH identity for the LaunchDaemon worker adapter.
- Validate a successful remote `worker-health-json.sh` response.
- Resolve Python and Starlette deprecation warnings.
<!-- AICONTROLCENTER:PI-002:END -->

<!-- AICONTROLCENTER:PI-003:START -->
## 2026-07-19 — PI-003 Ubuntu Worker Minimum Closure

### Changed

- Reclassified Ubuntu as an optional on-demand infrastructure worker.
- Prioritized Mac mini standalone Production operation.
- Deferred detailed Ubuntu telemetry and lifecycle automation.

### Verified

- Ubuntu reboot automatically activated Docker.
- Immich automatically restarted after Ubuntu boot.
- Nextcloud automatically restarted after Ubuntu boot.
- Required containers use `restart: unless-stopped`.
- Ubuntu was powered off after service recovery validation.
- AIControlCenter remained `ONLINE`.
- Health endpoint returned HTTP `200`.
- Dashboard endpoint returned HTTP `200`.
- `ubuntu-main` returned structured `OPTIONAL_UNAVAILABLE` status.
- Validated implementation runtime commit: `85e0d2186dcd9338dea4288e629092bd62f882e8`.

### Deferred

- Dedicated LaunchDaemon SSH identity
- Healthy Ubuntu telemetry
- Detailed storage and backup monitoring
- Worker lifecycle automation
<!-- AICONTROLCENTER:PI-003:END -->

<!-- AICONTROLCENTER:PI-004:START -->
## 2026-07-20 — PI-004 Mac Standalone Production Baseline

### Added

- Mac standalone Production service manifest.
- Homepage standalone projection contract.
- Explicit optional storage and backup metadata.

### Verified

- system LaunchDaemon automatic recovery after Mac reboot.
- immutable runtime and Git commit alignment.
- Health, Dashboard and Homepage HTTP `200`.
- Platform status `ONLINE` without Ubuntu.
- Full test suite passed.
- Final PI-004 Production evidence generated.
<!-- AICONTROLCENTER:PI-004:END -->

<!-- AICONTROLCENTER:PI-005:START -->
## PI-005 — Mac Service Deployment Platform

### Added

- Reusable Mac service manifest schema and dependency-free validator.
- Read-only deployment plan, service inspector, and desired/actual diff JSON interfaces.
- Ollama managed-service design and rollback-aware dry-run.
- SHA-256-bound approval request with expiry and action allowlist validation.

### Safety

- Ollama installation and model download remain disabled.
- All write operations require future approval and execution tooling.
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

### Added

- Canonical model-governance registry at
  `config/model-governance.json`.
- Default-deny, read-only registry loader.
- Immutable model-governance evaluation objects.
- Compliance evaluation for approved, missing, unapproved, digest-mismatch,
  and resource-policy states.
- Read-only `GET /api/governance/models` endpoint.
- Focused registry, evaluator, Ollama adapter, and API tests.

### Production

- Source commit:
  `39fe04e3330e398f38567efa58bddb39b9893756`
- Runtime release: `39fe04e3330e`
- Previous rollback release: `3679588b760c`
- Production health: `ONLINE`
- Ollama health: `ONLINE`
- Governance mode: `read-only`
- Default policy: `DENY`
- Write operations allowed: `false`
- Rollback readiness validated without performing an actual rollback.

### Technical Debt

- Existing Starlette/httpx test-client deprecation warning remains.
- Existing timezone-naive `datetime.utcnow()` warnings remain.
- These warnings did not block PI-007 and require a separate maintenance task.
<!-- AICONTROLCENTER:PI-007:END -->

## PI-008 — Model Governance Audit and Dashboard Integration

### Added

- canonical immutable governance audit snapshots
- deterministic SHA-256 snapshot identity
- SQLite migration and schema controls
- append-only audit repository
- audit snapshot service
- historical audit comparison service
- read-only audit query service
- GET-only governance audit API
- Dashboard governance audit read model
- Production runtime provenance environment

### Changed

- Production runner now uses release metadata instead of mutable Git HEAD
- Production restart no longer requires a clean Git working tree
- Dashboard now exposes `model_governance_audit`

### Fixed

- rollback failure caused by runtime commit and Git HEAD coupling
- unsafe symlink replacement procedure
- false-negative Dashboard validation caused by a 5-second timeout
- invalid direct diagnostic helper import

### Production

- active commit: `b9ad351a7241e521c8964218f59724fcb04db93c`
- active runtime: `b9ad351a7241`
- rollback runtime: `0352e396f329`
- full suite: `636 passed, 5 deselected`
- Production closure gate: passed

<!-- PI-009:START -->
## PI-009 — Governance Audit Operations Visibility

### Added

- Governance operations domain, event model and projection policy.
- Append-only SQLite operations event repository.
- Read-only governance operations presentation service.
- GET-only governance operations API route.
- Fail-soft Dashboard operations panel.
- Missing-schema and missing-database UNKNOWN projections.
- Production activation and Notion handoff documents.

### Changed

- Governance audit leakage assertions are scoped to the
  `model_governance_audit` panel so unrelated operation identifiers do
  not produce false positives.

### Safety

- No write API was added.
- No automatic migration, retry, restore or remediation was added.
- Production database content and WAL content remained unchanged.
<!-- PI-009:END -->

<!-- PI-009-OPERATIONS-FINAL:BEGIN -->
## 2026-07-22 — PI-009 Governance Operations Final Close

### Added

- Production UTC-aware SystemUTCClock adapter.
- JSON-first one-shot governance operation runner.
- Explicit Production dependency composition.
- Per-operation non-blocking execution locks.
- Ephemeral-path composition tests.

### Validated

- 14 targeted tests passed.
- 717 full-suite tests passed.
- 5 tests remained intentionally deselected.
- 427 warnings remained at the existing baseline.
- Production database and WAL were unchanged.
- No LaunchAgent was written or activated.

### Deferred to PI-010

- Explicit automated cadence policy.
- launchd installation and activation.
- First scheduled-run observation.
<!-- PI-009-OPERATIONS-FINAL:END -->

<!-- PI-010-HEADLESS-PRODUCTION-CLOSE-2026-07-23 -->
## 2026-07-23 — PI-010 Production Scheduler

Added explicit governance cadence, managed headless cron deployment, append-only Production audit validation, rollback backups, and uninstall/reinstall validation.

Added GovernanceAuditSnapshotExecutor for read-only JSON audit snapshots and SQLiteOnlineBackupVerifier for SQLite online backup, quick_check, row-count, and SHA-256 validation.

Both governed Production operations reached run_succeeded. The managed cron adapter remained active after rollback validation, and the full regression suite passed.

<!-- BEGIN AICONTROLCENTER SPF-002 CHANGELOG -->
## 2026-07-23 — Shopping Platform Foundation

### Added

- Shopping bounded-context architecture.
- AIControlCenter, WordPress, WooCommerce, and Ubuntu ownership matrix.
- Read-only adapter boundaries.
- Canonical `shopping.v1` JSON contract.
- SG-0 through SG-9 security gates.

### Safety

- AIControlCenter remains the Shopping Control Plane.
- WordPress remains a headless CMS.
- WooCommerce remains a replaceable commerce engine.
- Ubuntu remains a stateless infrastructure worker.
- No Shopping write capability was enabled.
<!-- END AICONTROLCENTER SPF-002 CHANGELOG -->

<!-- SPF-003:START -->
## 2026-07-23 — SPF-003 Shopping Read-Only Port Foundation

### Added

- Import-safe Shopping package boundaries.
- Seven transport-neutral read-only or compute-only Protocol interfaces.
- Provisional JSON-first Shopping contract aliases.
- Import, typing, signature, compatibility, write-deny, and side-effect tests.

### Changed

- Migrated `core/shopping/ports.py` to `core/shopping/ports/__init__.py` byte-for-byte.
- Preserved the existing `CommerceCatalogPort` import contract.

### Validation and Safety

- Targeted tests: 6 passed.
- Full regression: 747 passed with 5 deselected.
- Production infrastructure was not modified.
- Shopping write operations remain disabled.

Next milestone: **SPF-004 — Canonical JSON Schema v1**.

Implementation commit: `fd52aad1d9af9d056d80d8f7d6170605ea0d11b2`.
<!-- SPF-003:END -->


<!-- AICONTROLCENTER-SPF-004-CLOSED -->
## 2026-07-23 — SPF-004 Canonical JSON Schema v1

### Added

- 15 canonical Shopping contract schemas.
- shared schema definitions and error envelope.
- versioned `registry.json`.
- explicit Python schema registry loader.
- fail-closed contract payload validator.
- pinned `jsonschema==4.26.0` and `referencing==0.37.0`.
- six canonical schema validation tests.

### Validation

- targeted tests: 6 passed.
- full regression: 753 passed.
- remote schema references denied.
- automatic schema JSON loading during import denied.

### Fixed

Gate-harness false positives encountered during SPF-004 were classified and corrected:

- `TEST_ASSERTION_FALSE_POSITIVE_GLOBAL_PATH_BLOCK`
- `TEST_ASSERTION_FALSE_POSITIVE_STRING_PREFIX_COUNT`
- `TEST_HARNESS_EMBEDDED_NEWLINE_DEDENT_DEFECT`

No production defect was attributed to these harness failures.

<!-- SPF-005-CLOSE:BEGIN -->
## 2026-07-23 — SPF-005 Capability Registry deny-by-default

### Added
- Static immutable Shopping capability registry owned by AIControlCenter.
- Eleven canonical READ capabilities with vendor-neutral identifiers.
- Read authorization orchestration through `PolicyDecisionPort`.
- Denial and compatibility tests covering all registered reads and reserved writes.

### Security
- Unknown capabilities deny by default.
- Reserved WRITE capabilities are non-executable and denied before policy evaluation.
- Request and policy decision capability mismatches fail closed.
- Policy evaluation exceptions are normalized to `shopping.policy.evaluation_error`.
- Vendor exception messages are not exposed through authorization errors.

### Validation
- 22 targeted Shopping capability tests passed.
- 775 full regression tests passed.
- Production unchanged.
- Ubuntu unchanged.
- Shopping write operations remain disabled.

### Recovery Notes
- `TEST_HARNESS_LITERAL_INDENTATION_MISMATCH` affected an SPF-005-05 patch harness only and was recovered with AST-based source targeting.
- `POLICY_EXCEPTION_FAIL_CLOSED_HARDENING` is the actual security hardening introduced by SPF-005-05.

Implementation commit: `f807cc0dfb8a27d2bf387bdc3dd897e4fe331953`.
<!-- SPF-005-CLOSE:END -->

<!-- SPF-006-CLOSE:BEGIN -->
## 2026-07-23 — SPF-006 Read Adapter Contracts

### Added
- Commerce adapter contract conformance validation.
- CMS adapter contract conformance validation.
- JSON-first Commerce and CMS contract manifests.
- Commerce/CMS isolation and compatibility tests.

### Architecture
- `CommerceReadPort` and `CmsReadPort` remain the authoritative callable interfaces.
- Adapter implementations may not redefine platform business contracts.
- SPF-005 capability registry remains authoritative for capability bindings.
- Canonical AIControlCenter domain contracts are required across adapter boundaries.

### Safety
- Vendor DTO escape is prohibited.
- Adapter-owned policy evaluation is prohibited.
- Adapter-owned business logic is prohibited.
- WRITE-like public adapter methods are prohibited.
- Live WooCommerce and WordPress connections remain disabled.
- Production and Ubuntu were not modified.

### Validation
- Targeted: 28 passed.
- Full regression: 803 passed.

Implementation commit: `fd1bbe2ff212e9eeb442562ffeed32bed97c1072`.
<!-- SPF-006-CLOSE:END -->

<!-- SPF-007-CLOSE:BEGIN -->
## 2026-07-23 — SPF-007 Adapter Health Monitoring

### Added
- Vendor-neutral health probe normalization.
- Health states for healthy, degraded, and unavailable adapters.
- Vendor-neutral health failure taxonomy.
- Sanitized health failure detail codes.
- Stateless deterministic health aggregation.
- JSON-compatible monitoring snapshots.
- End-to-end timeout and failure compatibility tests.

### Architecture
- AIControlCenter owns adapter monitoring and routing signals.
- Health remains separate from authorization and policy evaluation.
- Aggregation precedence is UNAVAILABLE, then DEGRADED, then HEALTHY.
- Empty aggregation input fails closed as UNAVAILABLE.
- Probe retry, scheduler ownership, and persistent health state remain outside the health normalization layer.

### Safety
- Raw vendor exception text is rejected from monitoring metadata.
- Credential-bearing error payloads are prohibited.
- Shopping WRITE methods remain disabled.
- Live vendor transport remains disabled.
- Production and Ubuntu were not modified.

### Validation
- Targeted: 34 passed.
- Full regression: 837 passed.

Implementation commit: `63263b734ead4eb083f9b91923f4b41c3b644e34`.
<!-- SPF-007-CLOSE:END -->

<!-- SPF-008-CLOSE:BEGIN -->
## 2026-07-23 — SPF-008 Read-only Snapshots

### Added
- Canonical snapshot normalization contract.
- Deterministic canonical JSON serialization.
- Immutable snapshot read representation.
- Read-only snapshot query orchestration.
- Authorization-before-repository enforcement.
- Isolation and immutability validation.

### Architecture
- AIControlCenter owns snapshot governance and read orchestration.
- `SnapshotRepositoryPort` remains the authoritative repository boundary.
- Snapshot creation and persistence remain classified as writes.
- Schema validation remains deferred to SPF-009.
- Ubuntu remains free of Shopping application state.

### Safety
- Authorization denial prevents repository access.
- Authorization failures fail closed.
- Repository failures are sanitized.
- Vendor refresh, persistence, production registration, and Shopping writes remain disabled.

### Validation
- Targeted: 35 passed.
- Full regression: 872 passed.

Implementation commit: `d8859a3706a087f88be513e32097b22c9a8ec3d6`.
<!-- SPF-008-CLOSE:END -->

<!-- AICONTROLCENTER:SPF-009:CLOSED -->
## SPF-009 Validation and Schema Drift Closure

### Added

- Canonical Draft 2020-12 runtime schema validator with deterministic `VALID`, `INVALID`, and `ERROR` results.
- Local-only `referencing.Registry` schema resolution with remote-reference rejection.
- Consumer-safety schema drift classifier with four explicit drift states.
- Read-only schema drift monitor using authorization-before-discovery and the authoritative `context` plus `adapter_name` discovery contract.
- Negative, isolation, immutability, sanitization, compatibility, and full-regression coverage.

### Validation

- 58 SPF-009 targeted tests passed.
- 930 full-regression tests passed with 5 deselected.
- Production, Ubuntu and platform write operations remained unchanged and disabled.

<!-- AICONTROLCENTER:SPF-010:CLOSED -->
## SPF-010 — Shopping Platform Foundation Production Readiness Closure

- Status: CLOSED
- Shopping Platform Foundation: 10/10 (100%)
- Production Readiness Gate: PASSED for the read-only Foundation.
- Closed SPF-010 and the Shopping Platform Foundation.
- Validated 233 Shopping tests.
- Full regression: 930 or more passed, 5 deselected, 0 failed, 0 errors.
- Read-only operational smoke validation: PASSED.
- AIControlCenter remains the single Control Plane on Mac mini M4.
- Ubuntu Server remains a stateless infrastructure worker only.
- Production write operations remain disabled.
- Automatic schema adoption and automatic schema migration remain disabled.
- Any future mutation or write capability requires a separate sprint and explicit production gate.

<!-- BEGIN AICONTROLCENTER:SRI-03 -->
## Unreleased — SRI-03 External Read Integration

### Added

- Canonical WooCommerce CommerceReadPort integration.
- Lossless raw WooCommerce read path for canonical normalization.
- ProductSnapshot and OrderSummary canonical normalization and schema validation.
- GET-only bounded WooCommerce read transport.
- Caddy ingress configuration on the Mac Control Plane.

### Validated

- Caddy runtime and Mac LAN ingress.
- DDNS and public IPv4 consistency.
- External WAN TCP 80 through an LTE or 5G request returning HTTP 200.
- DNS A, AAAA, CNAME, and CAA issuance state.
- Authoritative ipTIME parent CAA restriction.

### Architecture decisions

- Provider-owned DDNS is not the production canonical TLS identity.
- Root cause: `PARENT_CAA_PROHIBITS_PUBLIC_CA_ISSUANCE`.
- Production TLS requires a platform-controlled DNS namespace.

### Safety

- Shopping writes remain disabled.
- Production ACME retries against the blocked ipTIME hostname are stopped.
- No Ubuntu Shopping business logic or application state was introduced.
<!-- END AICONTROLCENTER:SRI-03 -->

<!-- SRI-06B-R1:CHANGELOG -->
## Shopping External Read Integration Closure

### Added

- Production WooCommerce GET-only integration with protected read credential.
- Generic core/cms boundary and WordPress published post and page adapter.
- Canonical CMS models and normalization.
- ExternalReadObserver with Health, Schema, Snapshot and Drift.
- Sanitized persisted JSON operational evidence.

### Production validation

- WooCommerce products: 0.
- WooCommerce orders: 0.
- WordPress published posts: 1.
- WordPress published pages: 5.
- Full repository regression: 984 passed and 5 deselected.

### Failure prevention ledger

- F25 CLOSED: lifecycle semantics replace physical invocation count assumptions.
- F26 CLOSED: launchd authority does not require a fixed plist installation path.
- F27 CLOSED: health route ownership is explicit.
- F28 CLOSED: shared namespace permissions are not the per-service secret boundary.
- F29 CLOSED: annotation symbols are not assumed to be runtime exports.
- F30 CLOSED: domain snapshot normalization is not used for generic cross-domain observations.
- F31 CLOSED: secret absence is checked before local secret references are cleared.
- F32 CLOSED: credential prefix substrings are not treated as complete credential values.
- F33 CLOSED: staged diff hygiene is authoritative because unstaged diff checks do not include untracked file content.
<!-- END SRI-06B-R1 -->

<!-- AICONTROLCENTER:DPL-01:START -->
## 2026-07-28 — DPL-01 Architecture and Documentation

### Added

- Canonical DPL-01 inventory, assessment, blockers and sprint plan.
- DPL architecture decision covering ownership, immutable contracts,
  read/plan/apply separation, platform boundaries and legacy Linux policy.
- Repository agent instructions preserving the approved architecture and
  production-write prohibition.

### Documented

- DPL bounded context and lifecycle.
- SRI closure baseline and current DPL program state.
- DPL-01 through DPL-08 roadmap and production authorization milestones.

No code, configuration, Compose, schema, test, runtime or production change was
performed.
<!-- AICONTROLCENTER:DPL-01:END -->

## 2026-07-29 — DPL-04D M2 Operational Readiness

### Added

- Immutable M2 evidence, check, finding, report and decision contracts.
- Pure deterministic thirteen-category readiness gate and four safe fixtures.
- M2 non-production sandbox runbook and go/no-go checklist.

### Status and safety

DPL-04A through DPL-04D and DPL-04 are CLOSED. The canonical passing fixture
records `M2 READINESS_ACCEPTED`; `M2 ACTIVATION_NOT_STARTED`. No executor,
Ubuntu, runtime, API, persistent audit, production write or activation was
performed. Production activation remains `NOT_AUTHORIZED`.
