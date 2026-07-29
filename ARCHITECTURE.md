# AI Home Datacenter Architecture

## M3-A2C Permit and Replay Recovery Boundary

The Mac Control Plane owns authoritative replay state. M3-A2A read-only
inspection remains intact, M3-A2B writing remains operationally disabled, and
M3-A2C adds separate explicit-path online backup, restore, exact recovery and
concurrency validation. Ubuntu owns no permit, nonce, replay, backup or
recovery state. All writable validation used pytest temporary paths. M3-A1 and
M3-A2A through M3-A2C are closed; no operational database, backup schedule,
restore or writer is active, and Production activation is `NOT_AUTHORIZED`.
M3-A3 Operational Monitoring and Alerts is next.

## M3-A1C SQLite Audit Recovery Boundary

`core.deployment.audit_sqlite_recovery` is a separate Mac Control Plane
boundary over M3-A1A inspection and M3-A1B schema contracts. Explicit-path
SQLite online backup, canonical manifest binding, separate-target restore and
deterministic recovery comparison are fail-closed and operationally disabled.
Ubuntu owns no authoritative backup or recovery state. M2 and M3-A1A through
M3-A1C are closed after pytest-only validation; no operational database,
backup schedule or restore exists, persistent writer activation is not
started, and Production activation is `NOT_AUTHORIZED`. M3-A2 is next.

## M3-A1B Append-Only SQLite Audit Writer Boundary

`core.deployment.audit_sqlite_writer` is a separate AIControlCenter-owned Mac
Control Plane adapter that appends canonical audit events to an explicitly
injected, pre-existing SQLite ledger. It cannot create, migrate or repair a
database and does not weaken `core.deployment.audit_sqlite`, which remains
read-only. WAL, schema, append-only triggers and the full hash chain are
validated before each serialized append. M2, M3-A1A and M3-A1B are closed.
Only pytest temporary databases were used; operational activation and
Production writes remain prohibited. M3-A1C is next.

## M2 Pilot Evidence and Rollback Boundary

`core.deployment.pilot_activation` and `pilot_evidence` are AIControlCenter-
owned Mac Control Plane boundaries. M2-P3 validates immutable activation
evidence and derives fixed rollback steps before an injected test-only port can
act. Production code has no filesystem rollback adapter. One controlled
activation and rollback ran only below pytest temporary roots; persistent host
activation is not started, persistent host rollback is not implemented and
Production activation remains `NOT_AUTHORIZED`.

## M2 Pilot Authorization Boundary

`core.deployment.pilot_authorization` is a pure AIControlCenter-owned policy
boundary on the Mac Control Plane. It composes public DPL-03C authorization,
DPL-04D readiness and typed executor contracts without importing an adapter,
API, worker, persistence, network or command implementation. Permits are
deterministic, one-use, non-production and exact-scope bound. They do not start
the pilot. Ubuntu owns no authorization or audit. Persistent SQLite audit is
not implemented and Production activation is `NOT_AUTHORIZED`.

## DPL Durable Audit Boundary

AIControlCenter owns authoritative durable deployment audit on the Mac Control
Plane. The audit domain is canonical JSON with stable IDs, deterministic
digests and tamper-evident hash-chain linkage behind a replaceable
`DurableAuditPort`. The selected future adapter is an append-only SQLite ledger
stored outside Git; SQLite is not the domain model and is not implemented in
DPL-04C. Ubuntu cannot own audit policy or state. Query integration is
read-only-first; retention, deletion, compaction and production activation are
not authorized.

## DPL Mac Sandbox Boundary

`core.deployment.sandbox_adapter` is a Mac Control Plane adapter implementing
the typed non-production executor port. It depends inward on DPL contracts and
ports only. Planning, authorization, GET-only API composition and workers
cannot import it. The adapter requires an injected non-repository sandbox root,
confines canonical JSON artifacts beneath it, and has no command, network,
runtime-service, Ubuntu or production capability. Missing-root composition is
deny-only, and evidence is not durably persisted.

## Platform Goal

AI Home Datacenter is a production-ready,
multi-year AI platform rather than a conventional
home server.

## Mac mini M4 — Control Plane

The Mac mini is the always-on Brain and the single
AIControlCenter Control Plane.

It owns:

- AI orchestration and agents
- business logic and workflow orchestration
- Dashboard and Homepage
- WordPress and WooCommerce headless integration
- n8n automation
- scheduling and notifications
- GitHub, Notion, and Ubuntu control
- AI product and customer workflows

## Ubuntu Server — Infrastructure Worker

Ubuntu is an on-demand, stateless infrastructure
worker.

It provides:

- Docker and container runtime
- storage and file operations
- Immich, Nextcloud, and Plex
- backups
- infrastructure JSON APIs

Ubuntu must not own AI workloads, business logic,
Control Plane orchestration, or application state.

## Architecture Principles

- Git First
- JSON First
- REST and headless architecture
- Docker Compose and Infrastructure as Code
- read-only monitoring before write operations
- stateless infrastructure workers
- modular services
- automated testing and documentation
- rollback before cutover

## Current Runtime Architecture

The Mac Shadow API is supervised by a system
LaunchDaemon.

- Service: system/com.aicontrolcenter.api.shadow
- Application user: kyouhan
- Listener: 127.0.0.1:18100
- Mode: shadow-read-only
- Runtime: commit-specific Python virtual environment
- GUI login required: false
- Mutating HTTP methods: blocked

## Production Gate

Ubuntu AIControlCenter remains active until:

- Headless Reboot Recovery passes
- 24-hour Shadow observation passes
- Ubuntu Worker JSON integration passes
- Cutover and rollback validation pass

<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## ADR: Mac Control Plane Production Baseline

**Status:** Accepted and operationally verified.

The Mac mini M4 is the sole AIControlCenter
Control Plane.

Ubuntu remains a stateless infrastructure worker.

Runtime flow:

`system launchd`
→ `root-owned runner`
→ `non-root application user`
→ `commit-specific Python runtime`
→ `AIControlCenter Shadow API`
→ `127.0.0.1:18100`

Validated contracts:

- Repository commit: `1e102c001c28108bee9583294abee77ce7d43643`
- Runtime commit: `1e102c001c28`
- Health: HTTP `200`
- Write protection: HTTP `405`
- Listener: `127.0.0.1:18100`
- GUI login dependency: none
- Transactional install: enabled
- Transactional rollback: enabled
- launchd settle after bootout: 2 seconds
- Final restart PID: `19761 → 19842`

Ownership boundaries:

- Mac owns AI, orchestration, business logic,
  scheduling, workflow and application state.
- Ubuntu owns Docker, storage, backup and file
  operations only.
- Ubuntu must not own AI workloads, business
  logic, Control Plane orchestration or
  application state.
- Infrastructure is consumed through JSON APIs.
- Production writes remain disabled until a
  separate cutover Gate is approved.
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->

## Dashboard Shadow Control Plane

The Mac mini is the AI Home Datacenter Control Plane.

AIControlCenter owns Control Plane status, policy, orchestration, authorization and runtime observability.

### Request Architecture

```text
Mac mini
  -> AIControlCenter Shadow API
  -> GET /dashboard
  -> DashboardAPI
  -> ControlPlaneStatus
  -> RuntimeMetadata
  -> immutable metadata.json
```

The Dashboard consumes normalized JSON. It does not parse human-readable shell output.

### Runtime Metadata Architecture

Each commit-specific Runtime contains an immutable metadata file:

```text
~/Library/Application Support/AIControlCenter/runtime/
  current
  venvs/
    <12-character-commit>/
      bin/python
      metadata.json
```

Runtime metadata schema version 1 contains:

- Full 40-character Git commit
- 12-character short commit
- Runtime mode
- UTC creation timestamp

The metadata provider validates:

- Supported schema version
- Full commit format
- Short commit consistency
- Supported Runtime mode
- Required timestamp

Invalid, missing or unreadable metadata is returned as normalized JSON with `available: false`.

Invalid metadata does not crash the Dashboard API.

### Runtime Activation Gate

The canonical Runtime bootstrap performs:

```text
Runtime Contract validation
  -> repository commit validation
  -> clean Git validation
  -> commit-specific virtual environment
  -> dependency installation
  -> application import validation
  -> test suite
  -> metadata generation
  -> metadata schema validation
  -> runtime/current activation
```

Metadata generation and validation occur before the `runtime/current` symlink is changed.

A metadata failure prevents Runtime activation.

### Safety Policy

The Shadow API is read-only.

Allowed methods:

- GET
- HEAD
- OPTIONS

Write requests are rejected with HTTP `405`.

Dashboard requests must not execute:

- Git commands
- `launchctl`
- Runtime symlink mutation
- Infrastructure write operations

Ubuntu remains a stateless infrastructure worker.

Ubuntu is not involved in Control Plane business logic or AI workloads.

<!-- AICONTROLCENTER:PI-002:START -->
## PI-002 Ubuntu Worker Health JSON Adapter

AIControlCenter monitors the Ubuntu infrastructure worker through a read-only JSON adapter.

Production execution path:

```text
system LaunchDaemon
→ canonical Mac runner
→ root-owned worker environment
→ production worker configuration
→ SSH transport adapter
→ Ubuntu worker health JSON script
→ MonitoringSnapshot
→ Dashboard JSON
```

Production contracts:

- Mac mini remains the Control Plane.
- Ubuntu remains a stateless infrastructure worker.
- Ubuntu does not own platform business logic or application state.
- Worker integrations are read-only.
- Worker transport is bounded by connection and command timeouts.
- Worker failures return structured optional-error JSON.
- Worker failure does not make the Control Plane API unavailable.
- `GET /dashboard` monitors `ubuntu-main` by default.

Runtime configuration:

- Supervisor: `system/com.aicontrolcenter.api.shadow`
- Runtime user and group: `kyouhan:staff`
- Worker environment: `/Library/Application Support/AIControlCenter/worker.env`
- Worker environment ownership and mode: `root:staff 640`
- Production worker config: `config/workers.mac-production.yaml`
- Local listener: `127.0.0.1:18100`

The worker environment contains configuration only. SSH private keys and passwords are not stored in it.
<!-- AICONTROLCENTER:PI-002:END -->

<!-- AICONTROLCENTER:PI-003:START -->
## PI-003 Ubuntu Worker Minimum Closure

The Mac mini Control Plane must remain fully operational when the Ubuntu worker is powered off or unavailable.

Architecture contract:

- Mac mini is the mandatory always-on Control Plane.
- Ubuntu is an optional on-demand infrastructure worker.
- Ubuntu does not own AI workloads, platform business logic or Control Plane state.
- Ubuntu unavailability must not interrupt AIControlCenter health or Dashboard availability.
- Worker failures are represented as structured optional JSON errors.
- Immich and Nextcloud are Ubuntu-local infrastructure services.
- Ubuntu-local containers recover through `docker.service` and `restart: unless-stopped`.

Validated standalone behavior:

- AIControlCenter remained `ONLINE` with Ubuntu powered off.
- `GET /health` returned HTTP `200`.
- `GET /dashboard` returned HTTP `200`.
- `ubuntu-main` returned `OPTIONAL_UNAVAILABLE`.
- The Control Plane continued operating without Ubuntu.
<!-- AICONTROLCENTER:PI-003:END -->

<!-- AICONTROLCENTER:PI-004:START -->
## PI-004 Mac Standalone Production Baseline

- Mac mini is the mandatory standalone Control Plane.
- Ubuntu is an optional infrastructure worker.
- AIControlCenter runs through a system LaunchDaemon.
- Production uses an immutable commit-specific Python runtime.
- Homepage is an embedded read-only API at `/homepage/status`.
- Homepage reuses the Dashboard optional-worker contract.
- Storage and backup are optional external-worker capabilities.
- Mac reboot recovery was validated without Ubuntu.
<!-- AICONTROLCENTER:PI-004:END -->

<!-- AICONTROLCENTER:PI-005:START -->
## PI-005 — Mac Service Deployment Platform

AIControlCenter owns Mac service deployment governance, validation, inspection, approval policy, and audit evidence.

The deployment pipeline is JSON-first and separates read-only operations from write operations:

`Manifest → Validate → Plan → Inspect → Diff → Dry-run → Approval → Future Executor`

Ollama is defined as a replaceable native macOS model runtime. It has no platform-wide business logic and has no Ubuntu dependency.

The canonical Ollama network contract is loopback-only at `127.0.0.1:11434`, with model inventory health at `/api/tags`.

PI-005 does not install Ollama, create a LaunchDaemon, download models, or enable deployment execution.
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

AIControlCenter is the sole control plane and source of truth for model
approval, lifecycle policy, compliance evaluation, audit, and API exposure.

The model-governance flow is:

1. `config/model-governance.json` defines the approved registry.
2. `core/governance/model_registry.py` validates the registry using a
   default-deny, read-only contract.
3. Ollama provides observed local inventory only.
4. `core/governance/model_evaluator.py` compares approved and observed models.
5. `GET /api/governance/models` exposes the evaluation as JSON.

Supported compliance states include `COMPLIANT`, `UNAPPROVED`, `MISSING`,
`DIGEST_MISMATCH`, and `RESOURCE_POLICY_VIOLATION`.

Model pull, create, copy, and delete operations remain denied. Ollama does not
own platform governance or business logic. Ubuntu remains a stateless
infrastructure worker and must not run AI workloads, store AI models, or own
model-governance state.
<!-- AICONTROLCENTER:PI-007:END -->

## PI-008: Model Governance Audit and Dashboard Integration

PI-008 establishes a read-only model-governance audit subsystem owned by AIControlCenter.

### Ownership

AIControlCenter owns:

- canonical governance audit snapshot schema
- audit orchestration
- immutable snapshot identity
- SQLite audit persistence
- historical comparison
- read-only audit APIs
- Dashboard audit read model
- deployment provenance and runtime identity

Ollama provides observed model inventory only.

Ubuntu remains a stateless infrastructure worker and owns no AI workload, model state, audit application state, or platform business logic.

### Persistence

Audit state is stored on the Mac mini at:

`~/Library/Application Support/AIControlCenter/data/model-governance-audit.sqlite3`

The database is outside the runtime directory and uses:

- SQLite WAL mode
- schema versioning
- append-only snapshot storage
- update-denied triggers
- delete-denied triggers
- no automatic deletion
- no automatic compaction
- online backup only

### Read-only API

PI-008 exposes GET-only endpoints:

- `/api/governance/audit/latest`
- `/api/governance/audit/snapshots`
- `/api/governance/audit/snapshots/{snapshot_id}`
- `/api/governance/audit/comparison`

No model pull, create, copy, delete, remediation, or other write operations are permitted.

### Dashboard

`/dashboard` includes the `model_governance_audit` read model.

The Dashboard integration is fail-soft and exposes governance status without owning audit persistence or remediation logic.

### Runtime provenance

Production runtime identity is derived from immutable release metadata:

`.aicontrolcenter-source-commit`

The Production runner no longer depends on mutable Git HEAD or Git working-tree cleanliness.

Active Production release:

- source commit: `b9ad351a7241e521c8964218f59724fcb04db93c`
- runtime release: `b9ad351a7241`
- rollback release: `0352e396f329`

<!-- PI-009:START -->
## PI-009 — Governance Audit Operations Visibility

Status: **Implementation Complete / Production Activation Pending**

AIControlCenter owns governance audit operations policy, scheduling,
projection, API presentation, Dashboard composition and operational
authorization.

The implementation provides:

- an append-only governance operations domain and SQLite adapter;
- an application-layer operational projection;
- a strict GET-only read API;
- a panel-local fail-soft Dashboard projection;
- lowercase presentation vocabulary at the API boundary;
- no automatic migration, retry, restore or remediation;
- no Ubuntu business logic or application-state ownership.

The production database remained unchanged during implementation and
validation. Production migration and scheduler activation require the
separate PI-009 Production Activation Gate.
<!-- PI-009:END -->

<!-- PI-009-OPERATIONS-FINAL:BEGIN -->
## PI-009 Final Architecture Decision

Governance operation execution is separated from
scheduling policy.

    JSON CLI
      -> OperationsApplicationService
           -> SQLiteOperationsEventRepository
           -> SystemUTCClock
           -> AutomationExecutor
           -> BackupVerifyService

AIControlCenter owns composition, policy validation,
locking, JSON output and audit dispatch.

The runner does not own cadence, retry, catch-up,
remediation or restore policy. No governance business
logic is placed on Ubuntu.

External schedulers may invoke the one-shot interface
only after a separate controlled activation gate.
<!-- PI-009-OPERATIONS-FINAL:END -->

<!-- PI-010-HEADLESS-PRODUCTION-CLOSE-2026-07-23 -->
## PI-010 Headless Scheduler Architecture

AIControlCenter owns governance cadence, policy, execution, JSON output, audit correlation, authorization, and deployment control.

The managed user crontab is a replaceable Mac mini operating-system adapter. Governance run identity and scheduled time remain inside the application and audit boundary.

Dedicated parameterless capabilities implement governance audit snapshot generation and SQLite online backup verification. No governance scheduling, AI workload, application state, or business logic runs on Ubuntu.

<!-- BEGIN AICONTROLCENTER SPF-002 ARCHITECTURE -->
## Shopping Platform Foundation

Status: SPF-002 CLOSED

- Control Plane: AIControlCenter
- Package root: `core/shopping`
- WordPress role: Headless CMS only
- WooCommerce role: Replaceable commerce engine only
- Ubuntu role: Stateless infrastructure worker
- Sprint 1 mode: Read-only
- Shopping write operations: Disabled

WordPress and WooCommerce integrate through REST/JSON adapters.
Direct external database access is prohibited.
Governance, authorization, audit, workflow, and policy remain in AIControlCenter.

Canonical detail: `docs/architecture/shopping-platform-foundation.md`
<!-- END AICONTROLCENTER SPF-002 ARCHITECTURE -->

<!-- SPF-003:START -->
## SPF-003 — Shopping Read-Only Port Foundation

Status: **Closed** on 2026-07-23.

- `core.shopping` is the application-owned Shopping bounded context.
- Seven transport-neutral ports expose read-only or compute-only capabilities.
- `CommerceCatalogPort` remains compatible through the byte-preserving `ports.py` to `ports/__init__.py` migration.
- Provisional JSON-first contracts remain isolated in `core.shopping.contracts.provisional`.
- Commerce, CMS, webhook, snapshot-persistence, and audit-append writes remain disabled.
- Canonical contract freezing is assigned to **SPF-004 — Canonical JSON Schema v1**.

Implementation commit: `fd52aad1d9af9d056d80d8f7d6170605ea0d11b2`.
<!-- SPF-003:END -->


<!-- AICONTROLCENTER-SPF-004-CLOSED -->
## SPF-004 Canonical JSON Schema v1

Status: CLOSED

Shopping contracts now use a versioned, vendor-neutral canonical JSON contract layer owned by AIControlCenter.

- JSON Schema dialect: Draft 2020-12
- Contract schema version: `1.0.0`
- Canonical contract bindings: 15
- Schema resources: 17
- Registry asset: `core/shopping/contracts/schemas/v1/registry.json`
- Explicit loader: `core.shopping.contracts.schema_registry.load_schema_registry`
- Runtime validation: `Draft202012Validator`
- Unknown contracts fail closed.
- Unknown payload fields are rejected by canonical strict objects.
- Remote and network schema resolution are prohibited.
- Schema assets are not loaded automatically during module import.
- Vendor DTOs remain adapter-private.
- Shopping write operations remain disabled.

Canonical contract validation belongs to the Mac mini AIControlCenter Control Plane. Ubuntu remains a stateless infrastructure worker and does not own Shopping contracts, state, business logic, or validation policy.

Implementation commit: `7a436a62fbaa2c176e877297d88b810b255f2776`

<!-- SPF-005-CLOSE:BEGIN -->
## SPF-005 Capability Governance — CLOSED

AIControlCenter owns Shopping capability governance and read authorization orchestration.

- Capability registry is static, immutable, vendor-neutral, and controlled by AIControlCenter.
- Eleven Shopping READ capabilities are registered.
- Nine WRITE capability identifiers are reserved but are not executable.
- Unknown capabilities fail closed.
- WRITE capabilities fail closed before policy evaluation.
- Known READ capabilities require `PolicyDecisionPort.evaluate_read`.
- Request and decision capability mismatches fail closed.
- Policy evaluation exceptions are normalized to `shopping.policy.evaluation_error`.
- Raw vendor or adapter exception messages are not exposed through authorization denial.
- No adapter execution, production registration, Ubuntu business logic, or Shopping write operation was enabled by SPF-005.

Authorization flow:

`Capability Registry -> READ classification -> PolicyDecisionPort -> explicit allow -> authorized read`

Implementation commit: `f807cc0dfb8a27d2bf387bdc3dd897e4fe331953`

Validation baseline: 22 targeted tests passed; 775 full regression tests passed.

Next architecture task: SPF-006 Read Adapter Contracts.
<!-- SPF-005-CLOSE:END -->

<!-- SPF-006-CLOSE:BEGIN -->
## SPF-006 Read Adapter Contracts — CLOSED

AIControlCenter owns the authoritative Shopping read ports and adapter contract boundaries.

- `CommerceReadPort` remains the authoritative callable Commerce interface.
- `CmsReadPort` remains the authoritative callable CMS interface.
- Adapter contract modules validate exact async method conformance against those ports.
- Commerce canonical returns are `ProductSnapshot`, `ProductSnapshotPage`, and `OrderSummary`.
- CMS canonical returns are `ContentSnapshot` and `ContentSnapshotPage`.
- SPF-005 capability bindings remain authoritative and are consumed rather than duplicated.
- Commerce and CMS capability sets are isolated.
- Vendor DTO escape, adapter-owned business logic, adapter-owned policy evaluation, and WRITE methods are prohibited.
- No live WooCommerce or WordPress network connection is enabled by SPF-006.
- Live vendor integration and adapter health monitoring remain deferred to SPF-007.

Implementation commit: `fd1bbe2ff212e9eeb442562ffeed32bed97c1072`.

Validation baseline: 28 targeted tests passed; 803 full regression tests passed.

Next architecture task: SPF-007 Adapter Health Monitoring.
<!-- SPF-006-CLOSE:END -->

<!-- SPF-007-CLOSE:BEGIN -->
## SPF-007 Adapter Health Monitoring — CLOSED

AIControlCenter owns Shopping adapter health semantics, monitoring aggregation, routing signals, and operational governance.

- `AdapterHealthPort` remains the authoritative health read port.
- Health states are `HEALTHY`, `DEGRADED`, and `UNAVAILABLE`.
- Failure taxonomy is vendor-neutral and fail-closed.
- Timeout, transport, authentication, authorization, invalid payload, schema mismatch, dependency, configuration, and unknown failures resolve to unavailable health.
- Latency and rate-limit conditions resolve to degraded health.
- Health is not authorization and does not bypass SPF-005 capability or policy governance.
- Probe normalization rejects raw vendor error text and credential-bearing metadata.
- Health aggregation is deterministic and stateless.
- Overall precedence is `UNAVAILABLE > DEGRADED > HEALTHY`.
- Empty aggregation input resolves to `UNAVAILABLE`.
- Probe-layer retry, persistence, scheduler ownership, business writes, and adapter-owned policy decisions are prohibited.
- Live WooCommerce and WordPress transport remains disabled by SPF-007.
- Ubuntu remains a stateless infrastructure worker.

Implementation commit: `63263b734ead4eb083f9b91923f4b41c3b644e34`.

Validation baseline: 34 targeted tests passed; 837 full regression tests passed.

Next architecture task: SPF-008 Read-only Snapshots.
<!-- SPF-007-CLOSE:END -->

<!-- SPF-008-CLOSE:BEGIN -->
## SPF-008 Read-only Snapshots — CLOSED

AIControlCenter owns Shopping snapshot governance and read orchestration.

- `SnapshotRepositoryPort` remains the authoritative snapshot read boundary.
- Supported repository operations remain `get_latest_snapshot` and `list_snapshots`.
- Snapshot creation, persistence, update, replacement, deletion, and retention cleanup are classified as application-state writes and remain outside SPF-008.
- Snapshot normalization accepts canonical JSON-compatible data only.
- Normalization is deterministic and returns an immutable read model.
- Snapshot query authorization occurs before repository access.
- Authorization denial or authorization failure prevents repository execution.
- Repository and policy failures are sanitized before exposure.
- Snapshot queries do not refresh vendor data.
- Schema validation and schema drift governance remain owned by SPF-009.
- No new database or filesystem persistence is introduced.
- Production live vendor registration remains disabled.
- Ubuntu remains a stateless infrastructure worker.

Implementation commit: `d8859a3706a087f88be513e32097b22c9a8ec3d6`.

Validation baseline: 35 targeted tests passed and 872 full regression tests passed.

Next architecture task: SPF-009 Validation and Schema Drift.
<!-- SPF-008-CLOSE:END -->

<!-- AICONTROLCENTER:SPF-009:CLOSED -->
## SPF-009 Validation and Schema Drift Closure

- Status: CLOSED on 2026-07-23.
- AIControlCenter remains the single control plane and owns schema governance, authorization, validation, drift policy, monitoring, and audit boundaries.
- Canonical contract source remains `core/shopping/contracts/schemas/v1` using JSON Schema Draft 2020-12.
- Runtime validation statuses are `VALID`, `INVALID`, and `ERROR`; only `VALID` is accepted and all operational uncertainty fails closed.
- Schema resolution is local-only. Remote HTTP schema resolution and automatic fetch are forbidden.
- Drift statuses are `NO_DRIFT`, `COMPATIBLE_DRIFT`, `BREAKING_DRIFT`, and `UNKNOWN_DRIFT` from the canonical-consumer-safety perspective.
- `UNKNOWN_DRIFT` is fail-closed and no drift result automatically changes the canonical contract.
- Schema discovery remains read-only and authorization occurs before `SchemaDiscoveryPort.discover_schema(*, context, adapter_name)`.
- Schema ID and adapter name are separate concerns; no vendor DTO owns the canonical contract.
- Automatic schema adoption, migration, application-state persistence, vendor writes, production registration, and Ubuntu application state remain disabled.

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
- Architecture state: Foundation boundaries are frozen for production-readiness closure.
- External commerce and CMS components remain replaceable behind adapters and APIs.

<!-- BEGIN AICONTROLCENTER:SRI-03 -->
## SRI-03 External Read Production Architecture

AIControlCenter on the Mac mini M4 remains the single Control Plane.
Ubuntu remains a stateless infrastructure worker and owns no Shopping business logic, application state, AI workload, or ingress policy.

### Headless Shopping boundary

- WordPress is the CMS.
- WooCommerce is a replaceable Commerce Engine.
- AIControlCenter owns policy, orchestration, normalization, validation, audit, authorization, workflow, and Shopping business logic.
- External components integrate through adapters and JSON or REST contracts.

### Caddy production ingress

- Caddy runs on the Mac Control Plane.
- WAN TCP 80 forwards to Mac TCP 58080.
- WAN TCP 443 forwards to Mac TCP 58443.
- Caddy owns transport ingress only and contains no Shopping business logic.

### Production TLS identity

`bokstory.iptime.org` is an operational DDNS locator only.
It is not the production canonical TLS identity.

Authoritative DNS evidence classified the hostname as `PARENT_CAA_PROHIBITS_PUBLIC_CA_ISSUANCE`.
Production HTTPS therefore requires a platform-controlled DNS namespace.
AAAA remains absent until IPv6 ingress is separately validated.

### Evidence

- SRI-03D3A3-D8 confirmed external LTE or 5G HTTP ingress and HTTP 200.
- SRI-03D3A3-D9 discovered the inherited CAA restriction.
- SRI-03D3A3-D10 confirmed the parent CAA restriction on authoritative ipTIME nameservers.
<!-- END AICONTROLCENTER:SRI-03 -->

<!-- SRI-06B-R1:ARCHITECTURE -->
## SRI External READ and Observability Architecture

### Ownership

- core/cms owns generic CMS models, ports and WordPress normalization.
- core/cms must not import core/shopping.
- core/shopping owns commerce schema, snapshot and drift semantics.
- core/monitoring owns generic operational observation orchestration.
- ExternalReadObserver receives domain dependencies through injection and owns no network client.

### Public edge

- Host Caddy is the sole public edge.
- /healthz is an explicit infrastructure health route.
- Remaining application traffic falls back to WordPress at 127.0.0.1:58081.

### Operational evidence

- Stage order is Health, Schema, Snapshot and Drift.
- Persisted JSON is authoritative and console summaries are human-only.
- Generic observations use sanitized generic JSON snapshots.
- Shopping snapshot normalization is reserved for Shopping domain snapshots.
- Contract drift is a failure condition and business-data drift is observed separately.

### Recovery

Recovery requires immutable snapshot, scratch restore, structural validation, semantic validation, explicit authorization, production restore and production validation.
<!-- END SRI-06B-R1 -->

<!-- AICONTROLCENTER:DPL-01:START -->
## DPL Deployment Package Bounded Context

DPL is an AIControlCenter-owned bounded context for immutable desired-state
packages and observed-state reports. It preserves the Mac mini M4 as the
always-on Brain and single Control Plane.

### Ownership and dependencies

- AIControlCenter owns DPL governance, policy, orchestration, approval,
  authorization, audit and deployment control.
- DPL read observes inventory and state.
- DPL plan validates policy, computes diff and emits a dry-run plan.
- Apply is a separate future boundary; read and plan must not import or invoke
  mutating executors.
- DPL v1 uses versioned JSON Schemas and a registry.
- A DPL package is immutable and Git-identifiable; it never grants activation
  authority.

### Platform boundary

- Mac production services use launchd.
- Host Caddy is the only public edge.
- WordPress is the CMS Engine and WooCommerce is the Commerce Engine.
- AIControlCenter owns all business logic.
- Ubuntu remains optional, stateless and on demand.
- DPL-02 activates no Ubuntu adapter and excludes
  `UbuntuWorkerClient.execute`.
- Linux systemd Control Plane artifacts are `LEGACY_UNSUPPORTED`,
  production-prohibited and excluded from DPL.

DPL-02 is limited to inventory, manifest and policy validation, diff, dry-run
planning, readiness reporting and audit. Apply, install, restart, bootstrap,
rollback execution, production writes and generic Ubuntu command execution are
prohibited. Production activation is not authorized.

Canonical details: `docs/architecture/dpl-deployment-package.md`.
<!-- AICONTROLCENTER:DPL-01:END -->

## DPL M2 Readiness Boundary

`core.deployment.m2_readiness` is a pure evidence-consumer owned by
AIControlCenter on the Mac Control Plane. It imports no API, worker, runtime
adapter, command, network or persistence implementation. Its accepted result
is sandbox-only and non-production-only; it performs no activation. Ubuntu
owns no governance or audit. DPL-04 is CLOSED with
`M2 READINESS_ACCEPTED`, `M2 ACTIVATION_NOT_STARTED`, and Production activation
`NOT_AUTHORIZED`. M2-P1 policy is available but grants no execution or
activation; M2-P2 remains the next separately controlled boundary.

## M3 Permit Replay Write Boundary

M3-A2A remains the read-only inspector. M3-A2B adds a separate Mac Control
Plane-owned existing-file SQLite writer using explicit configuration,
`mode=rw`, preconfigured WAL and serialized append-only transactions. It owns
permit reservation, terminal disposition and replay integrity; Ubuntu owns
none of this state. No operational database, migration, repair, audit write or
Production activation is composed.

## M3 Permit Replay Recovery Boundary

Recovery depends only on M3-A2A public inspection/path/state contracts, M3-A2B
public writer contracts, deployment contracts and Python SQLite. Verified
temporary outputs are atomically published only after byte, canonical manifest,
ordered-ledger and derived-state equality checks. A restored file is never
automatically selected as operational.
