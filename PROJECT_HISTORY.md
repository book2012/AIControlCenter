# Project History

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
