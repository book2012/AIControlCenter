# Project History

## 2026-07-30 — M3-A4B2B0 Closed

AIControlCenter added deterministic read-only Mac operational bootstrap host
preflight and exact future-target inventory validation. No operational permit
was issued or claimed, authorization was not granted, bootstrap was not
executed, operational state was not created, and Production remained
`NOT_AUTHORIZED`. M3-A4B2B1 Operational Permit Issuance is next.

## 2026-07-30 — M3-A4B2A Closed

AIControlCenter validated the controlled Mac bootstrap executor only beneath
injected pytest-owned `/private/tmp` roots. Synthetic one-use permit,
audit/replay schema, baseline recovery, monitoring evidence and failure
cleanup were validated. No operational permit was issued, operational
bootstrap was not executed, operational state was not created, writers and
monitoring remained inactive, and Production activation remained
`NOT_AUTHORIZED`. M3-A4B2B is next.

## 2026-07-30 — M3-A4B1 Closed

AIControlCenter added the deterministic controlled non-production bootstrap
authorization contracts, exact M3-A4A restriction acknowledgements, canonical
one-use permits, validation, and an injected registry port. Synthetic permits
and claims were validated in memory only. No operational permit was issued,
bootstrap was not authorized or executed, operational paths remain absent,
writers remain inactive, and Production activation remains `NOT_AUTHORIZED`.
M3-A4B2 Controlled Mac Operational Bootstrap is next.

## 2026-07-30 — M3-A4A Closed

AIControlCenter closed M3-A4A with a deterministic, evidence-only
`PRE_ACTIVATION_READINESS` gate and validated future path, permission,
bootstrap and rollback plans. M2, M3-A1, M3-A2 and M3-A3 remain closed.
Operational databases were not created; writers and monitoring were not
activated; external dispatch was not implemented; bootstrap authorization was
not granted; Production activation remains `NOT_AUTHORIZED`. M3-A4B Controlled
Mac Operational Bootstrap is next.

## 2026-07-30 — M3-A3C and M3-A3 Track Closed

AIControlCenter validated the deterministic monitoring-to-logical-routing drill
using only immutable evidence and an object-scoped in-memory simulator. All
M3-A3 stages and the Monitoring and Alert Track are closed. External dispatch
and persistence remain unimplemented; operational monitoring and databases
remain inactive; Production activation remains `NOT_AUTHORIZED`. M3-A4
Controlled Operational Activation Gate is next.

## 2026-07-30 — M3-A3B Closed

AIControlCenter closed M3-A3B with pure deterministic logical routing,
deduplication, reminders, recurrence and severity escalation over immutable
M3-A3A candidates and explicit history. M3-A1, M3-A2 and M3-A3A remain closed.
External dispatch and alert-routing persistence are not implemented;
operational monitoring and databases remain inactive. Production activation
remains `NOT_AUTHORIZED`. M3-A3C Monitoring and Alert Operational Drill is
next.

## 2026-07-30 — M3-A3A Closed

AIControlCenter closed M3-A3A with a pure deterministic PRE_ACTIVATION
monitoring boundary and immutable alert candidates. M3-A1 and M3-A2 remain
closed. Read-only monitoring snapshots and candidate evaluation are available;
external dispatch and monitoring persistence are not implemented. Operational
databases were not created, operational writers were not activated, and
Production activation remains `NOT_AUTHORIZED`. M3-A3B Alert Routing and
Deduplication is next.

## 2026-07-30 — M3-A2C Closed

M3-A2C added explicit-path online replay-state backup, canonical manifests,
verified restore, exact recovery and post-recovery concurrency validation.
Only pytest temporary databases were used. M3-A1 and M3-A2A through M3-A2C are
closed; the operational replay DB was not created, no schedule, restore or
writer was activated, raw nonce writes remained zero and Production activation
remained `NOT_AUTHORIZED`. M3-A3 Operational Monitoring and Alerts is next.

## 2026-07-29 — M3-A2A Permit and Replay Read-Only Foundation

AIControlCenter closed M3-A2A with a separate Mac-owned, explicit-path,
read-only SQLite integrity boundary for future durable permit and replay state.
It deterministically validates event lifecycles, binding, hash-chain, privacy
and Production restrictions and derives redacted permit states. Validation
used only pytest temporary databases. The operational permit/replay database
was not created; durable reservation, consumption and persistent nonce writes
remain disabled; Production activation is `NOT_AUTHORIZED`. M3-A2B is next.

## 2026-07-29 — M3-A1C SQLite Backup, Restore and Recovery

AIControlCenter closed M3-A1C with explicit-path SQLite online backup,
canonical manifest binding, separate-target restore and deterministic complete
ledger comparison. Validation used only pytest temporary databases. No
operational audit database, backup schedule or restore was created or
performed; persistent writer activation is not started and Production
activation remains `NOT_AUTHORIZED`. M3-A2 Durable Permit and Replay State is
next.

## 2026-07-29 — M3-A1B Append-Only SQLite Audit Writer

AIControlCenter closed M3-A1B with a separate Mac-owned SQLite append adapter.
It requires an explicit pre-existing database, validates WAL, schema controls
and the complete hash chain, and performs one atomic read-back-verified append
or a zero-write idempotent retry. Validation used only pytest temporary
databases. The operational database was not created, operational activation is
not started, persistent Production writes are not enabled, and Production
activation remains `NOT_AUTHORIZED`. M3-A1C is next.

## 2026-07-29 — M3-A1A SQLite Read-Only Integrity

AIControlCenter closed M3-A1A after adding a Mac-owned read-only SQLite
inspection boundary with deterministic integrity, chain and privacy reports.
The future application-state location is policy only: no operational database
was created, persistent audit writes remain disabled, migrations were not
executed and Production activation remains `NOT_AUTHORIZED`. M2 controlled
pilot validation is closed. M3-A1B Append-Only SQLite Audit Writer is next.

## 2026-07-29 — M2-P3 Pilot Evidence and Rollback Validation

M2-P3 closed with canonical tamper detection, fixed evidence-derived rollback
planning and one pytest-owned rollback restoring the pre-activation digest.
Persistent host activation is not started, persistent host rollback and SQLite
audit are not implemented, and Production activation is `NOT_AUTHORIZED`.

## 2026-07-29 — M2-P2 Controlled Sandbox Pilot Activation

M2-P2 closed after exactly one successful controlled pilot executed through an
injected Mac sandbox adapter inside a pytest-owned temporary directory. The new
activation boundary reserves one-use permits before invocation, denies replay
after success or failure, fixes typed operation order, and emits immutable
audit-ready receipts. No persistent host sandbox, persistent audit adapter,
Production activation, Ubuntu change, network access or runtime command was
performed. M2-P3 Pilot Evidence and Rollback Validation is next.

## 2026-07-29 — M2-P1 Pilot Authorization Closed

AIControlCenter added a pure, deterministic and default-deny policy for a
separately controlled Mac-only non-production sandbox pilot. The one-use permit
binds accepted M2 readiness, valid DPL-03C execution authorization, exact
digests, identities, scope, sandbox-root identity and explicit validity while
enforcing separation of duties. No pilot was executed or activated.

DPL-04 is CLOSED, M2 readiness is ACCEPTED, M2-P1 is CLOSED and pilot
authorization policy is AVAILABLE. Pilot activation is NOT STARTED, persistent
SQLite audit is NOT IMPLEMENTED and Production activation is
`NOT_AUTHORIZED`. Next: M2-P2 Controlled Sandbox Pilot Activation and Evidence.

## DPL-04C

On 2026-07-29, AIControlCenter accepted the durable deployment audit
architecture. The Mac Control Plane owns the authoritative ledger domain;
canonical JSON, stable digests and hash-chain linkage provide deterministic
tamper evidence through pure contracts and `DurableAuditPort`. A future
append-only SQLite adapter was selected but not implemented. DPL-04C closed,
DPL-04D became ready, M2 remained incomplete and production activation remained
`NOT_AUTHORIZED`.

## DPL-04B

AIControlCenter added a Mac-only, explicit-root sandbox adapter for
deterministic non-production manifest and evidence materialization. It
introduced no commands, network access, durable audit, Ubuntu ownership or
production authorization. DPL-04C became the next gated deployment task.

AIControlCenter became the Brain.

Ubuntu became an optional Worker.

Implemented

- BrainAgent
- Provider Manager
- Telegram
- Dashboard
- Conversation Memory
- SQLite
- Command Router

## Sprint 21-22

Scheduler Foundation completed.

Memory Manager completed.

AIControlCenter now has:

- Heartbeat
- Scheduled Job Registry
- Background Scheduler
- Conversation Memory
- Working Memory
- Long-term Memory
- Memory API

<!-- AI_SHOPPING_PLATFORM_START -->
## AI Shopping Platform Service Layer

AI Shopping Platform development started after the infrastructure
platform reached production-ready status.

Shopping is implemented as a service layer inside AIControlCenter.

The architectural ownership is:

- WordPress provides the shopping homepage and CMS
- WooCommerce provides the commerce engine
- AIControlCenter owns Shopping business logic and AI workflow
- AI Agent generates content and performs approved updates
- n8n executes external automation
- Mac mini M4 is the final production Control Plane
- Ubuntu remains an infrastructure worker

Development currently runs in a virtual environment.

The same source code will later be deployed to Mac mini M4 using
production-specific configuration.
<!-- AI_SHOPPING_PLATFORM_END -->

<!-- SHOPPING_M4_START -->

## Shopping Platform M4 History

AI Shopping Platform was introduced as a service layer on top of the completed AI Home Datacenter Platform.

During M4:

- WordPress and WooCommerce were deployed in the Ubuntu virtual validation environment.
- AIControlCenter remained the sole business-logic and orchestration layer.
- WooCommerce was connected through a read-only Adapter.
- External HTTP development access was established through ipTIME DDNS and port forwarding.
- Public TLS using the ipTIME hostname was rejected by the parent-domain CAA policy.
- Production HTTPS was deferred until a user-owned domain is available.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## Shopping Platform M5 History

M5 introduced the first external AI Shopping Storefront.

The Storefront was implemented as a modular WordPress Presentation Plugin.

WordPress displays Featured Products, categories, search results, price filters, stock filters, pagination, and product images.

AIControlCenter continues to own product selection, search validation, Commerce Adapter access, and future recommendation logic.

The implementation was validated through the external ipTIME DDNS development address while Production HTTPS remains deferred to a user-owned domain.
<!-- SHOPPING_M5_END -->

<!-- AI_SHOPPING_STOREFRONT_V016_ADR -->
## ADR — AI Shopping Storefront v0.16.0 Baseline

Date: 2026-07-13

Decision:

Orange Coco v6 is the canonical Shopping Storefront presentation layer.

The WordPress plugin remains a presentation adapter and does not own
shopping business logic. Product detail pages retrieve product data
through the AIControlCenter Shopping API.

HTTP contract:

- Existing products return HTTP 200.
- Missing products return HTTP 404.

Rationale:

This preserves the headless architecture and keeps business logic
inside the single AIControlCenter Control Plane.

<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:START -->
## 2026-07-14 — Non-root LaunchDaemon Milestone

            The Mac Control Plane Shadow Runtime completed
            its non-root LaunchDaemon and automatic restart
            production gates.

            The earlier LaunchAgent design was rejected after
            reboot testing demonstrated that a GUI bootstrap
            domain was unavailable in the headless operating
            environment.

            The replacement system LaunchDaemon:

            - starts without a GUI login
            - runs the application as `kyouhan`
            - binds only to `127.0.0.1:18100`
            - returns HTTP `200` from `/health`
            - blocks mutating requests with HTTP `405`
            - uses a commit-specific Python runtime
            - uses secure root-owned installation files
            - recovered automatically:
              `1661 → 1975`

            Ubuntu remained unchanged and continues operating
            until Mac Shadow observation and rollback gates
            are complete.

            - Generated: `2026-07-14T03:31:53+00:00`
- Branch: `sprint/mac-control-plane-foundation`
- Commit: `db4d93a2652a704dfa9a7e149623064adb961504`
- Runtime commit: `db4d93a2652a`
<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:END -->

<!-- AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:START -->
## 2026-07-14 — Headless Recovery

            The Mac Control Plane recovered its read-only
            AIControlCenter API following a full reboot
            without a GUI login.

            The recovered service retained:

            - non-root application execution
            - commit-specific Runtime selection
            - localhost-only networking
            - read-only Shadow enforcement
            - system LaunchDaemon supervision

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
## 2026-07-14 — Shadow Observation Sprint

The Mac Control Plane entered its 24-hour read-only
Shadow observation phase after Headless Reboot Recovery.

No production cutover was performed.

Configured: `2026-07-14T04:19:41+00:00`
<!-- AICONTROLCENTER:SHADOW_OBSERVATION:END -->

<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## 2026-07-16 — Mac Control Plane Completed

The Mac mini M4 Control Plane completed its
foundation and operational validation program.

Milestones:

- Headless system LaunchDaemon recovery
- Non-root AIControlCenter execution
- Commit-specific Runtime enforcement
- `23.535`-hour Shadow observation
- `283/283` successful observations
- Canonical manager reconciliation
- Transactional apply and rollback
- launchd settle policy
- Final canonical apply
- Final restart:
  `19761 → 19842`
- Health HTTP `200`
- Write protection HTTP `405`
- Localhost-only listener `127.0.0.1:18100`

The Control Plane implementation is complete.
Ubuntu remains a stateless infrastructure worker.
Production write cutover is intentionally deferred.
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->

## 2026-07-16 — PI-001 Dashboard Shadow API Integration

Status: COMPLETE

Implemented:

- Dashboard Control Plane JSON contract
- Shadow read-only enforcement
- Immutable Runtime metadata provider
- Runtime metadata schema validation
- Commit-specific Runtime metadata generation
- Metadata-gated Runtime activation

Validated:

- Runtime commit: `ba8d2c9772577863c3c040d01654c4f011e2d45e`
- Runtime short commit: `ba8d2c977257`
- `GET /health`: HTTP `200`
- `GET /dashboard`: HTTP `200`
- `POST /dashboard`: HTTP `405`
- Listener: `127.0.0.1:18100`
- Runtime commit matches Git HEAD

Architecture result:

- Mac mini remains the Control Plane.
- AIControlCenter remains the orchestration layer.
- Ubuntu remains a stateless infrastructure worker.
- Dashboard requests do not execute Git, launchctl or shell commands.

<!-- AICONTROLCENTER:PI-002:START -->
## 2026-07-17 — PI-002 Ubuntu Worker Health JSON Adapter

PI-002 established the first Production read-only integration between the Mac mini Control Plane and the Ubuntu infrastructure worker.

Implemented:

- Worker health JSON schema and validation
- SSH transport timeouts and error handling
- Production worker configuration selection
- Worker monitoring through `MonitoringSnapshot`
- Dashboard worker JSON integration
- system LaunchDaemon worker environment loading
- `root:staff 640` environment permission contract
- Default `ubuntu-main` monitoring on `GET /dashboard`

Production validation:

- Implementation commit: `39dc5c3db72c9ac1592fc3920012aba3eacd23cd`
- Immutable implementation runtime: `39dc5c3db72c`
- LaunchDaemon PID during validation: `32297`
- Health HTTP: `200`
- Dashboard HTTP: `200`
- Worker count: `1`
- Worker JSON contract: valid
- Full regression: `412 passed, 5 deselected`

The remote SSH command returned exit status `255`. AIControlCenter correctly represented this as an optional structured worker error while preserving Dashboard availability.

Architecture result:

- AIControlCenter remains the single Control Plane.
- Mac mini remains the always-on Brain.
- Ubuntu remains a stateless optional infrastructure worker.
- Infrastructure failure does not migrate business logic or state to Ubuntu.
<!-- AICONTROLCENTER:PI-002:END -->

<!-- AICONTROLCENTER:PI-003:START -->
## 2026-07-19 — PI-003 Ubuntu Worker Minimum Closure

PI-003 closed the initial Ubuntu integration program and shifted platform priority to the Mac mini standalone Production environment.

Ubuntu boot validation confirmed:

- `docker.service` was enabled and active.
- Immich containers started automatically.
- Nextcloud containers started automatically.
- Required containers used `restart: unless-stopped`.
- Immich returned HTTP `200` before shutdown.
- Nextcloud returned the expected login redirect.

Mac standalone validation confirmed after Ubuntu shutdown:

- AIControlCenter Control Plane health: `ONLINE`
- Health endpoint: HTTP `200`
- Dashboard endpoint: HTTP `200`
- Ubuntu worker status: `OPTIONAL_UNAVAILABLE`
- Optional worker errors remained structured JSON.
- Validated implementation runtime: `85e0d2186dcd`

Architecture decision:

- Ubuntu may remain powered off until infrastructure services are required.
- Mac mini standalone service deployment is the next Production priority.
- Detailed Ubuntu telemetry and lifecycle automation were moved to backlog.
<!-- AICONTROLCENTER:PI-003:END -->

<!-- AICONTROLCENTER:PI-004:START -->
## 2026-07-20 — PI-004 Mac Standalone Production Baseline

PI-004 established the Mac mini as an independent Production Control Plane.

Validated capabilities:

- system LaunchDaemon supervision
- immutable runtime deployment
- Health, Dashboard and Homepage API availability
- Homepage read-only standalone projection
- Ubuntu optional-worker continuity
- optional external storage and backup semantics
- automatic service recovery after Mac reboot
- full test suite and Production evidence

The program now shifts to reusable Mac service deployment, starting with Ollama.
<!-- AICONTROLCENTER:PI-004:END -->

<!-- AICONTROLCENTER:PI-005:START -->
## PI-005 — Mac Service Deployment Platform Baseline

AIControlCenter introduced a reusable JSON-first deployment governance layer for native Mac services.

The Sprint delivered validation, planning, inspection, desired/actual comparison, rollback-aware dry-run generation, and an expiring approval contract.

No Ollama binary, service, model, or write executor was deployed during this Sprint.
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

PI-007 established AIControlCenter as the source of truth for approved model
policy and compliance evaluation.

Implementation history:

- Added the canonical model-governance registry.
- Added a strict read-only registry loader.
- Added registry-versus-Ollama inventory evaluation.
- Added `GET /api/governance/models`.
- Verified that OpenAPI exposes only `GET` for the governance endpoint.
- Completed focused and full-suite validation.
- Deployed immutable runtime `39fe04e3330e`.
- Validated Production health, Ollama inventory, governance output, and Git
  cleanliness.
- Validated rollback readiness using previous runtime `3679588b760c` without
  switching the live runtime.

Operational validation confirmed:

- health status `ONLINE`
- Ollama status `ONLINE`
- governance mode `read-only`
- default policy `DENY`
- approved model count `0`
- observed model count `0`
- violation count `0`
- write operations disabled

Validation notes:

- LaunchDaemon uses `/bin/bash` as `ProgramArguments[0]` and the installed
  runner as the following argument.
- The runner source and installed copy have matching hashes.
- No fixed immutable release ID is embedded in the runner.
- macOS process output resolves the virtual-environment Python executable to
  its underlying Homebrew Python path; this is not a runtime-binding failure.
- Two validation gates produced false negatives because they assumed literal
  runner paths in process output. Corrected gates passed.
<!-- AICONTROLCENTER:PI-007:END -->

## PI-008 — Model Governance Audit and Dashboard Integration

PI-008 introduced a Production-ready, read-only audit layer for approved model governance.

### Delivery timeline

The sprint delivered:

- canonical audit snapshot contracts
- SQLite migrations and append-only enforcement
- immutable repository operations
- audit snapshot generation
- compliance comparison
- bounded read-only query services
- governance audit APIs
- Dashboard integration
- deployment provenance

### Production incident

During the initial deployment, the legacy runner compared the active runtime directory name with mutable Git HEAD.

After the repository advanced while the previous runtime remained active, LaunchDaemon repeatedly exited with:

`Runtime commit does not match Git HEAD`

Recovery established the following operational rules:

- use `os.replace()` for atomic symlink replacement
- never depend on mutable Git HEAD for Production restart
- store provenance inside each release
- validate runner and runtime as one deployment contract
- gate endpoint validation behind health checks
- use bounded Dashboard timeouts greater than the observed normal latency
- distinguish diagnostic script failures from application failures

A metadata bridge runner restored Production safely. The bridge behavior was then canonicalized in the repository and committed as:

`b9ad351a7241e521c8964218f59724fcb04db93c`

### Final Production state

- active runtime: `b9ad351a7241`
- rollback runtime: `0352e396f329`
- full suite: `636 passed, 5 deselected`
- Production closure gate: passed
- Ollama model count: `0`
- governance mode: read-only
- audit database: Mac mini application data root
- SQLite append-only enforcement: validated
- Ubuntu AI workload and audit state: none

<!-- PI-009:START -->
## 2026-07-22 — PI-009 Governance Audit Operations

PI-009 implemented freshness-aware, read-only operational visibility
for governance audit snapshots and SQLite online-backup verification.

Implementation commit:

`e1d46099427321a3ba7a150aad589320c8f1261a`

Final implementation validation:

- 17 targeted tests passed;
- 710 tests passed, 5 deselected, 427 warnings;
- production database SHA-256:
  `435857ee9e5940fc4ab18d164a63144d422955724e8c818f33529264b792663c`;
- production database content unchanged;
- WAL content unchanged;
- repository clean.

Production migration and scheduler activation were intentionally not
performed.
<!-- PI-009:END -->

<!-- PI-009-OPERATIONS-FINAL:BEGIN -->
## 2026-07-22 — PI-009 Governance Operations Closed

PI-009 completed the governance operation execution
platform.

Evidence:

- Production migration followed a verified byte-identical
  backup.
- Manual SQLite backup verification completed.
- SystemUTCClock was added in commit
  58fca02274bc516933508f6a3fa48fc0a046d174.
- The JSON-first runner was added in commit
  d1072aa35fb5034c1097923fd7f6d7643132460b.
- Runner implementation passed 14 targeted tests.
- Full regression passed 717 tests with 5 deselected and
  the existing 427-warning baseline.
- Production database and WAL were unchanged.
- No scheduler was installed or activated.

Automated cadence inference was rejected. Execution
capability and scheduling policy were deliberately split,
and activation moved to PI-010.
<!-- PI-009-OPERATIONS-FINAL:END -->

<!-- PI-010-HEADLESS-PRODUCTION-CLOSE-2026-07-23 -->
## 2026-07-23 — PI-010 Closed

PI-010 delivered Production governance scheduling on the Mac mini Control Plane.

Direct launchctl and GUI-dependent activation paths were rejected during operational validation. The selected Production deployment is the managed user crontab adapter.

Immutable snapshot serialization was corrected in commit fee92a7b091d53201fd923ef42b7e1e75edd00be. Capability boundaries were finalized in commit 88f548fcc7b7cf849fdc9e9897993576e3bf68c0. Dedicated semantic capabilities were added in commit 3a7033aaee56145928bfd5fa2fdaaab318ecf77a.

Both Production operations reached run_succeeded, rollback passed, the scheduler remained active, and the full regression suite passed.

<!-- BEGIN AICONTROLCENTER SPF-002 PROJECT_HISTORY -->
## Shopping Platform Foundation Decision

Date: 2026-07-23

Shopping Platform was established as an AIControlCenter bounded domain.
It is not a WordPress plugin and it is not an Ubuntu application.

WordPress remains a replaceable headless CMS.
WooCommerce remains a replaceable commerce engine.

External components cannot own platform policy, authorization, recommendations, audit, workflow, customer automation, or deployment control.

Monitoring must stabilize before validation.
Validation must stabilize before approved write operations.
Write interfaces are intentionally absent during Sprint 1.
<!-- END AICONTROLCENTER SPF-002 PROJECT_HISTORY -->

<!-- SPF-003:START -->
## 2026-07-23 — SPF-003 Closed

SPF-003 established the Shopping bounded-context package structure, migrated the legacy ports module to a package without changing its bytes, preserved `CommerceCatalogPort`, introduced seven read-only or compute-only Protocol interfaces, added provisional JSON-first contracts, and validated import safety and deny-by-default write governance.

Implementation commit: `fd52aad1d9af9d056d80d8f7d6170605ea0d11b2`.

Validation: 6 targeted tests and 747 full regression tests passed with 5 deselected.

Next production milestone: **SPF-004 — Canonical JSON Schema v1**.
<!-- SPF-003:END -->


<!-- AICONTROLCENTER-SPF-004-CLOSED -->
## 2026-07-23 — SPF-004 Canonical JSON Schema v1 Closed

SPF-004 established the first versioned canonical Shopping contract layer in AIControlCenter.

Delivered:

- Draft 2020-12 JSON Schema contract set
- 15 canonical contract bindings
- 17 schema resources
- `registry.json`
- explicit local schema registry loader
- fail-closed Python validator
- pinned runtime dependencies
- permanent contract validation tests

Validation:

- targeted: 6 passed
- full regression: 753 passed

Safety:

- production unchanged
- Ubuntu unchanged
- remote schema resolution disabled
- Shopping write operations disabled

During gate development three test-harness defects were identified without production impact:

1. `TEST_ASSERTION_FALSE_POSITIVE_GLOBAL_PATH_BLOCK`
2. `TEST_ASSERTION_FALSE_POSITIVE_STRING_PREFIX_COUNT`
3. `TEST_HARNESS_EMBEDDED_NEWLINE_DEDENT_DEFECT`

The resulting gate policy now favors semantic validation, AST parsing, exact Git scope, byte comparison, and public runtime behavior instead of brittle textual assertions.

Implementation commit: `7a436a62fbaa2c176e877297d88b810b255f2776`

<!-- SPF-005-CLOSE:BEGIN -->
## 2026-07-23 — SPF-005 Capability Registry deny-by-default

SPF-005 introduced AIControlCenter-owned capability governance for the Shopping Platform Foundation.

Final implementation:
- static immutable capability registry
- 11 registered READ capabilities
- 9 reserved non-executable WRITE capability identifiers
- `authorize_read` application orchestration
- `PolicyDecisionPort` integration
- fail-closed request and decision capability validation
- fail-closed policy exception normalization
- vendor exception message leak prevention

Validation:
- targeted: 22 passed
- full regression: 775 passed
- production modified: false
- Ubuntu modified: false
- write operations enabled: false

Implementation commit: `f807cc0dfb8a27d2bf387bdc3dd897e4fe331953`.

Harness recovery classification: `TEST_HARNESS_LITERAL_INDENTATION_MISMATCH`.

Security hardening classification: `POLICY_EXCEPTION_FAIL_CLOSED_HARDENING`.

Next task: SPF-006 Read Adapter Contracts.
<!-- SPF-005-CLOSE:END -->

<!-- SPF-006-CLOSE:BEGIN -->
## 2026-07-23 — SPF-006 Read Adapter Contracts

SPF-006 established vendor-neutral read adapter contract boundaries owned by AIControlCenter.

Implemented:
- Commerce adapter conformance contract
- CMS adapter conformance contract
- JSON-first contract manifests
- exact async port signature validation
- canonical return contract validation
- SPF-005 capability binding reuse
- Commerce/CMS isolation validation
- WRITE-like public method rejection

Validation:
- targeted: 28 passed
- full regression: 803 passed
- production modified: false
- Ubuntu modified: false
- write operations enabled: false
- live vendor connection enabled: false

Implementation commit: `fd1bbe2ff212e9eeb442562ffeed32bed97c1072`.

Next task: SPF-007 Adapter Health Monitoring.
<!-- SPF-006-CLOSE:END -->

<!-- SPF-007-CLOSE:BEGIN -->
## 2026-07-23 — SPF-007 Adapter Health Monitoring

SPF-007 established the AIControlCenter-owned health monitoring boundary for Shopping adapters.

Implemented:
- canonical health probe normalization
- HEALTHY, DEGRADED, and UNAVAILABLE semantics
- vendor-neutral failure taxonomy
- sanitized failure detail codes
- deterministic stateless health aggregation
- fail-closed empty monitoring state
- JSON-compatible monitoring snapshots
- timeout and failure compatibility validation

Validation:
- targeted: 34 passed
- full regression: 837 passed
- production modified: false
- Ubuntu modified: false
- write operations enabled: false
- live vendor connection enabled: false

Implementation commit: `63263b734ead4eb083f9b91923f4b41c3b644e34`.

Next task: SPF-008 Read-only Snapshots.
<!-- SPF-007-CLOSE:END -->

<!-- SPF-008-CLOSE:BEGIN -->
## 2026-07-23 — SPF-008 Read-only Snapshots

SPF-008 established the AIControlCenter-owned read-only snapshot boundary for Shopping.

Implemented:
- deterministic canonical snapshot normalization
- immutable and detached snapshot read models
- authorization-before-repository query orchestration
- fail-closed authorization behavior
- sanitized repository failure handling
- read-only snapshot capability enforcement
- isolation and immutability regression coverage

Validation:
- targeted: 35 passed
- full regression: 872 passed
- production modified: false
- Ubuntu modified: false
- write operations enabled: false
- snapshot persistence enabled: false
- vendor refresh enabled: false

Implementation commit: `d8859a3706a087f88be513e32097b22c9a8ec3d6`.

Next task: SPF-009 Validation and Schema Drift.
<!-- SPF-008-CLOSE:END -->

<!-- AICONTROLCENTER:SPF-009:CLOSED -->
## SPF-009 Validation and Schema Drift Closure

- Closure date: 2026-07-23.
- Implementation commit: `3fa21878e72cdb9608a728a1c676e70fb70b5717` (`feat(shopping): add schema validation and drift monitoring`).
- SPF-009 introduced canonical runtime validation, local-only schema resolution, conservative drift detection, and read-only drift monitoring.
- Recovery history: the discovery integration verifier was corrected to honor the authoritative `context` and `adapter_name` port contract; the monitor test harness was made independent of optional pytest async plugins.
- Final targeted validation: 58 passed.
- Final full regression: 930 passed, 5 deselected.
- Production modified: false; Ubuntu modified: false; application write operations enabled: false.
- Next milestone: SPF-010.

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
- Historical milestone: Shopping Platform Foundation reached 10/10 and passed its production-readiness gate.
- SPF-010 completed without enabling vendor writes, Ubuntu application state, or Ubuntu business logic.

<!-- SRI-06B-R1:PROJECT-HISTORY -->
## Shopping External Read Integration

SRI established the first production external READ plane for the AI Home Datacenter.

### Milestones

- SRI-01 and SRI-02 established inventory and GET-only policy.
- SRI-03 opened the public edge and validated WooCommerce READ integration.
- SRI-04 introduced core/cms and validated canonical WordPress reads.
- SRI-05 introduced ExternalReadObserver and validated production operational evidence.
- SRI-06 validated the repository and prepared the Codex handoff.

### Closure evidence

- SRI-03: 2197eac7020c7b6901e7a3454b83155c1ed2a0dd44ccd7297e8e6fc633a16f09
- SRI-04: 9d12681647aa7f65bc9924dbd31d8c3be6b493dd6f7a742881592989520542d3
- SRI-05: da98aad81e845357b4611b6ed694dde48cf0346ecd3191d534826019865ef797
- SRI-06A: 27f94520d0b83c1af36a476ff3580a87cb5ec9307567e446b2bad5b5c9bd39fa

### Final observed production state

- Products: 0.
- Orders: 0.
- Published posts: 1.
- Published pages: 5.
- Credential permission: read.
- Production business writes: 0.
- Ubuntu business logic changes: 0.
<!-- END SRI-06B-R1 -->

<!-- AICONTROLCENTER:DPL-01:START -->
## 2026-07-28 — DPL-01 Deployment Package Decisions

DPL began after SRI established the production external READ baseline. The
program was deliberately constrained to immutable desired-state and observation
contracts because deployment intent must be reviewable without becoming
execution authority.

The Mac mini M4 remains the always-on Brain and single Control Plane so
governance, authorization, approval, audit and orchestration have one owner.
Ubuntu remains optional and stateless because moving business logic,
application state or generic execution there would split authority and weaken
auditability.

Read, plan and apply were separated because existing deployment and remote
worker code exposes mutation surfaces near inspection and planning. DPL-02
therefore contains no apply path and activates no Ubuntu adapter.
`UbuntuWorkerClient.execute` is excluded; any later SSH use must sit behind
fixed typed read-only actions.

Host Caddy remains the sole public edge to avoid competing ingress ownership.
The Caddy, Colima, Compose and Commerce host-port path will receive one
canonical end-to-end validation contract. Mac production supervision is
launchd; inherited Linux systemd Control Plane artifacts are retained for
history but classified `LEGACY_UNSUPPORTED` and production-prohibited.

Production activation and production writes were not authorized.
<!-- AICONTROLCENTER:DPL-01:END -->

## 2026-07-29 — DPL-04D Readiness Accepted

DPL-04D closed DPL-04 with a pure evidence-driven gate. The canonical fixture
accepted M2 readiness for a separately authorized Mac-only non-production
sandbox. No pilot or production activation occurred. Persistent SQLite
deployment audit remains required before broader mutable deployment.

## 2026-07-29 — M3-A2B Closed

M3-A2B added the Mac Control Plane-owned durable permit reservation and
terminal-state writer without modifying the M3-A2A read-only foundation.
Temporary pytest databases validated atomicity, hash chains, idempotency and
concurrency. The operational replay database was not created, the writer was
not activated, raw nonce writes remained disabled and Production activation
remained `NOT_AUTHORIZED`. M3-A2C is next.
