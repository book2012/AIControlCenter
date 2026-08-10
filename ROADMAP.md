# Roadmap

## AI provider architecture

- [x] AI-PROVIDER-01A: vendor-neutral contract, strict router, normalized errors,
  network-free OpenAI boundary and deterministic fake adapter.
- [ ] AI-PROVIDER-01B: Responses API repository transport and smoke CLI are
  implemented; human-controlled authenticated smoke is pending.
- [ ] AI-PROVIDER-01C: candidate Runtime integration and promotion.
- [x] AI-PROVIDER-01C-A: canonical Control Plane `BrainAgent.ask` workflow
  integration through `ProviderRouter` (repository only; no authenticated call).
- [ ] AI-PROVIDER-01C-B: create a new Candidate Runtime.
- [ ] AI-PROVIDER-01C-C: Production promotion only after explicit human
  authorization.
- [ ] Synchronize the provider architecture record to Notion
  (`DEFERRED_UNTIL_FINAL_PHASE`).

Production Runtime remains `7b171f135dc7`; PI-009 authorization remains intact.

<!-- AICONTROLCENTER:ACTIVATION_01C_POINTER_CLOSEOUT:START -->
## ACTIVATION-01C Controlled Pointer Activation

Status: `COMPLETE`

Authorized transition:

`b9ad351a7241 -> acd80ab9f6ae`

Runtime pointer activation:

`PASS`

Activation report SHA-256:

`d59a3aa81accca4e6f330c85774924221e33e247376a069a1d922f5716dec24a`

Natural launchd KeepAlive recovery:

`PASS`

Explicit service restart commands:

`0`

Launchd state:

`running`

Listener:

`127.0.0.1:18100`

Listener/PID correlation:

`PASS`

Approved wrapper SHA-256:

`a58d926f8845f6b0aa7863250b02c0c461ea843bfa03a83313eaaa547ca98212`

Wrapper serving target:

`core.api.shadow:app`

HTTP validation:

- `GET /health -> 200`
- `GET /runtime/health -> 200`
- `POST /health -> 405`

Post-activation ACTIVATION-01B inspection ID:

`activation-inspection-bc8f2b34d45242c4b835d4ba852667a3`

Post-activation report digest:

`sha256:f419242b927804a6c97ad947ad4eb2deb9b2a07545724d750fd85ab3a80def22`

01B terminal status:

`BLOCKED`

Remaining transition-phase blockers:

`["GIT_IDENTITY_MATCH","GIT_VALIDATION_COMPLETE","PROCESS_SERVING_TARGET_MATCH","RUNTIME_CURRENT_MATCH"]`

Operational Runtime, launchd, listener and HTTP checks passed.

The residual blockers are contract-phase mismatches:

- pre-activation Runtime expectation
- Control Plane Git identity versus Candidate source identity
- launchd wrapper indirection versus direct serving-target inference

01C independently verifies the exact approved wrapper SHA and its
static `uvicorn core.api.shadow:app` exec chain.

Rollback executions:

`0`

Explicit launchd mutation commands:

`0`

Caddy changes:

`0`

Public openings:

`0`

Ubuntu changes:

`0`

Production authorization:

`NO`

ACTIVATION-01C does not constitute PI-009 Production authorization.
<!-- AICONTROLCENTER:ACTIVATION_01C_POINTER_CLOSEOUT:END -->

<!-- AICONTROLCENTER:ACTIVATION_01C_AUTHORIZATION_FREEZE:START -->
## ACTIVATION-01C Authorization Contract

Status: `FROZEN`

Active Runtime: `b9ad351a7241`

Candidate Runtime: `acd80ab9f6ae`

Candidate source commit: `acd80ab9f6aeb848900e1a19e3fa3afd69face8a`

Candidate startup import gate: `PASS`

Observed Active Runtime failure:

`ModuleNotFoundError: No module named 'jsonschema'`

First mutation boundary:

`Runtime pointer activation only`

Explicit service restart authority:

`NO`

Automatic rollback authority:

`NO`

Ubuntu changes:

`NO`

Public opening:

`NO`

Production authorization:

`NO`

Canonical human approval statement:

`ACTIVATION-01C AUTHORIZE POINTER SWITCH acd80ab9f6ae FROM b9ad351a7241`

The exact mutation command and rollback boundary are defined in:

- `docs/deployment/ACTIVATION-01C-CONTROLLED-ACTIVATION-ARCHITECTURE.md`
- `docs/operations/macos/ACTIVATION-01C-HUMAN-AUTHORIZATION-CONTRACT.md`
<!-- AICONTROLCENTER:ACTIVATION_01C_AUTHORIZATION_FREEZE:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_OPERATIONAL_VALIDATION:START -->
## ACTIVATION-01B Read-Only Operational Validation

Status: `COMPLETE`

Classification: `PASS / FAIL-CLOSED`

The bounded read-only inspector completed the full Mac control-plane
observation path.

Inspector exit code: `2`

Overall status: `BLOCKED`

Inspection ID: `activation-inspection-7f2591c5066142dfaa383a31ae943f0d`

Report digest: `sha256:5afa71f7bd1edb1111203f0227a1cb3314a306cc1355ec465d33f5d10800e9e4`

Inspector commit: `698f60444894cb4f22c9cbc647abc2ee2a530e59`

Blocking reasons:

`["GIT_IDENTITY_MATCH","GIT_VALIDATION_COMPLETE","HTTP_GET_HEALTH","HTTP_GET_RUNTIME_HEALTH","HTTP_POST_HEALTH_DENIED","LAUNCHD_RUNNING","LISTENER_COUNT_MATCH","LISTENER_PID_MATCH","PROCESS_SERVING_TARGET_MATCH"]`

Sanitized errors:

`[]`

Operational safety:

- Runtime mutations: `0`
- Service restarts: `0`
- Rollback executions: `0`
- launchd changes: `0`
- Caddy changes: `0`
- Public openings: `0`
- Production writes: `0`
- Ubuntu changes: `0`
- Production authorization: `NO`

`READY_FOR_AUTHORIZATION_REVIEW` is evidence readiness only.

A `BLOCKED` result is a successful fail-closed operational
validation. It does not authorize remediation or Production.

Notion synchronization remains pending as the final
project-management gate.
<!-- AICONTROLCENTER:ACTIVATION_01B_OPERATIONAL_VALIDATION:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_HTTP_CONTRACT_FIX:START -->
## ACTIVATION-01B HTTP Evidence Contract Correction

Status: `COMPLETE`

Operational validation exposed a direct-localhost
`HTTP_PROBE_FAILED` condition.

The registered HTTP evidence contract uses:

- `actual_status`
- `result`
- `body_length`
- `sanitized_error`
- `attempt_count`
- `redirect_followed`

Transport or connection failures are now represented as probe
evidence:

- `actual_status = null`
- `result = ERROR`
- `body_length = 0`
- bounded `sanitized_error`
- `attempt_count = 1`
- `redirect_followed = false`

The corresponding blocking inspection check fails.

A transport failure therefore resolves to `BLOCKED` rather than
being promoted to an inspector execution `ERROR`.

Runtime mutations: `0`
Service restarts: `0`
Rollback executions: `0`
launchd changes: `0`
Caddy changes: `0`
Public openings: `0`
Ubuntu changes: `0`
Production authorization: `NO`
<!-- AICONTROLCENTER:ACTIVATION_01B_HTTP_CONTRACT_FIX:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_LAUNCHD_SCOPE_FIX:START -->
## ACTIVATION-01B Launchd Parser Scope Correction

Status: `COMPLETE`

Operational validation discovered that `launchctl print` contains
nested resource and jetsam records whose field names overlap with the
top-level service record.

Observed example:

- service scope: `state = spawn scheduled`
- resource scope: `state = active`
- jetsam scope: `state = active`

The previous parser flattened all scopes and therefore emitted
`LAUNCHD_CONFLICTING_FIELD`.

The corrected parser is brace-depth aware and consumes identity,
state, pid, username and program arguments only from the service
record scope.

Nested launchd metadata is ignored rather than selected
heuristically.

Conflicting values within the service scope still fail closed.

The change affects observation logic only.

Runtime mutations: `0`
Service restarts: `0`
Rollback executions: `0`
launchd changes: `0`
Caddy changes: `0`
Public openings: `0`
Ubuntu changes: `0`
Production authorization: `NO`
<!-- AICONTROLCENTER:ACTIVATION_01B_LAUNCHD_SCOPE_FIX:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_RUNTIME_LAYOUT_FIX:START -->
## ACTIVATION-01B Runtime Layout Correction

Status: `COMPLETE`

Read-only operational validation discovered a Control Plane
observation-path mismatch.

Canonical Runtime layout:

- Runtime environments: `runtime/venvs/<runtime-id>`
- Candidate metadata: `metadata.json`
- Source identity: `.aicontrolcenter-source-commit`

The inspector previously looked under `runtime/releases/<runtime-id>`
and expected `runtime-metadata.json`.

The repair changes observation logic only.

No Runtime environment was created, removed or modified.

Runtime mutations: `0`
Service restarts: `0`
Rollback executions: `0`
launchd changes: `0`
Caddy changes: `0`
Public openings: `0`
Ubuntu changes: `0`
Production authorization: `NO`
<!-- AICONTROLCENTER:ACTIVATION_01B_RUNTIME_LAYOUT_FIX:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_C4:START -->
## ACTIVATION-01B-C4 Read-Only Inspector

Status: `COMPLETE`

ACTIVATION-01B read-only inspector implementation is complete.

Implemented capabilities:

- Versioned activation inspection policy
- Versioned localhost route manifest
- Existing bounded Git evidence reuse
- Bounded macOS read-only adapters
- Exact `launchctl print` inspection
- Structured `lsof -F` listener inspection
- Runtime filesystem observation
- Isolated Runtime Python `-I -S --version` probe
- Exact localhost HTTP probes
- Immutable pure evaluator
- Launchd serving-target observation
- Canonical `PROCESS_SERVING_TARGET_MATCH` check
- Actual-evidence report materialization
- Evidence digest regeneration
- Check evidence-reference regeneration
- Canonical report digest generation
- Final report JSON Schema validation
- Deterministic CLI exit codes

Status contract:

- `READY_FOR_AUTHORIZATION_REVIEW` -> exit `0`
- `BLOCKED` -> exit `2`
- Invalid policy, manifest or contract -> exit `3`
- Observation or internal error -> exit `4`

Evidence mismatches remain `BLOCKED`.

No exit code grants Production authorization.

C4 focused integration gate: `43 passed`

Base commit: `9f7d71a08235d23502c72c417a029b480b29a5e8`

Runtime mutations: `0`
Service restarts: `0`
Rollback executions: `0`
launchd changes: `0`
Caddy changes: `0`
Public openings: `0`
Ubuntu changes: `0`
Production authorization: `NO`

- [x] C1 contract foundation
- [x] C2 immutable models and pure evaluator
- [x] C3 bounded macOS adapters
- [x] C4 JSON runner and integration
- [ ] Controlled read-only operational validation
- [ ] Human authorization review
<!-- AICONTROLCENTER:ACTIVATION_01B_C4:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_C3:START -->
## ACTIVATION-01B-C3 Bounded macOS Read-Only Adapters

Status: `COMPLETE`

Implemented bounded macOS observation adapters for:

- exact `launchctl print`
- structured `lsof -F` listener inspection
- Runtime pointer, metadata and source-marker reads
- isolated Runtime Python `-I -S --version` probe
- exact `127.0.0.1` single-attempt HTTP probes

Safety boundaries:

- absolute executable paths
- `shell=False`
- bounded timeout and output size
- no retries or redirects
- no credentials, cookies or authorization headers
- no launchd mutation operations
- no Runtime mutation
- no Ubuntu operations

Focused gate: `35 passed`

Base commit: `e2781094351fd9d68b562f0806799c8dbc4f100a`

Production remains `NOT_AUTHORIZED`.

- [x] Command execution port
- [x] HTTP transport port
- [x] `launchctl print` adapter
- [x] `lsof -F` listener adapter
- [x] Runtime filesystem adapter
- [x] Isolated Runtime Python probe
- [x] Exact localhost HTTP transport
- [x] Bounded parser tests
- [ ] C4 JSON runner and orchestration integration
<!-- AICONTROLCENTER:ACTIVATION_01B_C3:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_C2:START -->
## ACTIVATION-01B-C2 Pure Evaluator

Status: `COMPLETE`

Implemented immutable inspection models and a deterministic,
fail-closed evaluator producing only:

- `READY_FOR_AUTHORIZATION_REVIEW`
- `BLOCKED`
- `ERROR`

The evaluator validates C1 contracts and digest bindings, orders
checks deterministically, derives blocking reasons, sanitizes
errors and emits a canonical inspection report.

Focused gate: `PASS`

Base commit: `4ad97e44c9bf499fc3368be5d41017ccb9924134`

No host adapter, Runtime command, HTTP probe, service operation,
launchd change, Ubuntu change or Production authorization occurred.

Production remains `NOT_AUTHORIZED`.

- [x] Immutable models
- [x] Pure fail-closed evaluator
- [x] Deterministic report generation
- [x] Host-dependency prohibition tests
- [ ] C3 bounded macOS read-only adapters
<!-- AICONTROLCENTER:ACTIVATION_01B_C2:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_C1_CLOSEOUT:START -->
## ACTIVATION-01B-C1 Contract Foundation

Status: `COMPLETE`

- [x] Inspection policy Schema
- [x] Route-manifest Schema
- [x] Inspection-report Schema
- [x] Registry resources and bindings
- [x] Synthetic fixtures
- [x] Canonical digest bindings
- [x] Secret-field rejection
- [x] Pure-validation tests
- [x] Focused contract gate
- [x] Safe deployment regression
- [ ] Operational test-root harness stabilization
- [ ] C2 immutable models and pure evaluator

Production remains `NOT_AUTHORIZED`.
<!-- AICONTROLCENTER:ACTIVATION_01B_C1_CLOSEOUT:END -->

<!-- AICONTROLCENTER:ACTIVATION_01A:START -->
## ACTIVATION-01A — Architecture and Runbook Only

Status: `COMPLETE`

Contract documentation commit: `d14058553baa1dfc45e027a59ff580013584913b`

- [x] Atomic activation contract
- [x] Exact service restart contract
- [x] Post-activation localhost validation contract
- [x] Fail-closed failure conditions
- [x] Separate rollback authorization boundary
- [x] Evidence requirements
- [x] Production authorization boundary
- [x] Repository `PYTHONPATH` limitation
- [x] Documentation commit and remote synchronization

No operational activation is authorized.

## ACTIVATION-01B — Read-Only Activation Inspector

Status: `ARCHITECTURE_FROZEN`

- [x] Repository capability inventory
- [x] Targeted reusable-component review
- [x] Architecture document
- [x] macOS read-only runbook
- [x] Host command allowlist
- [x] Runtime Python probe hardening
- [x] HTTP method-denial probe hardening
- [x] CLI status and exit-code semantics
- [x] No-mutation test strategy
- [ ] Versioned activation policy schema
- [ ] Versioned localhost route-manifest schema
- [ ] Activation inspection report schema
- [ ] Registered contract fixtures
- [ ] Pure models and evaluation service
- [ ] Bounded macOS adapters
- [ ] Canonical JSON CLI
- [ ] Fixture-based no-mutation test suite
- [ ] Read-only real-host validation
- [ ] Implementation documentation closeout

Production remains `NOT_AUTHORIZED`.
<!-- AICONTROLCENTER:ACTIVATION_01A:END -->

M4-A3 is closed after deterministic test-only lifecycle and live-boundary
isolation validation. Next is `M4-A4_READ_ONLY_OPERATIONAL_OBSERVATION` under
separate architecture and authorization gates. No M4-A3 artifact is
operationally valid. Production remains `NOT_AUTHORIZED`, Ubuntu remains
excluded, and the 427 warnings remain backlog.

M3-A4B2B2B-R4 closes strict-live contract compatibility only. Next is fresh
independent approval bound to R4 and a separately authorized Mac bootstrap.
M3-A4B3 remains blocked until actual bootstrap succeeds. Production remains
`NOT_AUTHORIZED`.

Recovery-2 completes reviewed evidence only. Actual managed targets remain
absent; next is fresh independent approval bound to the final R3 commit before
any authorized Mac bootstrap. Production remains `NOT_AUTHORIZED`.

The blocked R3 attempt is recovered with reviewed live composition and
pytest-only controlled orchestration. The actual operation remains
`NOT EXECUTED`; next is fresh independent approval bound to the recovery
commit before any authorized Mac bootstrap.

## M3-A4B2B2B-R1 closure

Existing safe parent compatibility is complete. Shared siblings remain outside
deployment ownership. Next: M3-A4B2B2B fresh approval and authorized Mac
bootstrap; Production remains `NOT_AUTHORIZED`.

## Current milestone

- M3-A4A CLOSED
- M3-A4B1 CLOSED
- M3-A4B2A CLOSED
- M3-A4B2B0 CLOSED
- M3-A4B2B1A CLOSED after validation
- Next: M3-A4B2B1B Operator Approval and Operational Permit Issuance

## M3-A4B2B0 Closure and M3-A4B2B1

M3-A4B2B0 is closed after deterministic read-only Mac host preflight
validation. Operational permit and authorization remain absent, bootstrap has
not executed, targets remain uncreated, and Production remains
`NOT_AUTHORIZED`. Next: M3-A4B2B1 Operational Permit Issuance.

## M3-A4B2A Closure and M3-A4B2B

M3-A4B2A is closed after controlled executor validation beneath pytest-owned
temporary roots. Synthetic permit consumption, audit/replay bootstrap,
baseline backup/restore and cleanup are validated. Operational permit issuance
and bootstrap remain absent; Production activation remains `NOT_AUTHORIZED`.
Next: M3-A4B2B Authorized Mac Operational Bootstrap Execution.

## M3-A4B1 Closure and M3-A4B2

M2, M3-A1, M3-A2, M3-A3, M3-A4A and M3-A4B1 are closed. Controlled bootstrap
authorization capability is available and synthetic one-use permit validation
is complete. No operational permit was issued, bootstrap was not authorized or
executed, operational targets remain absent, and Production activation is
`NOT_AUTHORIZED`. Next: M3-A4B2 Controlled Mac Operational Bootstrap.

## M3-A2A Closure and M3-A2B

M2 controlled pilot validation, M3-A1 and M3-A2A are closed. Read-only
permit/replay integrity inspection is available, while the operational
database, durable reservation, consumption and persistent nonce writes remain
absent. Production activation is `NOT_AUTHORIZED`. Next: M3-A2B Durable Permit
Reservation and Consumption.

## M3-A1C Closure and M3-A2

M2 controlled pilot validation and M3-A1A through M3-A1C are closed after
pytest-only backup, restore and recovery validation. Operational database,
backup schedule, restore and persistent writer activation remain absent.
Production activation is `NOT_AUTHORIZED`. Next: M3-A2 Durable Permit and
Replay State.

## M3-A1B Closure and M3-A1C

M2 controlled pilot validation, M3-A1A and M3-A1B are CLOSED. The append-only
SQLite writer is implemented and validated only with pytest temporary
databases. The operational database does not exist, operational writer
activation is not started, persistent Production audit writes are not enabled,
and Production activation remains `NOT_AUTHORIZED`. Next: M3-A1C Backup,
Restore and Recovery Validation.

## M2-P3 Closure and M3-A1

M2-P1 through M2-P3 are CLOSED after one controlled pytest activation and one
controlled pytest rollback. Persistent host activation is NOT STARTED,
persistent host rollback and persistent SQLite audit are NOT IMPLEMENTED and
Production activation remains `NOT_AUTHORIZED`. Next: M3-A1 Durable SQLite
Audit Adapter.

## M2-P1 Closure and M2-P2

M2-P1 Controlled Non-Production Sandbox Pilot Authorization is CLOSED. Pilot
authorization policy is AVAILABLE; pilot activation is NOT STARTED. Persistent
SQLite audit is NOT IMPLEMENTED and Production activation remains
`NOT_AUTHORIZED`. Next: M2-P2 Controlled Sandbox Pilot Activation and Evidence.

## DPL-04C Closure

DPL-04C is complete. The Mac Control Plane owns durable deployment audit, with
pure canonical event and hash-chain contracts behind a replaceable port. The
future append-only SQLite adapter is selected but not implemented. DPL-04A,
DPL-04B and DPL-04C are closed; DPL-04D is ready. M2 remains incomplete and
production activation is `NOT_AUTHORIZED`.

## DPL-04B Closure

DPL-04B is complete. The Mac-only adapter can materialize deterministic
manifest and evidence JSON only under an explicit, confined non-production
sandbox root. Default composition remains deny-only; command execution,
durable audit and production activation remain prohibited. DPL-04C is next.

## DPL-04A Closure

DPL-04A is complete. Typed executor contracts and ports are limited to
non-production Mac Control Plane targets and use a deny-only default
composition. No concrete real executor or production activation is authorized.
DPL-04B is next.

## DPL-03 Closure

DPL-03A through DPL-03D are complete subject to repository validation.
DPL-03D is simulation-only and does not authorize or perform production
deployment. M2 remains incomplete; DPL-04 is the next separately gated
milestone.

## Complete

- Core Runtime
- Dashboard
- BrainAgent
- Telegram
- Conversation Memory
- SQLite
- Command Router

## Current

Doctor

## Next

Logs

Backup Verify

Worker Health

Backup Execute

Homepage

Mac mini Production

## Sprint 21

- [ ] Brain Scheduler
- [ ] Heartbeat
- [ ] Job Registry
- [ ] Scheduler API
- [ ] Job Runner

## Sprint 22

- [x] Memory Manager
- [x] Working Memory
- [x] Long-term Memory
- [x] Memory API
- [x] Telegram Memory Commands

## Sprint 23

- [ ] Knowledge Registry
- [ ] Markdown Loader
- [ ] Knowledge Search
- [ ] Knowledge API
- [ ] Telegram /knowledge
- [ ] BrainAgent Knowledge Context

<!-- AI_SHOPPING_PLATFORM_START -->
## AI Shopping Platform Roadmap

### S0 Control Plane Baseline

Status: In Progress

- Shopping domain bootstrap
- Health API
- Readiness API
- Capabilities API
- Virtual environment tests
- Documentation
- Git Production Gate

### S1 Read-only Product Catalog

- Commerce Catalog Port
- Mock Product Adapter
- Product list API
- Product detail API
- Pagination
- Schema validation

### S2 WordPress and WooCommerce Virtual Environment

- WordPress container
- WooCommerce installation
- Test catalog
- REST API credentials
- AIControlCenter read-only adapter

### S3 AI Product Workflow

- Product generator
- SEO writer
- Product description generator
- Category generator
- Human approval
- Audit history

### S4 Controlled Publishing

- Authentication
- Authorization
- Idempotency
- Controlled WooCommerce writes
- Rollback
- Audit logging

### S5 Shopping Homepage

- WordPress theme
- Homepage
- Category pages
- Product pages
- Shopping Assistant integration

### S6 Production Hardening

- ARM64 validation
- Mac mini deployment
- Restart recovery
- Monitoring
- Backup
- Runbook
<!-- AI_SHOPPING_PLATFORM_END -->

<!-- SHOPPING_M4_START -->

## Shopping Platform Roadmap

### M4 — Live WooCommerce Control Plane

- [x] Shopping domain bootstrap
- [x] WordPress runtime
- [x] WooCommerce runtime
- [x] Product API
- [x] Category API
- [x] Integration API
- [x] Adapter Factory
- [x] systemd Secret integration
- [ ] Final Production Gate and Git closeout

### M5 — Shopping Experience

- [ ] Shopping Homepage
- [ ] Product detail experience
- [ ] Shopping Dashboard widgets
- [ ] Search and filtering

### M6 — AI Commerce

- [ ] AI Product Generator
- [ ] AI SEO Writer
- [ ] AI Category Generator
- [ ] AI Price Recommendation
- [ ] Approval workflow

### Production Blocker

A user-owned domain is required for public HTTPS.
The current ipTIME DDNS hostname cannot receive a certificate because of its parent-domain CAA policy.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## Shopping Platform Service Roadmap

### M5 — AI Shopping Storefront Foundation

- [x] Featured Products API
- [x] Product Search API
- [x] Category Navigation
- [x] Price Filters
- [x] Stock Filter
- [x] Pagination
- [x] Product Image Support
- [x] Placeholder Fallback
- [x] WordPress Presentation Plugin
- [x] External Storefront
- [ ] Final Documentation and Git Closeout

### M6 — AI Product Generation

- [ ] Product Draft Model
- [ ] AI Product Generator
- [ ] AI Description Writer
- [ ] AI SEO Writer
- [ ] AI Category Suggestion
- [ ] Approval Workflow
- [ ] Controlled WooCommerce Write
- [ ] Audit Log

### M7 — Shopping Operations

- [ ] Order Read Integration
- [ ] Customer Read Integration
- [ ] Inventory Monitoring
- [ ] Shopping Dashboard
- [ ] Notifications
- [ ] n8n Automation
<!-- SHOPPING_M5_END -->

<!-- AI_SHOPPING_STOREFRONT_V016_ROADMAP -->
## Shopping Platform Baseline

Status: Completed

Completed:

- Orange Coco Storefront
- Shopping API integration
- Category, search and product APIs
- Product detail page
- Responsive homepage
- HTTP 404 contract
- Git baseline commit

Next:

- Mac mini Production Control Plane
- WordPress and WooCommerce migration
- AIControlCenter launchd runtime
- Production domain and HTTPS
- Wishlist and checkout improvements
- AI recommendation and product creation

<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:START -->
## Mac Control Plane Roadmap

            ### Completed

            - [x] Mac Foundation Gate
            - [x] Git and SSH control
            - [x] Runtime Contract
            - [x] Python 3.12 production runtime
            - [x] Full Test Suite
            - [x] Read-only Health Gate
            - [x] Shadow read-only ASGI layer
            - [x] LaunchAgent architecture evaluation
            - [x] LaunchAgent rejected for headless production
            - [x] Non-root system LaunchDaemon
            - [x] Secure plist and runner ownership
            - [x] Automatic restart validation
            - [x] Localhost-only listener validation
            - [x] Health HTTP `200`
            - [x] Write probe HTTP `405`

            ### Current Sprint

            - [ ] Headless reboot recovery
            - [ ] Verify service before GUI login
            - [ ] Verify PID change after reboot
            - [ ] Verify process user `kyouhan`
            - [x] Verify Runtime commit preservation

            ### Next Sprint

            - [ ] 24-hour Shadow observation
            - [ ] CPU and memory baseline
            - [ ] restart-count monitoring
            - [ ] log-growth monitoring
            - [ ] Ubuntu Worker JSON read-only connection
            - [x] Mac Dashboard Shadow connection
            - [ ] Cutover and rollback runbook

            - Generated: `2026-07-14T03:31:53+00:00`
- Branch: `sprint/mac-control-plane-foundation`
- Commit: `db4d93a2652a704dfa9a7e149623064adb961504`
- Runtime commit: `db4d93a2652a`
<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:END -->

<!-- AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:START -->
## Mac Control Plane Roadmap Update

            - [x] Non-root LaunchDaemon
            - [x] Automatic restart
            - [x] Headless reboot recovery
            - [x] Health HTTP 200
            - [x] Write protection HTTP 405
            - [x] Localhost-only listener
            - [ ] Reconcile manager installer with plist
            - [ ] Complete 24-hour Shadow observation
            - [ ] Validate Ubuntu Worker JSON APIs
            - [ ] Complete cutover and rollback runbooks

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
## Shadow Observation Sprint

- [x] Headless reboot recovery
- [x] Read-only observer architecture
- [x] JSON Lines observation contract
- [x] Five-minute sampling definition
- [ ] Complete 24-hour observation window
- [ ] Review CPU and RSS baseline
- [ ] Review PID transitions
- [ ] Review log growth
- [ ] Approve or reject production cutover

Configured: `2026-07-14T04:19:41+00:00`
<!-- AICONTROLCENTER:SHADOW_OBSERVATION:END -->

<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## Mac Control Plane Foundation

Status: **Complete**

- [x] Commit-specific Runtime
- [x] Non-root system LaunchDaemon
- [x] Headless reboot recovery
- [x] Read-only Shadow API
- [x] Localhost-only listener
- [x] 24-hour observation
- [x] Canonical installation manager
- [x] Transactional apply
- [x] Transactional rollback
- [x] launchd settle policy
- [x] Final apply validation
- [x] Final restart validation
- [x] Documentation closeout

### Next Program Phase

- [ ] AIControlCenter REST API consolidation
- [x] Dashboard integration
- [ ] Homepage integration
- [ ] Ubuntu Worker read-only JSON APIs
- [ ] n8n read-only workflows
- [ ] Production cutover design and approval
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->

### PI-001 Dashboard Shadow API Integration

- [x] Dashboard Control Plane JSON contract
- [x] Immutable Runtime metadata
- [x] Runtime metadata schema validation
- [x] Metadata-gated Runtime activation
- [x] `GET /health` returns HTTP `200`
- [x] `GET /dashboard` returns HTTP `200`
- [x] `POST /dashboard` returns HTTP `405`
- [x] Runtime commit matches Git HEAD

Production Runtime: `ba8d2c977257`

<!-- AICONTROLCENTER:PI-002:START -->
### PI-002 Ubuntu Worker Health JSON Adapter

Status: **Complete — Structured Monitoring Gate**

- [x] Define worker health JSON schema
- [x] Implement bounded SSH transport
- [x] Implement Ubuntu health JSON adapter
- [x] Add Production worker configuration
- [x] Add structured failure continuity
- [x] Connect `ubuntu-main` to the Production Dashboard
- [x] Validate immutable runtime deployment
- [x] Validate system LaunchDaemon operation
- [x] Validate Health and Dashboard HTTP `200`
- [x] Validate full regression suite
- [ ] Configure dedicated SSH identity for the service process
- [ ] Validate successful remote worker telemetry

Next milestone: Ubuntu Worker Healthy Telemetry.
<!-- AICONTROLCENTER:PI-002:END -->

<!-- AICONTROLCENTER:PI-003:START -->
### PI-003 Ubuntu Worker Minimum Closure

Status: **Complete**

- [x] Confirm Ubuntu is an optional worker
- [x] Confirm Docker boot activation
- [x] Confirm Immich automatic recovery
- [x] Confirm Nextcloud automatic recovery
- [x] Confirm `unless-stopped` restart policies
- [x] Power off Ubuntu after validation
- [x] Validate Mac Control Plane standalone operation
- [x] Validate Health HTTP `200`
- [x] Validate Dashboard HTTP `200`
- [x] Validate structured optional-worker failure

### PI-004 Mac Standalone Production Baseline

Status: **Next**

- [ ] Inventory Mac mini services
- [ ] Validate Mac reboot recovery
- [ ] Define service deployment manifest
- [ ] Deploy Homepage on the Mac mini
- [ ] Validate local AI runtime and provider health
- [ ] Validate automation service deployment
- [ ] Add install, update and rollback automation
<!-- AICONTROLCENTER:PI-003:END -->

<!-- AICONTROLCENTER:PI-004:START -->
### PI-004 Mac Standalone Production Baseline

Status: **Complete**

- [x] Inventory Mac services
- [x] Create Mac Production service manifest
- [x] Confirm Homepage as embedded API
- [x] Align Homepage optional-worker contract
- [x] Validate immutable runtime deployment
- [x] Validate Mac reboot recovery
- [x] Run full test suite
- [x] Generate Production evidence

### PI-005 Mac Service Deployment Platform

Status: **Next**

- [ ] Define reusable service manifest schema
- [ ] Define install, update, restart and rollback interfaces
- [ ] Deploy Ollama as a managed Mac service
- [ ] Integrate Ollama health and model inventory
- [ ] Define n8n deployment contract
- [ ] Define OpenClaw adapter boundary
<!-- AICONTROLCENTER:PI-004:END -->

<!-- AICONTROLCENTER:PI-005:START -->
## PI-005 — Complete

- [x] Service manifest schema
- [x] JSON manifest validator
- [x] Read-only deployment plan
- [x] Mac service inspector
- [x] Desired/actual deployment diff
- [x] Ollama managed-service design
- [x] Dry-run and rollback plan
- [x] Installation approval gate
- [x] Full test and Production evidence

Next: PI-006 approved Ollama native deployment.
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

Status: **Production Complete — Final Documentation Commit Pending**

Completed milestones:

- architecture and ownership boundary
- canonical default-deny registry
- read-only registry loader
- governance evaluator
- read-only governance API
- full test suite and immutable runtime deployment
- Production operational validation
- rollback-readiness validation

Deferred beyond PI-007:

- approved model onboarding
- model download or deletion workflows
- write-operation authorization
- resource enforcement
- automated remediation
- model lifecycle audit UI

Any write-capable model lifecycle feature requires a separate Product Increment
and explicit Production approval.
<!-- AICONTROLCENTER:PI-007:END -->

## PI-008 — COMPLETE

Model Governance Audit and Dashboard Integration has completed the Production gate.

Completed scope:

- audit schema and immutable snapshots
- SQLite append-only persistence
- comparison and query services
- read-only API
- Dashboard integration
- runtime provenance
- Git-independent Production runner
- Production deployment
- rollback compatibility
- documentation closure

Next production milestone:

PI-009 should focus on operational observability for governance audit history, bounded Dashboard latency, backup verification, and alerting while preserving the read-only-first policy.

Write operations remain out of scope until monitoring, audit history, backup, and operational alerting are stable.

<!-- PI-009:START -->
## PI-009 Roadmap Status

### Completed

- Domain and event contracts.
- SQLite persistence adapter.
- Application service and projections.
- GET-only API integration.
- Fail-soft Dashboard integration.
- Regression and database-safety validation.
- Repository documentation handoff.

### Pending Production Gate

- Review and approve production migration.
- Review and approve scheduler activation.
- Synchronize the PI-009 Notion handoff.
- Execute post-activation operational validation.
- Confirm rollback readiness.

PI-010 must not depend on activated PI-009 scheduling until these
production gates are complete.
<!-- PI-009:END -->

<!-- PI-009-OPERATIONS-FINAL:BEGIN -->
## PI-009 Completion and PI-010 Transition

### PI-009 — Governance Operations

- [x] Domain contracts
- [x] SQLite append-only repository
- [x] Application dispatch service
- [x] Read-only API and Dashboard projection
- [x] Production schema migration
- [x] Verified Production backup
- [x] Manual operation validation
- [x] Production UTC clock adapter
- [x] JSON-first one-shot runner
- [x] Full regression
- [x] Documentation close

### PI-010 — Controlled Scheduler Policy and Activation

- [ ] Approve explicit cadence for each operation
- [ ] Render disabled launchd definitions
- [ ] Validate temporary plist artifacts
- [ ] Obtain explicit installation approval
- [ ] Install and activate under controlled gate
- [ ] Observe the first operation executions
- [ ] Validate audit projection and logs
- [ ] Document unload and rollback procedures
<!-- PI-009-OPERATIONS-FINAL:END -->

<!-- PI-010-HEADLESS-PRODUCTION-CLOSE-2026-07-23 -->
## PI-010 — Governance Operations Scheduling

Status: CLOSED — 2026-07-23

Completed explicit cadence, JSON one-shot execution, dedicated governance runtime capabilities, headless Production scheduling, authoritative run_succeeded validation, rollback protection, regression, and documentation close.

Next milestone: Shopping Platform Foundation.

<!-- BEGIN AICONTROLCENTER SPF-002 ROADMAP -->
## Shopping Platform Foundation

Status: In Progress

| Task | Scope | Status |
| --- | --- | --- |
| SPF-001 | Repository and branch baseline | CLOSED |
| SPF-002 | Architecture and ownership foundation | CLOSED |
| SPF-003 | Package and read-only port skeleton | NEXT |
| SPF-004 | Canonical JSON Schema v1 | QUEUED |
| SPF-005 | Deny-by-default capability registry | QUEUED |
| SPF-006 | Read adapter contracts | QUEUED |
| SPF-007 | Adapter health monitoring | QUEUED |
| SPF-008 | Read-only snapshot retrieval | QUEUED |
| SPF-009 | Validation and schema drift detection | QUEUED |
| SPF-010 | Regression and operational close | QUEUED |

Write progression:
Monitoring → Validation → Reconciliation → Approval → Dry Run → Canary Write → Production Write.
<!-- END AICONTROLCENTER SPF-002 ROADMAP -->

<!-- SPF-003:START -->
## Shopping Platform Foundation Progress — 2026-07-23

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture foundation
- [x] SPF-003 Package and read-only port skeleton
- [ ] SPF-004 Canonical JSON Schema v1
- [ ] SPF-005 Capability registry deny-by-default
- [ ] SPF-006 Read adapter contracts
- [ ] SPF-007 Adapter health monitoring
- [ ] SPF-008 Read-only snapshots
- [ ] SPF-009 Validation and schema drift
- [ ] SPF-010 Regression, operational validation, and documentation closure

SPF-003 implementation commit: `fd52aad1d9af9d056d80d8f7d6170605ea0d11b2`.
<!-- SPF-003:END -->


<!-- AICONTROLCENTER-SPF-004-CLOSED -->
## Shopping Platform Foundation Progress

Completed:

- SPF-001 Repository and branch baseline
- SPF-002 Architecture foundation
- SPF-003 Package and read-only port skeleton
- SPF-004 Canonical JSON Schema v1

Next production task:

- **SPF-005 Capability Registry — deny by default**

Remaining after SPF-004:

- SPF-005 Capability Registry
- SPF-006 Read Adapter Contracts
- SPF-007 Adapter Health Monitoring
- SPF-008 Read-Only Snapshots
- SPF-009 Validation and Schema Drift
- SPF-010 Regression, Operational Validation and Documentation Closure

An internal read-only Homepage Preview is now architecturally unblocked, but it must remain fixture or controlled read-only until the required adapter and monitoring gates are complete.

<!-- SPF-005-CLOSE:BEGIN -->
## Shopping Platform Foundation Progress

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture foundation
- [x] SPF-003 Package and read-only port skeleton
- [x] SPF-004 Canonical JSON Schema v1
- [x] SPF-005 Capability Registry deny-by-default
- [ ] SPF-006 Read Adapter Contracts
- [ ] SPF-007 Adapter Health Monitoring
- [ ] SPF-008 Read-only Snapshots
- [ ] SPF-009 Validation and Schema Drift
- [ ] SPF-010 Regression, Operational Validation, and Documentation Closure

Current completion: **5/10 — 50%**.

Next production milestone: SPF-006 establishes replaceable read adapter contracts without enabling Shopping writes.
<!-- SPF-005-CLOSE:END -->

<!-- SPF-006-CLOSE:BEGIN -->
## Shopping Platform Foundation Progress

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture foundation
- [x] SPF-003 Package and read-only port skeleton
- [x] SPF-004 Canonical JSON Schema v1
- [x] SPF-005 Capability Registry deny-by-default
- [x] SPF-006 Read Adapter Contracts
- [ ] SPF-007 Adapter Health Monitoring
- [ ] SPF-008 Read-only Snapshots
- [ ] SPF-009 Validation and Schema Drift
- [ ] SPF-010 Regression, Operational Validation, and Documentation Closure

Current completion: **6/10 — 60%**.

Next production milestone: SPF-007 introduces observable adapter health and controlled live read integration without enabling Shopping writes.
<!-- SPF-006-CLOSE:END -->

<!-- SPF-007-CLOSE:BEGIN -->
## Shopping Platform Foundation Progress

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture foundation
- [x] SPF-003 Package and read-only port skeleton
- [x] SPF-004 Canonical JSON Schema v1
- [x] SPF-005 Capability Registry deny-by-default
- [x] SPF-006 Read Adapter Contracts
- [x] SPF-007 Adapter Health Monitoring
- [ ] SPF-008 Read-only Snapshots
- [ ] SPF-009 Validation and Schema Drift
- [ ] SPF-010 Regression, Operational Validation, and Documentation Closure

Current completion: **7/10 — 70%**.

Next production milestone: SPF-008 introduces controlled read-only snapshot boundaries without enabling Shopping writes or moving application state to Ubuntu.
<!-- SPF-007-CLOSE:END -->

<!-- SPF-008-CLOSE:BEGIN -->
## Shopping Platform Foundation Progress

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture foundation
- [x] SPF-003 Package and read-only port skeleton
- [x] SPF-004 Canonical JSON Schema v1
- [x] SPF-005 Capability Registry deny-by-default
- [x] SPF-006 Read Adapter Contracts
- [x] SPF-007 Adapter Health Monitoring
- [x] SPF-008 Read-only Snapshots
- [ ] SPF-009 Validation and Schema Drift
- [ ] SPF-010 Regression, Operational Validation, and Documentation Closure

Current completion: **8/10 — 80%**.

Next production milestone: SPF-009 validates canonical contracts and detects schema drift without enabling Shopping writes or moving application state to Ubuntu.
<!-- SPF-008-CLOSE:END -->

<!-- AICONTROLCENTER:SPF-009:CLOSED -->
## SPF-009 Validation and Schema Drift Closure

- [x] SPF-009 — Validation and Schema Drift.
  - Runtime validator CLOSED.
  - Drift classifier CLOSED.
  - Authorization-first read-only schema drift monitoring CLOSED.
  - Negative/isolation/full regression CLOSED at 930 passed, 5 deselected.
- [ ] SPF-010 — Regression, operational validation and documentation closure.
- Foundation progress after SPF-009: **9/10 = 90%**.

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
- Foundation roadmap milestone: COMPLETE.
- Next production milestone: post-Foundation read-only external integration and monitoring.
- Write enablement is not part of Foundation closure and requires a future explicit milestone.

<!-- BEGIN AICONTROLCENTER:SRI-03 -->
## SRI — Shopping External Read Integration

### Current sprint — SRI-03

SRI-03 implements the real external WooCommerce READ path while AIControlCenter remains the single Control Plane.

### Next milestone — Controlled Production DNS

1. Inventory a platform-controlled domain and DNS provider.
2. Select the canonical Shopping production hostname.
3. Configure or validate the A record against the current public IPv4.
4. Keep AAAA absent until IPv6 ingress is validated.
5. Validate CAA permits the selected public CA.
6. Reconfirm external HTTP ingress.
7. Validate staging TLS.
8. Perform one controlled Production TLS issuance.
9. Make Caddy reboot-safe with certificate storage continuity.
10. Connect the real WooCommerce upstream.
11. Create a dedicated WooCommerce READ-only credential.
12. Execute one canonical production GET.
13. Run Shopping and full regression suites.
14. Complete Git documentation and Notion closure.

### Following milestones

- SRI-04 — WordPress CMS real READ adapter
- SRI-05 — Health Schema Snapshot and Drift operational integration
- SRI-06 — Final regression and operational closure

After SRI closes the next program is DPL — Deployment Package.
<!-- END AICONTROLCENTER:SRI-03 -->

<!-- SRI-06B-R1:ROADMAP -->
## SRI Closure and Next Program

### Shopping External Read Integration

- SRI-01 external integration inventory: CLOSED.
- SRI-02 production read policy: CLOSED.
- SRI-03 WooCommerce production READ integration: CLOSED.
- SRI-04 WordPress CMS production READ integration: CLOSED.
- SRI-05 Health, Schema, Snapshot and Drift integration: CLOSED.
- SRI-06 regression, documentation, Git and handoff closure: final release baseline.

### Next program

DPL, Deployment Package, is the next production program.
DPL consumes the SRI architecture without moving business logic or application state to Ubuntu.
Codex performs implementation under Architect-owned specifications and acceptance gates.
<!-- END SRI-06B-R1 -->

<!-- AICONTROLCENTER:DPL-01:START -->
## DPL — Deployment Package Program

- [x] DPL-01 — Inventory, ownership, architecture decisions, blockers and
  sprint plan.
- [x] DPL-02 — Versioned package/report JSON Schemas and registry; read-only
  inventory, validation, diff, dry-run, readiness and audit.
- [ ] DPL-03 — Enforced read/plan/apply package and dependency separation.
- [ ] DPL-04 — Launchd-native Mac inventory and health inspection.
- [ ] DPL-05 — Canonical Host Caddy, Colima, Compose and Commerce ingress
  validation.
- [ ] DPL-06 — Typed Ubuntu read-only action contract and deny-by-default
  policy; activation separately gated.
- [ ] DPL-07 — Immutable evidence, compatibility and release-candidate
  validation.
- [ ] DPL-08 — Regression, operational documentation and production
  authorization review.

### Production milestones

1. Read-only contract milestone: DPL-02 schemas and reports accepted.
2. Architecture boundary milestone: DPL-03 dependency rules enforced.
3. Mac readiness milestone: DPL-04 and DPL-05 pass without mutation.
4. Optional worker contract milestone: DPL-06 typed allowlist accepted.
5. Release candidate milestone: DPL-07 evidence and compatibility pass.
6. Authorization milestone: DPL-08 review completes.

No milestone itself authorizes production activation. Apply and production
writes require a separate explicit authorization.
<!-- AICONTROLCENTER:DPL-01:END -->

## DPL-04 Closure and Next Milestone

DPL-04A through DPL-04D are CLOSED and DPL-04 is CLOSED.
M2 is `READINESS_ACCEPTED`; activation is `ACTIVATION_NOT_STARTED`.
M2-P1 is CLOSED and pilot authorization policy is AVAILABLE. The next milestone
is M2-P2 Controlled Sandbox Pilot Activation and Evidence. Persistent SQLite
audit implementation is required before any broader mutable deployment.
Production activation remains `NOT_AUTHORIZED`.

## M3 Permit Replay

- [x] M3-A2A — Read-only permit/replay foundation.
- [x] M3-A2B — Durable reservation, consumption and failed-closed writer.
- [x] M3-A2C — Replay-state backup, recovery and concurrency validation.

M3-A2C validation used pytest temporary databases only and proved
post-recovery concurrency. Operational replay DB, backup schedule, restore and
writer activation remain absent; raw nonce writes remain zero. Production
activation is `NOT_AUTHORIZED`.

- [x] M3-A3A — Read-only operational monitoring foundation.
- [x] M3-A3B — Alert routing and deduplication.
- [x] M3-A3C — Monitoring and Alert Operational Drill.

M3-A3A, M3-A3B and M3-A3C are closed, and the M3-A3 Monitoring and Alert Track
is closed. The end-to-end monitoring drill and simulated logical delivery are
validated. M3-A3B provides deterministic logical routing, deduplication, reminders,
recurrence and severity escalation. External dispatch and alert-routing
persistence are not implemented; operational monitoring, databases and writers
remain inactive. Production activation is `NOT_AUTHORIZED`. Next: M3-A4
Controlled Operational Activation Gate.

- [x] M3-A4A — Read-Only Operational Activation Readiness Gate.
- [ ] M3-A4B — Controlled Mac Operational Bootstrap.

M3-A4A is closed. The activation readiness gate and controlled bootstrap plan
are available without authorization or execution. Operational databases are
not created; writers and monitoring are not activated; external dispatch is
not implemented; bootstrap authorization is not granted; Production activation
is `NOT_AUTHORIZED`.
# Current milestone

- M3-A4B2B1A — CLOSED
- M3-A4B2B1B — CLOSED after validation
- Human approval gate — AVAILABLE
- Synthetic dual-identity approval and in-memory permit issuance — VALIDATED
- Current recommended review — DENIED; independent approver `UNASSIGNED`
- Operational permit/claim/bootstrap execution — zero
- Production activation — `NOT_AUTHORIZED`
- Next: M3-A4B2B1C Independent Approver Action and Live Permit Issuance
# M3-A4B2B2A closure

- CLOSED: authorized Mac bootstrap execution capability and atomic test claim.
- NOT EXECUTED: controlled operational bootstrap.
- NEXT: M3-A4B2B2B Fresh Permit and Authorized Mac Bootstrap Execution.
# Next deployment task

M3-A4B2B2B Fresh Approval and Authorized Mac Bootstrap. Production activation
remains `NOT_AUTHORIZED`.
# R5 closure

M3-A4B2B2B-R5 adds the deterministic warning acknowledgement projection and
pre-issuance compatibility gate. Next is fresh approval and separately
authorized current-user Mac bootstrap; M3-A4B3 remains blocked until success.

# M3-A4B3 closure

- CLOSED: complete bootstrap evidence chain and exact commit binding.
- CLOSED: audit/replay `HEALTHY`, zero events, two isolated baseline restores.
- CLOSED: source immutability and negative recovery validation.
- PERMANENTLY CONSUMED: the successful one-use permit.
- INACTIVE: writers, monitoring, dispatch, and Ubuntu.
- `NOT_AUTHORIZED`: production.
- NEXT: `M3-A4C_ACTIVATION_VALIDATION_AND_CLOSEOUT`.

# M3-A4C — CLOSED

- Decision: `READY_FOR_SEPARATELY_AUTHORIZED_CONTROLLED_ACTIVATION`.
- No writer, monitoring, dispatch, Ubuntu, or production activation.
- Next: `M4_CONTROLLED_ACTIVATION_ARCHITECTURE` with a separate gate.
- Separate backlog: the existing 427 deprecation warnings.

# M4-A1 — CLOSED

- COMPLETE: typed registry for five default-inactive, unauthorized capabilities.
- COMPLETE: deterministic immutable state transitions and architecture planner.
- COMPLETE: independent capability gates and explicit dependency policy.
- PROHIBITED: implicit escalation, Ubuntu ownership/delegation, and production.
- NO CHANGE: writers, monitoring runtime, dispatch, and external notification
  remain inactive; no operational authorization exists.
- Decision: `READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS`.
- Next: `M4-A2_CAPABILITY_AUTHORIZATION_CONTRACTS`.

# M4-A2 — CLOSED

- COMPLETE: immutable typed scope, request, approval, restriction, evidence,
  validation, grant-plan, plan, and decision contracts.
- COMPLETE: deterministic canonical JSON and SHA-256 digest/tamper binding.
- COMPLETE: independent identity policy and injected-clock, timezone-aware,
  maximum-one-hour single-use window validation.
- COMPLETE: capability-specific restrictions and separate dependency
  references without implicit authorization.
- NO CHANGE: no authorization, permit, claim, writer, monitoring, dispatch,
  Ubuntu, command, API write route, or production activation.
- Decision: `READY_FOR_TEST_ONLY_AUTHORIZATION_SIMULATION`.
- Production: `NOT_AUTHORIZED`.
- `.env`: not required.
- Next: `M4-A3_TEST_ONLY_AUTHORIZATION_SIMULATION`.
- Separate backlog: 427 existing deprecation warnings.
- Separate backlog: 427 existing deprecation warnings.

# M4-A1R1 — CLOSED

- BASELINE: M4-A1 commit `b719aa445af864c907ac5d384c2c8347d2d6688a`.
- COMPLETE: immutable retained SQLite source and disposable inspection/recovery
  working-copy contract.
- COMPLETE: WAL/SHM side effects confined to working copies; retained bytes,
  modes, sizes, mtimes, and digests unchanged.
- NO CHANGE: actual operational state, cryptographic/evidence semantics,
  writers, monitoring, dispatch, Ubuntu, commands, API routes, and production.
- `.env`: not required.
- Decision: `READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS`.
- Production: `NOT_AUTHORIZED`.
- Next: `M4-A2_CAPABILITY_AUTHORIZATION_CONTRACTS`.
# AUTO autonomous delivery roadmap

- [x] AUTO-01: immutable contracts, lifecycle, manifests, deterministic DAG,
  approval/retry/evidence policy, schemas and bounded executor port.
- [ ] AUTO-02: separately gated persistent Codex runner, terminal independence
  and recovery architecture.

AUTO-01 is architecture-only. Human approval remains mandatory for L4/L5 and
post-claim recovery. Persistent state and launchd are future work. Production
is `NOT_AUTHORIZED`.

<!-- SHOPPING-FIRST-REPRIORITIZATION:BEGIN -->
## Reprioritized Delivery Sequence

### Closed

- AUTO-01 — Autonomous Delivery Controller Architecture

### Deferred

- AUTO-02 — Persistent Codex Runner and Recovery
- AUTO-03 — M4 Master Manifest and Approval Gates
- M4-A4 — Read-Only Operational Observation
- M4-A5 — Separately Authorized Controlled Pilot
- M4-A6 — Evidence, Recovery and M4 Closeout

### Active Product Track

1. SHOP-00 — Shopping Platform Architecture Reprioritization
2. SHOP-01 — WooCommerce Read Adapter
3. SHOP-02 — Normalized Product Domain
4. SHOP-03 — Product Management API and Dashboard
5. Shopping draft, approval and controlled-write vertical slice
6. AI Integration Platform
7. Personal AI Assistant

The 427 existing deprecation warnings remain a separate remediation
backlog.
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


Product delivery sequence:

1. SHOP-01 — Product Management Read Model and Dashboard
2. SHOP-02 — Product Draft Workflow
3. SHOP-03 — Human Approval Workflow
4. SHOP-04 — Controlled WooCommerce Write
5. SHOP-05 — Order and Customer Read Integration
6. SHOP-06 — Shopping MVP Validation and Release
7. AI-01 — Shopping AI Integration

SHOP-01 must extend the existing Dashboard and Shopping APIs rather
than introduce a new frontend framework.
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

<!-- SHOP-01C-DASHBOARD-INTEGRATION:BEGIN -->
## SHOP-01C Dashboard JSON Integration

The existing `GET /dashboard` projection now includes an optional
`shopping_management` section.

The section is generated through the completed Shopping management
read model and remains read-only.

Failure isolation rules:

- Shopping configuration failure does not fail the Dashboard.
- Shopping catalog failure does not fail the Dashboard.
- Internal exception details are never exposed.
- An unavailable Shopping dependency returns a deterministic
  `UNAVAILABLE` envelope.
- Existing Dashboard behavior is preserved when no Shopping
  projection is injected.

The Dashboard imports no WooCommerce adapter and creates no local
product truth.

The next task is `SHOP-01D_VALIDATION_AND_CLOSEOUT`.
<!-- SHOP-01C-DASHBOARD-INTEGRATION:END -->

<!-- SHOP-01D-CLOSEOUT:BEGIN -->
## SHOP-01 Product Management Read Model and Dashboard

SHOP-01 is closed.

Completed capabilities:

- deterministic Shopping management read model
- product and inventory summary
- normalized operator-facing product list
- health, readiness, capability and integration projection
- optional `shopping_management` Dashboard dependency
- `GET /dashboard.shopping_management` JSON projection
- deterministic `UNAVAILABLE` failure envelope
- internal error-detail suppression
- source and result mutation isolation
- existing Dashboard compatibility
- default-configuration read-only operational observation

Architecture boundaries remain unchanged:

- WooCommerce remains the Commerce Engine.
- WordPress remains the CMS.
- AIControlCenter owns management projections and workflow logic.
- The Dashboard does not import WooCommerce adapters.
- No local product truth was created.
- No Shopping mutation route was added.
- Production writes remain `NOT_AUTHORIZED`.

The next active task is:

`SHOP-02A_PRODUCT_DRAFT_WORKFLOW_ARCHITECTURE`
<!-- SHOP-01D-CLOSEOUT:END -->

<!-- SHOP-01E2-COMPATIBILITY-ADAPTER:BEGIN -->
## SHOP-01E2 Shopping Product Compatibility Adapter

The default Mock catalog returned the legacy `Product` contract while
the management read model required the canonical product projection.

A dedicated application adapter now translates the existing
`ShoppingService` result into the canonical management contract.

Explicit mappings:

- `id` to `product_id`
- `image_url` to `image_urls`
- `Decimal` price to a JSON number

Missing SKU, inventory quantity, URL and updated timestamp values
remain null. The adapter does not synthesize unknown Commerce data.

The canonical management contract was not weakened. The Dashboard
continues to have no direct WooCommerce dependency.

The next task is:

`SHOP-01E3_WOOCOMMERCE_READ_ONLY_CONFIGURATION`
<!-- SHOP-01E2-COMPATIBILITY-ADAPTER:END -->

<!-- SHOP-01E3C-SECURE-RUNTIME:BEGIN -->
## SHOP-01E3C Secure WooCommerce Read Runtime

AIControlCenter now provides a reusable secure runtime loader for the
existing WooCommerce read-only credential file.

The loader validates:

- a regular non-symlink credential file
- current-user ownership
- file mode `0600`
- direct parent mode `0700`
- exact credential keys
- read-only WooCommerce API permission

Credential values are not copied into Git, LaunchAgent plist files or
the process environment.

Runtime selection uses the non-secret profile:

`AICONTROLCENTER_SHOPPING_PROFILE=woocommerce_read_only`

The profile is not enabled persistently by this task. Persistent
LaunchAgent activation requires a separate operational authorization.

The canonical WooCommerce target currently has zero products and one
product category. This is a valid empty Commerce Engine state, not an
adapter failure.

The next active task is:

`SHOP-02A_PRODUCT_DRAFT_WORKFLOW_ARCHITECTURE`
<!-- SHOP-01E3C-SECURE-RUNTIME:END -->

## Product Draft Sequence

- SHOP-01E read foundation — CLOSED.
- SHOP-01E3D persistent activation — DEFERRED.
- SHOP-02A Product Draft workflow architecture — COMPLETE.
- SHOP-02B Product Draft domain implementation — COMPLETE; contract 1.0.0 with a non-production in-memory adapter and no external writes.
- SHOP-02C Product Draft validation and human approval application service — COMPLETE; deny-by-default, HUMAN-only, exact-revision-bound, and in-memory only.
- SHOP-02D Product Draft read API and Dashboard projection — NEXT; production writes remain `NOT_AUTHORIZED`.

The zero-product, one-category WooCommerce observation does not block this sequence.
# Shopping sequence update

SHOP-02D is complete: GET-only ProductDraft reads and the `product_draft_review` Dashboard projection use a replaceable read source with explicit empty-versus-unavailable semantics. No mutation route, WooCommerce write, or persistent ProductDraft store exists. Production writes remain `NOT_AUTHORIZED`. Next: SHOP-03 controlled WooCommerce write architecture.

SHOP-03A is complete: immutable approved-revision eligibility, exact authorization, controlled-plan idempotency, deterministic preview, and an isolated fake/dry-run adapter are implemented. ProductDraft contracts remain 1.0.0; real WooCommerce writes are `NOT_IMPLEMENTED`, production writes are `NOT_AUTHORIZED`, and SHOP-03B requires separate authorization.
# Shopping controlled deployment roadmap

- SHOP-03B1: controlled live adapter contract and credential boundary — complete in intercepted validation mode; external requests 0, live writes 0.
- SHOP-03B2: one-product controlled pilot — next, contingent on separate exact product, revision, intent, and execution-time authorization.
## Shopping operator UI

- **UI-01 complete:** internal read-only `GET /homepage`, backed only by
  same-origin `GET /dashboard`.
- **UI-02 complete:** internal read-only Product Management Console at
  `GET /homepage/product-management`.
- **OPS-01 next:** staging Caddy, authentication, and monitoring; UI-02 adds no
  public opening or authentication change.

## PI-009A2 — Immutable Runtime Source Isolation

Priority: Production blocker

Goal:

Remove AIControlCenter runtime dependence on the mutable Git working tree.

Target architecture:

`runtime/venvs/<runtime-id>`
provides the immutable Python dependency environment.

`runtime/sources/<runtime-id>`
provides the immutable application-source snapshot.

The runtime wrapper must derive both artifacts from the same approved runtime
identity and must not use the repository root as the application PYTHONPATH.

Production authorization remains blocked until source isolation is validated.

## PI-009A2 Execution Plan

1. A2.1 — implement and test immutable source builder/validator and repository
   wrapper template
2. A2.2 — explicitly authorize and create one immutable source artifact
3. validate source artifact read-only
4. A2.3 — explicitly authorize wrapper cutover and one service kickstart
5. prove loaded application source is inside the immutable Runtime artifact
6. rerun PI-009 Technical Production Authorization Review

Production remains blocked until
`RUNTIME_SOURCE_ISOLATION_VERIFIED`.

### PI-009A2 New Candidate Requirement

The former Candidate cannot complete source isolation because its application
state defaults are repository-relative.

Execution plan:

1. commit state-isolation repair
2. complete immutable source artifact tooling on the repaired source
3. build a new Runtime Candidate from the repaired commit
4. validate new Candidate plus immutable source artifact
5. authorize operational source artifact creation
6. authorize wrapper cutover
7. rerun PI-009 Production Authorization Review

### PI-009A2 A2.1 Complete

The next Runtime Candidate will use the A2.1 completion commit as its immutable
source identity because the canonical bootstrap build contract is HEAD-only.

Next steps:

1. authorize one new Runtime Candidate build
2. build Candidate with canonical bootstrap
3. validate Candidate metadata and full test gate
4. create matching immutable source artifact under separate authorization
5. validate source/state identity
6. authorize immutable-source wrapper cutover
7. rerun PI-009 Production Authorization Review

### PI-009A2 A2.2A Complete

New Runtime Candidate `7b171f135dc7` is validated.

Next:

1. human-authorized operational immutable source artifact creation
2. operational source artifact validation
3. human-authorized immutable wrapper cutover
4. one launchd kickstart
5. final PI-009 Production Authorization Review

### PI-009A2 A2.2B Complete

Runtime `7b171f135dc7` and its immutable source artifact are operationally
validated as a matched pair.

Next:

1. freeze A2.3 live-cutover evidence
2. human-authorized Runtime pointer switch
3. install immutable-source live wrapper
4. exactly one launchd kickstart
5. validate immutable live execution
6. run final PI-009 Production Authorization Review

### PI-009A2 A2.3 Complete

Remaining Production path:

1. final deployment regression gate
2. final operational validation
3. PI-009 human Production authorization

### PI-009 Production Authorization Complete

The immutable AIControlCenter Runtime has passed the final technical gate and
received explicit human Production authorization.

Milestone:

`PI_009_PRODUCTION_AUTHORIZED`

Next platform milestone:

`AI-PROVIDER-01 — Secure Provider Integration`

### AI-PROVIDER-01B Complete

Authenticated OpenAI connectivity validated.

Next:

AI-PROVIDER-01C — Production Workflow Integration and Candidate Runtime Promotion

### AI-PROVIDER-01C-B Complete

Candidate Runtime and immutable source `102b8f1fa862` are validated without
Production activation. The network-free canonical workflow passed with the
fake provider and zero provider calls.

Next gated milestone:

AI-PROVIDER-01C-C — separately authorized Production promotion
