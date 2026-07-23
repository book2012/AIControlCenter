# AI Home Datacenter Architecture

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
