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

### M3-A1C

M2 controlled pilot validation and M3-A1A through M3-A1C are closed. SQLite
online backup, separate-target restore and deterministic recovery validation
were verified only with pytest temporary databases. The operational audit
database was not created, an operational backup schedule was not activated,
an operational restore was not performed, persistent audit writer activation
is not started, and Production activation is `NOT_AUTHORIZED`. Next: M3-A2
Durable Permit and Replay State.

### M3-A1B

M2 controlled pilot validation, M3-A1A and M3-A1B are closed. The separate
append-only SQLite writer is implemented and verified only with pytest-owned
temporary databases. No operational database was created, operational writer
activation is not started, persistent Production audit writes are not enabled,
and Production activation is `NOT_AUTHORIZED`. Next: M3-A1C Backup, Restore
and Recovery Validation.

### M2-P3

M2-P3 is closed. Immutable activation evidence is validated before a fixed,
evidence-derived plan can reach an injected test-only rollback port. Exactly
one controlled activation and rollback were validated only in pytest-owned
temporary sandboxes. Persistent host activation is not started, persistent
host rollback and persistent SQLite audit are not implemented, and Production
activation is `NOT_AUTHORIZED`. Next: M3-A1 Durable SQLite Audit Adapter.

### DPL-04C

DPL-04C is closed. AIControlCenter owns durable deployment audit on the Mac
Control Plane. Pure immutable audit contracts define canonical JSON, stable
digests and tamper-evident hash-chain verification behind a replaceable
`DurableAuditPort`. The selected future adapter is an append-only SQLite ledger;
no adapter, database, persistence or API write path is implemented. DPL-04A,
DPL-04B and DPL-04C are closed; DPL-04D is ready, M2 is not complete and
production activation is `NOT_AUTHORIZED`.

### DPL-04B

The Mac-only sandbox adapter implements the typed non-production executor port
for development, test and staging. Its root must be explicitly injected; the
default remains deny-only. It writes only canonical JSON manifest/evidence
files below that confined root and performs no command, network, service,
Ubuntu, repository or production operation. Evidence is not durably persisted
as audit state, and production activation remains unauthorized.

Next Sprint

- DPL-04D

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

<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## Mac Control Plane Production Baseline

The Mac mini M4 is the always-on Brain and the
single AIControlCenter Control Plane.

Current validated baseline:

- Branch: `sprint/mac-control-plane-foundation`
- Commit: `1e102c001c28108bee9583294abee77ce7d43643`
- Runtime commit: `1e102c001c28`
- Runtime: `/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/venvs/1e102c001c28`
- Supervisor:
  `system/com.aicontrolcenter.api.shadow`
- Application user: `kyouhan`
- Listener: `127.0.0.1:18100`
- Health contract: HTTP `200`
- Mutating request contract: HTTP `405`
- Mode: `shadow-read-only`
- GUI login required: `false`
- Transactional canonical apply: implemented
- Transactional rollback: implemented
- launchd bootout settle policy: 2 seconds
- Final restart: `19761 → 19842`

Shadow observation:

- Duration: `23.535` hours
- Samples: `283/283` passed
- Failed samples: `0`
- Success ratio: `100.0%`
- PID transitions: `0`
- Observation SHA-256:
  `a1c79121ff04699d0ee717d72aa158e81c954fe84387c0689a1c5c08fb83519d`
- Summary SHA-256:
  `c980df46e94b40b0b72086a55501f2cad4f748ad98d4f6ec7ceea9c15a02c8de`

Control Plane implementation is complete.
Production write cutover remains blocked pending
an explicit Production approval.
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->

## Dashboard Shadow Control Plane

AIControlCenter exposes a read-only Control Plane status contract through the Mac mini Shadow API.

Runtime endpoint:

- Listener: `127.0.0.1:18100`
- Health: `GET /health`
- Dashboard: `GET /dashboard`
- Write requests: rejected with HTTP `405`

The Dashboard response includes:

- Control Plane service identity
- Shadow operating mode
- Read-only enforcement state
- Local listener address
- Commit-specific Runtime metadata
- Runtime metadata validation status

Runtime identity is loaded from an immutable `metadata.json` file generated during the commit-specific Runtime build.

Dashboard requests do not execute Git, `launchctl`, or shell commands.

Runtime activation is allowed only after:

1. Dependency installation succeeds.
2. Application import succeeds.
3. The test suite succeeds.
4. Runtime metadata is generated.
5. Runtime metadata schema validation succeeds.

Current validated PI-001 Runtime:

- Commit: `ba8d2c9772577863c3c040d01654c4f011e2d45e`
- Short commit: `ba8d2c977257`
- Health status: HTTP `200`
- Dashboard status: HTTP `200`
- Write probe: HTTP `405`

<!-- AICONTROLCENTER:PI-002:START -->
## Ubuntu Worker Monitoring

AIControlCenter exposes Ubuntu worker monitoring through the Mac mini Control Plane.

Production endpoints:

- `GET /health` — Control Plane availability
- `GET /dashboard` — integrated Control Plane and worker status
- `GET /workers` — worker monitoring data

The Production Dashboard monitors `ubuntu-main` by default.

Worker transport failures are represented as structured JSON with `OPTIONAL_UNAVAILABLE` status. The Dashboard remains available with HTTP `200`.

Production baseline:

- Implementation commit: `39dc5c3db72c9ac1592fc3920012aba3eacd23cd`
- Immutable implementation runtime: `39dc5c3db72c`
- Supervisor: system LaunchDaemon
- Worker configuration: `config/workers.mac-production.yaml`
- Worker environment contract: `root:staff 640`
- Regression result: `412 passed, 5 deselected`
<!-- AICONTROLCENTER:PI-002:END -->

<!-- AICONTROLCENTER:PI-003:START -->
## Mac Standalone and Optional Ubuntu Worker

AIControlCenter runs independently on the Mac mini when the Ubuntu worker is offline.

Validated behavior:

- Control Plane health remains `ONLINE`.
- `GET /health` remains HTTP `200`.
- `GET /dashboard` remains HTTP `200`.
- The offline Ubuntu worker is reported as `OPTIONAL_UNAVAILABLE`.
- Worker errors remain structured JSON.

Ubuntu service recovery:

- Docker is enabled and active after boot.
- Immich containers start automatically.
- Nextcloud containers start automatically.
- Required containers use `restart: unless-stopped`.

Ubuntu may remain powered off until its infrastructure services are required.
<!-- AICONTROLCENTER:PI-003:END -->

<!-- AICONTROLCENTER:PI-004:START -->
## Mac Standalone Production Baseline

PI-004 validated AIControlCenter as an independent Mac mini Production platform.

- `/health` returned HTTP `200`.
- `/dashboard` returned HTTP `200`.
- `/homepage/status` returned HTTP `200`.
- Platform status remained `ONLINE`.
- Ubuntu remained optional and powered off.
- Storage and backup were reported as optional external capabilities.
- LaunchDaemon recovery after Mac reboot was validated.
<!-- AICONTROLCENTER:PI-004:END -->

<!-- AICONTROLCENTER:PI-005:START -->
## Mac Service Deployment Platform

PI-005 provides dependency-free JSON interfaces for service manifest validation, read-only planning, Mac service inspection, desired/actual diff, Ollama dry-run generation, and installation approval requests.

Ollama remains uninstalled and execution remains disabled. Actual installation requires a separate approved Sprint.
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
## Model Governance

AIControlCenter exposes a read-only model-governance endpoint:

`GET /api/governance/models`

The endpoint compares the AIControlCenter-approved model registry with the
inventory observed from Ollama.

Current Production baseline:

- mode: `read-only`
- default policy: `DENY`
- approved models: `0`
- observed models: `0`
- violations: `0`
- write operations allowed: `false`

Operational check:

`curl -fsS http://127.0.0.1:18100/api/governance/models`

The API supports `GET` only. Model pull, create, copy, and delete operations are
outside the approved PI-007 scope and remain denied.
<!-- AICONTROLCENTER:PI-007:END -->

## PI-008 — Model Governance Audit and Dashboard Integration

PI-008 is complete and active in Production.

Capabilities:

- immutable governance audit snapshots
- append-only SQLite persistence
- historical compliance comparison
- read-only audit query services
- GET-only audit APIs
- Dashboard governance audit integration
- metadata-backed Production runtime identity
- Git-independent Production restart and rollback compatibility

Production identity:

- commit: `b9ad351a7241e521c8964218f59724fcb04db93c`
- active runtime: `b9ad351a7241`
- rollback runtime: `0352e396f329`

Validation:

- full suite: `636 passed, 5 deselected`
- Production health: online
- Dashboard: online and read-only
- Ollama models: `0`
- governance write methods: `0`
- audit database: outside runtime
- append-only SQLite triggers: valid

<!-- PI-009:START -->
## PI-009 Governance Audit Operations

PI-009 adds read-only operational visibility for governance audit
snapshot and SQLite online-backup verification workflows.

Key behavior:

- router-level GET `/operations` presentation;
- Dashboard key `governance_audit_operations`;
- strict API errors and panel-local Dashboard fail-soft behavior;
- missing database or schema produces an UNKNOWN read-only projection;
- no write actions are exposed;
- production migration and scheduler activation remain disabled.

Validated baseline:

- 17 targeted tests passed;
- 710 tests passed, 5 deselected;
- production database SHA-256 remained unchanged;
- WAL content remained unchanged.
<!-- PI-009:END -->

<!-- PI-009-OPERATIONS-FINAL:BEGIN -->
## PI-009 Governance Operations — Closed

PI-009 was closed on 2026-07-22 with a JSON-first,
one-shot governance operation runner owned by
AIControlCenter.

Supported operations:

- governance_audit_snapshot
- sqlite_online_backup_verification

Runner interface:

    .venv/bin/python -m core.governance.operations.scheduler       --operation <operation> --once --json

Production composition:

- SQLiteOperationsEventRepository
- SystemUTCClock
- AutomationExecutor
- BackupVerifyService
- OperationsApplicationService

Safety boundaries:

- no automatic retry
- no automatic catch-up
- no automatic remediation
- no automatic restore
- no launchd activation
- no scheduling policy embedded in the runner
- Mac mini remains the Control Plane
- Ubuntu remains a stateless infrastructure worker

Validation baseline:

- implementation commit:
  d1072aa35fb5034c1097923fd7f6d7643132460b
- targeted tests: 14 passed
- full regression:
  717 passed, 5 deselected, 427 warnings
- Production database and WAL unchanged

Cadence policy and controlled launchd activation are
deferred to PI-010.
<!-- PI-009-OPERATIONS-FINAL:END -->

<!-- PI-010-HEADLESS-PRODUCTION-CLOSE-2026-07-23 -->
## PI-010 Production Governance Scheduler

PI-010 closed on 2026-07-23.

The Mac mini Control Plane runs AIControlCenter governance operations through a managed headless user crontab adapter.

Governance audit snapshots run daily at 03:10 Asia/Seoul. SQLite online backup verification runs Sunday at 04:10 Asia/Seoul.

The snapshot capability performs read-only database validation and creates an immutable JSON evidence artifact. The backup capability uses the SQLite online backup API and validates quick_check, row counts, and the resulting artifact hash.

Automatic retry, catch-up, remediation, and restore remain disabled. Ubuntu remains a stateless infrastructure worker.

<!-- BEGIN AICONTROLCENTER SPF-002 README -->
## Shopping Platform Foundation

Status: Architecture Foundation complete

Shopping is a governed AIControlCenter domain.
WordPress provides headless CMS capabilities.
WooCommerce provides replaceable commerce capabilities.

Sprint 1 remains read-only.
Product, customer, order, price, inventory, and publish writes are disabled.

Architecture documentation:

- `docs/architecture/shopping-platform-foundation.md`
- `docs/architecture/shopping-context-map.md`
- `docs/architecture/shopping-ownership-matrix.md`
- `docs/security/shopping-write-approval-gates.md`
- `docs/contracts/shopping-json-v1.md`

Next gated task: SPF-003 Shopping package and read-only port skeleton.
<!-- END AICONTROLCENTER SPF-002 README -->

<!-- SPF-003:START -->
## Shopping Platform Foundation Status

SPF-003 is closed. The repository contains an import-safe Shopping package foundation, seven asynchronous keyword-only read or compute ports, provisional JSON-first contracts, legacy `CommerceCatalogPort` compatibility, and deny-by-default write governance.

Validation: 6 targeted tests passed; 747 full regression tests passed with 5 deselected.

Next milestone: **SPF-004 — Canonical JSON Schema v1**.

Implementation commit: `fd52aad1d9af9d056d80d8f7d6170605ea0d11b2`.
<!-- SPF-003:END -->


<!-- AICONTROLCENTER-SPF-004-CLOSED -->
## Shopping Platform Foundation — SPF-004

SPF-004 Canonical JSON Schema v1 is complete.

Current Shopping foundation capabilities:

- 15 canonical read-contract schemas
- versioned schema registry
- explicit local-only schema loading
- Draft 2020-12 runtime validation
- fail-closed unknown-contract behavior
- strict unknown-field rejection
- schema discriminator validation for snapshots
- targeted schema suite: 6 passed
- full regression suite: 753 passed

Production and Shopping write operations remain disabled.

Next foundation task: **SPF-005 Capability Registry — deny by default**.

<!-- SPF-005-CLOSE:BEGIN -->
## Shopping Platform Foundation — SPF-005 CLOSED

SPF-005 establishes deny-by-default capability governance inside AIControlCenter.

- 11 executable READ capabilities
- 9 reserved non-executable WRITE capabilities
- immutable capability registry
- policy evaluation required for registered reads
- unknown and write capabilities denied before policy execution
- policy exceptions fail closed without leaking vendor messages
- 22 targeted tests passed
- 775 full regression tests passed
- Shopping writes remain disabled

Shopping Platform Foundation progress: **5/10** after SPF-005 closure.

Next: **SPF-006 Read Adapter Contracts**.
<!-- SPF-005-CLOSE:END -->

<!-- SPF-006-CLOSE:BEGIN -->
## Shopping Platform Foundation — SPF-006 CLOSED

SPF-006 establishes replaceable read adapter contract boundaries inside AIControlCenter.

- Commerce and CMS ports remain authoritative.
- Adapter contracts are vendor-neutral.
- Canonical Shopping contracts are required at the adapter boundary.
- Commerce and CMS capability bindings remain isolated.
- Vendor DTO escape is prohibited.
- Business logic and policy ownership inside adapters are prohibited.
- Shopping WRITE methods remain prohibited.
- Live vendor connections remain disabled.
- 28 targeted tests passed.
- 803 full regression tests passed.

Shopping Platform Foundation progress after SPF-006: **6/10 — 60%**.

Next: **SPF-007 Adapter Health Monitoring**.
<!-- SPF-006-CLOSE:END -->

<!-- SPF-007-CLOSE:BEGIN -->
## Shopping Platform Foundation — SPF-007 CLOSED

SPF-007 establishes vendor-neutral, read-only adapter health monitoring inside AIControlCenter.

- Health probe normalization is JSON-safe and sanitized.
- Health states are HEALTHY, DEGRADED, and UNAVAILABLE.
- Health aggregation is deterministic and stateless.
- UNAVAILABLE has highest aggregation precedence.
- Empty adapter input fails closed as UNAVAILABLE.
- Probe-layer retry and persistence are disabled.
- Health does not replace capability authorization or policy evaluation.
- Shopping WRITE operations remain disabled.
- Live vendor transport remains disabled.
- 34 targeted tests passed.
- 837 full regression tests passed.

Shopping Platform Foundation progress after SPF-007: **7/10 — 70%**.

Next: **SPF-008 Read-only Snapshots**.
<!-- SPF-007-CLOSE:END -->

<!-- SPF-008-CLOSE:BEGIN -->
## Shopping Platform Foundation — SPF-008 CLOSED

SPF-008 establishes read-only snapshot normalization and query orchestration inside AIControlCenter.

- Canonical snapshot payloads are normalized deterministically.
- Snapshot read models are immutable and detached from source mutation.
- Snapshot queries are authorized before repository access.
- Denied or failed authorization produces zero repository calls.
- Snapshot repository failures are sanitized.
- No snapshot creation or persistence is enabled.
- No vendor refresh is performed by snapshot queries.
- Shopping WRITE operations remain disabled.
- Production live registration remains disabled.
- 35 targeted tests passed.
- 872 full regression tests passed.

Shopping Platform Foundation progress after SPF-008: **8/10 — 80%**.

Next: **SPF-009 Validation and Schema Drift**.
<!-- SPF-008-CLOSE:END -->

<!-- AICONTROLCENTER:SPF-009:CLOSED -->
## SPF-009 Validation and Schema Drift Closure

- Shopping Platform Foundation progress: **9/10 tasks complete (90%)**.
- SPF-009 adds canonical runtime schema validation, deterministic fail-closed validation results, conservative schema drift classification, and authorization-first read-only drift monitoring.
- Validation targeted suite: **58 passed**.
- Full regression: **930 passed, 5 deselected**.
- Implementation commit: `3fa21878e72cdb9608a728a1c676e70fb70b5717`.
- No production, Ubuntu, vendor-write, schema-write, or application-state changes were enabled.
- Next foundation task: **SPF-010 regression, operational validation, documentation and production-readiness closure**.

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
- Current milestone: Shopping Platform Foundation 10/10 CLOSED — Production Readiness Gate Passed.
- Next milestone: post-Foundation read-only external integration and monitoring planning.

<!-- SRI-06B-R1:README -->
## SRI Production Baseline and Codex Workflow

Shopping External Read Integration is the production READ baseline for AIControlCenter.

- Mac mini M4 remains the always-on Control Plane.
- Ubuntu remains a stateless on-demand infrastructure worker.
- WooCommerce is the Commerce Engine.
- WordPress is the CMS Engine.
- AIControlCenter owns policy, orchestration, normalization, evidence and operational decisions.
- Production products and orders remain zero and no business fixture was introduced.

### Runtime READ paths

- WooCommerceReadTransportSession to WooCommerceRESTAdapter to canonical commerce models.
- WordPressRESTAdapter to ContentSnapshot and ContentSnapshotPage.
- ExternalReadObserver executes Health, Schema, Snapshot and Drift.

### Development execution model

AI Home Datacenter Architect retains architecture and production authority.
Codex acts as implementation executor for approved repository tasks.
Architecture changes, production writes and scope expansion require explicit Architect review.
<!-- END SRI-06B-R1 -->

<!-- AICONTROLCENTER:DPL-01:START -->
## Deployment Package Lifecycle

DPL is the current program after SRI closure.

`inventory → validate → diff → dry-run plan → readiness → audit`

DPL v1 uses immutable, versioned JSON desired-state packages and observation
reports. DPL-02 is read-only and does not apply, install, restart, bootstrap,
execute rollback, write to production or run generic Ubuntu commands.

The Mac mini M4 remains the single Control Plane, Host Caddy remains the only
public edge, and Ubuntu remains an optional stateless worker. Production
activation is not authorized.

See `docs/deployment/DPL-01-INVENTORY-ASSESSMENT.md`.
<!-- AICONTROLCENTER:DPL-01:END -->

## DPL-04D M2 Operational Readiness

DPL-04A, DPL-04B, DPL-04C, DPL-04D and DPL-04 are CLOSED. The pure injected-
evidence gate accepted the canonical sandbox fixture:
`M2 READINESS_ACCEPTED`. This is not deployment: `M2 ACTIVATION_NOT_STARTED`
and Production activation is `NOT_AUTHORIZED`. M2-P1 is CLOSED and pilot
authorization policy is AVAILABLE. The next milestone is M2-P2 Controlled
Sandbox Pilot Activation and Evidence. Persistent SQLite deployment audit is
required before broader mutable deployment.
