# AI Home Datacenter Architecture

## R4 strict-live compatibility boundary

The strict preflight reader alone permits the exact required governance field
`ubuntu_participation`, and only when its value is Boolean `false`. Its exact
schema still rejects every unknown host, command, destination, environment,
worker, nested Ubuntu, or production field; the global unsafe-field policy is
unchanged. The live permit service returns the frozen
`ControlledLivePermitResult`, and the orchestrator type-checks and revalidates
Git, identity, time, one-use, digest, controlled scope, and production denial
before canonical serialization. No Ubuntu or runtime dependency was added.

## Recovery-2 evidence boundary

Only `core.deployment.git_readonly_evidence` may import subprocess for the
deployment-control Git capability. It uses fixed `/usr/bin/git` read commands,
exact cwd, minimal environment, bounded timeout/output, and no shell, write,
credential, hook, or network command. The live package consumes its typed
collector/validator and does not import subprocess. Existing public SQLite
inspectors and PRE_ACTIVATION monitoring remain independent evidence
authorities; post-claim failures preserve canonical mode-0600 evidence.

## Controlled operational composition boundary

`core.deployment.operational_bootstrap_live` is the only reviewed local live
composition boundary. It invokes the existing execution coordinator directly;
earlier packages do not import it, and it exposes no API, worker, remote
command, or network surface.
The recovery composition fixes concrete readers, authorization, permit, atomic
claim, trusted `pwd` home, host/path validation, Mac runtime, evidence writer,
and execution coordinator collaborators. Callers cannot select collaborators
through JSON, CLI, or environment. The validation runner remains
validation-only.

## Operational permit issuance review boundary

M3-A4B2B1A is a pure Mac Control Plane review package binding existing M3-A4
evidence by canonical digest. It has no adapter, persistence, executor, network,
API or worker dependency and grants no authorization. Ubuntu cannot authorize,
issue, claim or execute a permit. Production remains NOT_AUTHORIZED.

## M3-A4B2B0 Read-Only Host Preflight Boundary

`core.deployment.operational_bootstrap_preflight` is a Mac Control Plane-owned,
read-only evidence and deterministic policy boundary. It validates the Darwin
host, exact Git/test/safety state, absent future targets, filesystem locality,
capacity, permission feasibility and closed-track evidence without a clock,
write adapter, database writer, executor, permit registry, subprocess, network,
API, worker or Ubuntu dependency. M3-A4B2B0 is closed; no permit,
authorization, bootstrap, target creation or Production activation occurred.
Next: M3-A4B2B1 Operational Permit Issuance.

## M3-A4B2A Controlled Bootstrap Validation Boundary

`core.deployment.operational_bootstrap` is the Mac Control Plane-owned
standard-library boundary for `TEST_ONLY_BOOTSTRAP_VALIDATION`. It is confined
to an exact injected pytest root under `/private/tmp` and has no API, worker,
Ubuntu, subprocess, network, writer composition or dispatch dependency.
M3-A4B2A is closed after single-use permit, schema, baseline recovery,
pre-activation evidence and cleanup validation. Operational execution remains
absent and Production activation is `NOT_AUTHORIZED`. Next: M3-A4B2B.

## M3-A4B1 Controlled Bootstrap Authorization Boundary

`core.deployment.operational_bootstrap_authorization` is a pure, deterministic
Mac Control Plane authorization boundary over public M3-A4A readiness
contracts. It binds exact Git, readiness, restriction, target, schema, plan,
safety, identity, approval, and validity evidence into a canonical one-use
controlled-non-production permit. Only an injected registry protocol exists;
there is no persistence or bootstrap executor. M3-A4B1 is closed after
synthetic validation. No operational permit was issued, no bootstrap was
authorized or executed, operational paths remain absent, writers remain
inactive, and Production activation is `NOT_AUTHORIZED`. Next: M3-A4B2.

## M3-A4A Operational Activation Readiness Boundary

`core.deployment.operational_activation_gate` is a collision-free, pure,
immutable and evidence-only Mac Control Plane boundary. It validates closure,
test, Git, safety, recovery, monitoring, future path/permission, bootstrap and
rollback evidence without clocks, probes, persistence, commands, network,
executors, API, worker or Ubuntu dependencies. Its readiness result is not an
authorization. M2, M3-A1, M3-A2, M3-A3 and M3-A4A are closed; operational
databases remain uncreated, writers and monitoring remain inactive, external
dispatch remains unimplemented, bootstrap authorization is not granted and
Production activation is `NOT_AUTHORIZED`. Next: M3-A4B Controlled Mac
Operational Bootstrap.

## M3-A3C Monitoring and Alert Drill Boundary

`core.deployment.monitoring_alert_drill` consumes only public M3-A3A and M3-A3B
contracts. It deterministically validates the complete monitoring-to-routing
flow and simulates logical receipts in an injected object-scoped sink. It has
no filesystem, database, network, subprocess, API, worker, Ubuntu, external
adapter, or production composition dependency. M3-A3C and the M3-A3 track are
closed. External dispatch and persistence remain unimplemented; operational
monitoring remains inactive and Production activation is `NOT_AUTHORIZED`.
Next: M3-A4 Controlled Operational Activation Gate.

## M3-A3B Alert Routing Boundary

`core.deployment.alert_routing` is a collision-free pure policy package owned
by AIControlCenter on the Mac Control Plane. It consumes only immutable M3-A3A
public contracts, explicit configuration, history, snapshot binding and
timestamps. It deterministically returns logical routes, suppression and
escalation decisions without dispatch, persistence, acknowledgement, clock,
database, command, network, API, worker or Ubuntu dependencies. M3-A1, M3-A2,
M3-A3A and M3-A3B are closed. Operational monitoring remains inactive,
operational databases remain uncreated and Production activation is
`NOT_AUTHORIZED`. M3-A3C Monitoring and Alert Operational Drill is next.

## M3-A3A Operational Monitoring Boundary

`core.deployment.operational_monitoring` is the pure, read-only monitoring
authority owned by AIControlCenter on the Mac Control Plane. It consumes
immutable public evidence, explicit timestamps and explicit thresholds and
returns deterministic PRE_ACTIVATION snapshots plus alert candidates. It has
no clock, persistence, database, adapter, command, network, notification,
API-worker or Ubuntu dependency. Alert dispatch and monitoring persistence are
not implemented. M3-A1, M3-A2 and M3-A3A are closed; operational databases and
writers remain inactive and Production activation is `NOT_AUTHORIZED`.

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
# M3-A4B2B1B approval boundary

AIControlCenter on the Mac Brain owns the human-approval intake and permit
issuance decision. Ubuntu cannot approve, issue, claim or execute permits. The
pure `operational_permit_approval` layer consumes M3-A4B2B1A review contracts
and delegates synthetic in-memory creation to M3-A4B1 only after all gates
pass. It has no persistence, executor, API, worker, network or dispatch
dependency. Live issuance and production activation remain unauthorized.
# M3-A4B2B2A execution boundary

AIControlCenter on the Mac mini M4 is the sole owner of operational permit
validation, atomic claim and bootstrap governance. The trusted local account
home determines the exact Application Support root. Ubuntu, workers, CMS,
commerce and n8n cannot participate. M3-A4B2B2A makes the controlled
non-production capability available in code without executing it or
authorizing production.
# M3-A4B2B2B-R1 shared application-state boundary

The Mac application-state parent is shared infrastructure. Deployment control
never assumes exclusive ownership and manages only `audit`, `security`, and
`monitoring`. Existing siblings are opaque and immutable to bootstrap.
Pre-existing safe `0755` parents carry a nonblocking restriction; newly created
managed directories require `0700`.
# Controlled operational activation boundary

Operational permit issuance and controlled Mac execution require a separate,
immutable, exact-commit activation authorization. Flags and environment
variables cannot grant this authority. Test and Mac operational adapters remain
strictly separated.
# R5 acknowledgement projection boundary

The Control Plane retains complete restriction acknowledgement evidence while
projecting only the semantic `warnings-427` Mac-operator/independent-approver
pair into the executor contract. Projection is typed, immutable,
order-independent, digest-bound, and validated before issuance and claim.

# Bootstrap evidence and recovery boundary

M3-A4B3 adds a Control-Plane-owned, read-only-first evidence validator and
recovery-work-confined restore adapter. It reuses public canonical helpers and
SQLite inspectors, never restores into the operational root, and has no issuer,
claim, live-runner, writer, monitoring, dispatch, network, Ubuntu, or business
logic capability. Snapshot permissions may be a read-only subset of the
created `0700`/`0600` state; broader permissions always fail closed.

# Controlled activation validation boundary

M3-A4C adds a pure immutable AIControlCenter closeout boundary. It validates
Git, evidence, recovery, health, control-plane, Mac-role, Ubuntu-exclusion, and
default-deny facts and emits deterministic JSON. It has no activation, issuer,
claim, restore, API, remote, worker, or business-logic capability. Success
requires a future independent architecture and authorization gate.

# M4 controlled activation architecture boundary

M4-A1 adds a closed typed capability registry, immutable per-capability state
machine, default-deny architecture policy, deterministic planner, and
validation facade. Capabilities cannot authorize or add dependencies
implicitly. AIControlCenter on Mac owns every governance, authorization, audit,
replay, and activation boundary; Ubuntu is ineligible. The package imports only
pure deployment contracts, exposes no runtime port, and cannot activate a
writer, monitor, dispatch, command, API write route, or production transition.

# M4 capability authorization contract boundary

M4-A2 adds immutable capability-scoped request, approval, restriction, evidence,
validation, and grant-plan contracts. Canonical JSON, SHA-256 binding, injected
UTC-aware time validation, independent identity policy, a maximum one-hour
window, and exact M3/M4-A1 bindings fail closed. Each M4-A1 capability is
requested alone; dependency references never imply authorization.

The grant contract is a test-only deterministic plan with authorization,
permit, claim, and activation fields false. No runtime port, API write route,
command, network client, writer, monitoring runtime, dispatch, Ubuntu
delegation, or production path exists. The decision
`READY_FOR_TEST_ONLY_AUTHORIZATION_SIMULATION` authorizes nothing.

# M4 test-only authorization simulation boundary

M4-A3 is pure and in-memory with injected time and seed. Its seven simulated
states are separate from the operational state machine and never enter
`CONTROLLED_ACTIVE`. Artifacts use namespace `m4-a3-test-only` and immutable
test-only, operational-invalid, non-production, Ubuntu-excluded, and
runtime-denied markers. Each capability owns an independent digest chain and
one process-local claim; dependencies are references only. Strict shape checks
and unconditional live-boundary rejection prevent marker deletion or field
renaming from producing an operational artifact. No operational store, writer,
runtime port, command, network, API write, Ubuntu, or activation dependency
exists.
# AUTO-01 control-plane boundary

AIControlCenter exclusively owns autonomous-delivery governance, policy,
roadmap compilation, scheduling, dependency planning, approvals, authorization,
retry and recovery decisions, evidence gates, completion and deployment
control. Codex is a bounded replaceable executor port, never an authority.

AUTO-01 adds pure typed contracts, fail-closed manifest validation, canonical
SHA-256 JSON, deterministic DAG compilation and a strict delivery lifecycle. It
adds no persistent runner, subprocess, network adapter, launchd service or
operational side effect. L4/L5 and post-claim recovery require human approval;
production remains `NOT_AUTHORIZED`. AUTO-02 owns the future persistent runner
and terminal-independence design.

<!-- SHOPPING-FIRST-REPRIORITIZATION:BEGIN -->
## Shopping-First Service Architecture

AIControlCenter remains the single control plane and owns business
logic, governance, orchestration, authorization, adapters and audit
references.

Replaceable open-source components retain their specialized roles:

- WordPress: CMS
- WooCommerce: Commerce Engine
- n8n: Automation Engine
- Ollama: Local Model Runtime
- OpenClaw: Assistant Interface
- GitHub: Source, CI and release evidence

General-purpose capabilities use replaceable open-source components.
Custom implementation requires a documented capability gap.

Service progression is Shopping Platform, then AI Integration Platform,
then Personal AI Assistant. Ubuntu remains a stateless infrastructure
worker and owns no orchestration or application state.
<!-- SHOPPING-FIRST-REPRIORITIZATION:END -->

<!-- SHOP-00-CLOSEOUT:BEGIN -->
## SHOP-00 Shopping Platform Reprioritization

SHOP-00 is closed.

Repository inventory and regression validation confirmed that the
existing Shopping Platform Foundation and Shopping External Read
Integration are already part of the current branch history.

Existing capabilities designated for reuse:

- WooCommerce external read adapter
- WooCommerce transport and normalization
- WordPress CMS adapter
- normalized product snapshot JSON contracts
- read authorization and deny-by-default policy
- schema validation and drift monitoring
- adapter health monitoring
- nine read-only Shopping API routes
- Orange Coco storefront

The former SHOP-01 WooCommerce Read Adapter scope is therefore
`CLOSED_BY_EXISTING_SRI`.

The first incomplete product capability is:

`SHOP-01_PRODUCT_MANAGEMENT_READ_MODEL_AND_DASHBOARD`

Architecture invariants:

- Storefront and management Dashboard are separate surfaces.
- Dashboard consumes AIControlCenter APIs only.
- Dashboard does not call WooCommerce directly.
- WooCommerce remains the Commerce Engine.
- WordPress remains the CMS.
- AIControlCenter owns business workflow and normalized management
  views.
- SHOP-01 is read-only.
- Product draft, approval and controlled write remain separate tasks.
- No Shopping business logic is placed on Ubuntu.
- Production writes remain `NOT_AUTHORIZED`.
<!-- SHOP-00-CLOSEOUT:END -->

<!-- SHOP-01B-MANAGEMENT-READ-MODEL:BEGIN -->
## SHOP-01B Shopping Management Read Model

SHOP-01B adds a pure read-only application projection for
operator-facing product management data.

The projection consumes the existing `ShoppingService` boundary and
produces deterministic JSON-safe output containing:

- service health
- readiness
- read/write capability state
- adapter integration state
- catalog totals
- in-stock and out-of-stock counts
- inventory quantity totals
- normalized product list fields

The module performs no network calls, persistence, product mutation,
WooCommerce imports or Dashboard registration.

The Product Management Dashboard remains a projection of WooCommerce
truth through AIControlCenter. It is not a second product database.

The next task is `SHOP-01C_DASHBOARD_JSON_INTEGRATION`.
<!-- SHOP-01B-MANAGEMENT-READ-MODEL:END -->
