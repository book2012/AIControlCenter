# TODO

## AI-PROVIDER

- [x] AI-PROVIDER-01A provider contract, strict router, safe normalized errors,
  fake adapter and no-network OpenAI adapter boundary.
- [ ] AI-PROVIDER-01B secure credential installation and authenticated
  connectivity (requires separate authorization).
- [ ] Notion synchronization (`PENDING`).

Never store provider API keys in Git. Production Runtime `7b171f135dc7` and
PI-009 authorization were not changed by 01A.

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

Next:

- [ ] Execute one controlled read-only inspection
- [ ] Capture canonical JSON evidence
- [ ] Review `BLOCKED` reasons
- [ ] Complete operational validation
- [ ] Synchronize Notion
- [ ] Keep Production `NOT_AUTHORIZED`
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

Next:

- [ ] Add versioned inspection policy data
- [ ] Add versioned localhost route manifest
- [ ] Implement JSON runner
- [ ] Integrate adapters with pure evaluator
- [ ] Add deterministic exit-code mapping
- [ ] Add read-only CLI integration tests
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

Next:

- [ ] Repository observation adapter
- [ ] Runtime metadata adapter
- [ ] `launchctl print` adapter
- [ ] `lsof -F` listener adapter
- [ ] Exact localhost HTTP adapter
<!-- AICONTROLCENTER:ACTIVATION_01B_C2:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_C1_CLOSEOUT:START -->
## ACTIVATION-01B-C1 Closeout

Status: `COMPLETE`

Completed:

- [x] Register three inspection contracts
- [x] Register three Schema resources
- [x] Validate synthetic fixtures
- [x] Validate canonical digest bindings
- [x] Pass focused contract gate
- [x] Pass safe deployment regression

Backlog:

- [ ] Stabilize isolated operational test roots
- [ ] Resolve Starlette/httpx deprecation
- [ ] Replace deprecated naive `datetime.utcnow()`
- [ ] Implement C2 immutable observation models
- [ ] Implement C2 pure fail-closed evaluator

Production remains `NOT_AUTHORIZED`.
<!-- AICONTROLCENTER:ACTIVATION_01B_C1_CLOSEOUT:END -->

<!-- AICONTROLCENTER:ACTIVATION_01A:START -->
ACTIVATION-01A is `COMPLETE` at contract documentation commit `d14058553baa1dfc45e027a59ff580013584913b`.

## ACTIVATION-01B — Read-Only Activation Inspector

Status: `ARCHITECTURE_FROZEN`

- [x] Freeze architecture and macOS runbook
- [x] Reuse canonical JSON and Schema registry
- [x] Freeze exact launchd command allowlist
- [x] Freeze isolated Runtime Python probe
- [x] Freeze zero-body `POST /health` denial probe
- [ ] Implement policy, route and report schemas
- [ ] Register schemas and valid fixtures
- [ ] Implement immutable models and ports
- [ ] Implement pure deterministic evaluation service
- [ ] Implement bounded macOS read-only adapters
- [ ] Implement canonical JSON CLI
- [ ] Add no-mutation and fail-closed tests
- [ ] Perform separately reviewed read-only host inspection
- [ ] Keep Production `NOT_AUTHORIZED`
<!-- AICONTROLCENTER:ACTIVATION_01A:END -->

## RUNTIME-BUILD-04A controlled gates

- [x] Build and validate release `acd80ab9f6ae` from
  `acd80ab9f6aeb848900e1a19e3fa3afd69face8a` without activation or a
  `runtime/current` change.
- [x] Pass dependency installation, application import, Full Suite, source
  marker, and metadata validation.
- [x] Complete direct localhost `core.api.shadow:app` smoke: six required GET
  routes returned 200 and `POST /health` returned 405.
- [x] Complete exact smoke PID cleanup and listener cleanup.
- [x] Recover and validate the structured build report from the builder log.
- [ ] Commit this documentation reconciliation.
- [ ] Non-force push and verify the remote SHA and repository synchronization.
- [ ] Hand off in a new chat before the activation risk boundary.
- [x] Design ACTIVATION-01A activation/rollback architecture and runbook only.
- [ ] Run a read-only activation preflight.
- [ ] Perform a separately authorized atomic `runtime/current` switch.
- [ ] Perform a separately authorized exact service restart.
- [ ] Run post-activation validation and rollback validation.
- [ ] Bundle application source inside the release, add a source manifest, and
  support source-independent launch.
- [ ] Configure and validate authenticated Caddy staging.

Active Runtime remains `b9ad351a7241`; release `acd80ab9f6ae` was built and
validated but not activated. Python and dependencies are release-owned, while
application source remains repository-bound through `PYTHONPATH`
(`source_bundled_inside_release=false`, `repository_source_binding=true`).
Runtime activation, rollback execution, service restart, public staging,
production, and production writes remain `NOT_AUTHORIZED`. No service,
launchd, Caddy, Ubuntu, public, or production change occurred.

## RUNTIME-BUILD-02 release gates

- [x] `TEST-INFRA-02` trusted evidence binding, deterministic canonical
  evidence generation, and local verification
  (`95f2f9d7b302428889d28e377fece3deb33eaf8e`).
- [x] `FIX-GIT-01` read-only loose-ref/packed-ref identity correction and local
  verification (`2bf553a733c3cb4c1d1b147f598fc7b696bd0318`).
- [x] Immutable Runtime source marker implementation and local verification
  (`52f896f085186dc7fef65106942980d2cdaaf8ef`).
- [x] Implement phased BUILD/VALIDATE and ACTIVATE modes
  (`5517fdb25a68c65f1bc8db03110900aa44ff173f`).
- [x] Require an explicit mode and fail closed for missing or invalid modes.
- [x] Build through owned staging and atomically finalize immutable releases
  without patching existing releases or changing `runtime/current`.
- [x] Restore the canonical builder Git mode to `100755`
  (`f8f2890178c78862cff53362fd167982fa672c99`).
- [x] Add deterministic executable-mode regression coverage.
- [x] Complete local main and standalone targeted and Full Suite verification;
  current baseline: 2271 passed, 5 deselected.
- [ ] Commit this documentation reconciliation; it remains open until the
  documentation change is committed.
- [ ] Non-force push the two Runtime builder commits and documentation commit,
  then verify the remote SHA and repository synchronization.
- [ ] Execute a real `--mode build` under separate authorization.
- [ ] Validate the new release source marker, metadata, Runtime Python, and
  application import.
- [ ] Capture evidence that `runtime/current` remains invariant during the real
  build.
- [ ] Run direct localhost HTTP GET smoke for `/homepage` and
  `/homepage/product-management` after the immutable Runtime build gate.
- [ ] Perform explicit activation and rollback only under separate
  authorization.
- [ ] Keep service restart behind its separate authorization gate.
- [ ] Configure and validate Caddy authentication and read-only staging before
  any separately authorized public opening.
- [ ] Obtain explicit production authorization. Until then, production and
  production writes remain `NOT_AUTHORIZED`.

- [x] OPS-01B-R5-R3A generate and validate the immutable runtime source commit
  marker atomically with `metadata.json`.
- [ ] OPS-01B-R5-R3 build a new immutable runtime from committed Git source
  under separate authorization; do not repair an existing release in place.

- [x] Close M4-A3 deterministic test-only authorization simulation.
- [x] Prove simulation artifacts fail closed at live boundaries.
- [ ] Implement `M4-A4_READ_ONLY_OPERATIONAL_OBSERVATION` under a separate gate.

M4-A3 created no real authorization, operational permit, claim, writer,
monitoring, dispatch, notification, Ubuntu action, command, API write route, or
activation. Production remains `NOT_AUTHORIZED`; `.env` is not required and
the 427 warnings remain backlog.

- [x] Close R4 strict-live preflight and typed permit contract compatibility.
- [ ] Obtain fresh independent approval bound to the R4 commit.
- [ ] Execute the Mac bootstrap only under separate explicit authorization.
- [ ] Begin M3-A4B3 only after actual bootstrap succeeds.

- [x] Close Recovery-2 with isolated read-only Git evidence, independent public
  inspector and PRE_ACTIVATION assertions, and preserved failure evidence.

- [ ] M3-A4B2B2B Fresh Approval and Authorized Mac Bootstrap: obtain fresh
  independent approval bound to the R3 commit.
- [x] Recover the blocked R3 attempt with reviewed default live composition
  and pytest-only end-to-end controlled orchestration.

## M3-A4B2B2B recovery

- [x] Support an existing safe shared Mac application-state parent.
- [x] Preserve unrelated siblings and parent metadata.
- [ ] Obtain fresh approval and permit bound to the new commit.
- [ ] Execute separately authorized controlled Mac bootstrap.

Production activation remains `NOT_AUTHORIZED`.

## Next

- [ ] M3-A4B2B1B Operator Approval and Operational Permit Issuance

M3-A4B2B1A is CLOSED after validation. Operator/approver identities and
restriction acknowledgements remain NOT PROVIDED; permit and bootstrap remain
NOT ISSUED, NOT CLAIMED, NOT AUTHORIZED and NOT EXECUTED.

## Deployment Package Lifecycle

- [x] DPL-04B Mac-only sandbox adapter
- [x] DPL-04C durable audit architecture decision
- [x] DPL-04D M2 operational readiness
- [x] M2-P1 controlled non-production sandbox pilot authorization
- [x] M2-P2 controlled sandbox pilot activation and evidence
- [x] M2-P3 pilot evidence and rollback validation
- [x] M3-A1A SQLite read-only integrity foundation
- [x] M3-A1B Append-Only SQLite Audit Writer
- [x] M3-A1C Backup, Restore and Recovery Validation
- [x] M3-A2A Durable Permit and Replay State Read-Only Foundation
- [x] M3-A2B Durable Permit Reservation and Consumption
- [x] M3-A2C Replay-State Backup, Recovery and Concurrency Validation
- [x] M3-A3A Read-Only Operational Monitoring Foundation
- [x] M3-A3B Alert Routing and Deduplication
- [x] M3-A3C Monitoring and Alert Operational Drill
- [x] M3-A4A Read-Only Operational Activation Readiness Gate
- [x] M3-A4B1 Controlled Bootstrap Authorization Package
- [x] M3-A4B2A Controlled Mac Bootstrap Executor Validation
- [x] M3-A4B2B0 Read-Only Mac Operational Bootstrap Host Preflight
- [ ] M3-A4B2B1 Operational Permit Issuance

M3-A4A, M3-A4B1, M3-A4B2A and M3-A4B2B0 are closed. Read-only host preflight
is available. No operational permit was issued; authorization was not granted;
bootstrap was not executed; operational directories and databases were not
created; Production activation is `NOT_AUTHORIZED`.

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

<!-- AICONTROLCENTER:PI-003:START -->
## PI-003 Closure and PI-004 Priorities

### PI-003 Completed

- [x] Ubuntu boot recovery validation
- [x] Immich automatic activation
- [x] Nextcloud automatic activation
- [x] Mac standalone health validation
- [x] Optional worker failure continuity

### PI-004 P0

- [ ] Inventory all Mac mini services and ports
- [ ] Validate AIControlCenter after Mac reboot
- [ ] Deploy and validate Mac Homepage
- [ ] Validate Ollama and AI provider health
- [ ] Validate n8n deployment status
- [ ] Define service manifest and ownership
- [ ] Automate install, update, restart and rollback

### Ubuntu Backlog

- [ ] BACKLOG-U01 Dedicated SSH identity
- [ ] BACKLOG-U02 Healthy Ubuntu telemetry
- [ ] BACKLOG-U03 Detailed storage monitoring
- [ ] BACKLOG-U04 Backup verification
- [ ] BACKLOG-U05 Worker lifecycle automation
<!-- AICONTROLCENTER:PI-003:END -->

<!-- AICONTROLCENTER:PI-004:START -->
## PI-004 Closure and PI-005 Priorities

### PI-004 Completed

- [x] Mac service inventory
- [x] Mac standalone service manifest
- [x] Homepage Production contract alignment
- [x] LaunchDaemon reboot recovery
- [x] Production Gate and evidence

### PI-005 P0

- [ ] Service manifest schema validation
- [ ] Reusable deployment command interface
- [ ] Ollama native macOS supervisor contract
- [ ] Ollama health and model inventory API
- [ ] Deployment rollback validation
<!-- AICONTROLCENTER:PI-004:END -->

<!-- AICONTROLCENTER:PI-005:START -->
## PI-005

- [x] Close Mac Service Deployment Platform baseline.
- [x] Keep all deployment execution disabled.
- [x] Preserve Ollama as a replaceable Mac-only runtime.

## Next Priority

- [ ] PI-006: approved Ollama installation and system LaunchDaemon deployment.
- [ ] Add Ollama health and model inventory adapter to AIControlCenter.
<!-- AICONTROLCENTER:PI-005:END -->

<!-- PI-009:START -->
## PI-009 Remaining Operational Tasks

- [x] Implement governance operations domain.
- [x] Implement append-only SQLite adapter.
- [x] Implement application projection service.
- [x] Implement GET-only operations API.
- [x] Implement fail-soft Dashboard panel.
- [x] Complete targeted and full regression.
- [x] Verify production database content hash is unchanged.
- [x] Prepare Production Activation Gate.
- [x] Prepare Notion handoff document.
- [ ] Synchronize handoff into Notion.
- [ ] Obtain explicit production migration approval.
- [ ] Obtain explicit scheduler activation approval.
- [ ] Perform post-activation operational validation.
- [ ] Confirm rollback procedure and observation window.
<!-- PI-009:END -->

<!-- PI-009-OPERATIONS-FINAL:BEGIN -->
## PI-009 Close Checklist

- [x] Production operation schema migrated
- [x] Production database backup verified
- [x] Manual operation validated
- [x] Production UTC clock implemented
- [x] JSON-first runner implemented
- [x] Per-operation lock implemented
- [x] Automatic retry disabled
- [x] Automatic catch-up disabled
- [x] Automatic remediation disabled
- [x] Automatic restore disabled
- [x] Full regression passed
- [x] Git implementation state clean
- [x] Documentation updated

## PI-010 Next Operational Work

- [ ] Define explicit operation cadence
- [ ] Review disabled launchd definitions
- [ ] Approve scheduler installation
- [ ] Activate under controlled gate
- [ ] Observe initial scheduled executions
- [ ] Verify unload and rollback procedure
<!-- PI-009-OPERATIONS-FINAL:END -->

<!-- PI-010-HEADLESS-PRODUCTION-CLOSE-2026-07-23 -->
## PI-010 Completion

- [x] Explicit governance cadence
- [x] JSON one-shot runner
- [x] Headless Production scheduler
- [x] Dedicated governance audit snapshot capability
- [x] Dedicated SQLite online backup verifier
- [x] Production run_succeeded validation
- [x] Append-only audit correlation
- [x] Database and crontab rollback backups
- [x] Uninstall and reinstall rollback validation
- [x] MappingProxy-safe serialization
- [x] Full regression
- [x] Canonical documentation close

## Next

- [ ] Start Shopping Platform Foundation
- [ ] Define WordPress and WooCommerce read-only adapters
- [ ] Define AIControlCenter shopping domain boundaries

<!-- BEGIN AICONTROLCENTER SPF-002 TODO -->
## Shopping Platform Foundation Sprint 1

Completed:

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture Foundation

Next:

- [ ] SPF-003 Shopping package and read-only port skeleton

Queued:

- [ ] SPF-004 Canonical JSON Schema v1
- [ ] SPF-005 Deny-by-default capability registry
- [ ] SPF-006 Read adapter contracts
- [ ] SPF-007 Adapter health monitoring
- [ ] SPF-008 Read-only snapshot retrieval
- [ ] SPF-009 Validation and schema drift detection
- [ ] SPF-010 Regression and operational close

Sprint tasks completed: 2 of 10
Sprint tasks remaining: 8
Shopping write operations enabled: No
<!-- END AICONTROLCENTER SPF-002 TODO -->

<!-- SPF-003:START -->
## Current Shopping Task State

- [x] SPF-003 — Import-safe package and read-only port foundation
- [ ] SPF-004 — Canonical JSON Schema v1

SPF-003 validation: 6 targeted tests and 747 full regression tests passed.

Implementation commit: `fd52aad1d9af9d056d80d8f7d6170605ea0d11b2`.
<!-- SPF-003:END -->


<!-- AICONTROLCENTER-SPF-004-CLOSED -->
## Shopping Platform Foundation Task State

- [x] SPF-004 Canonical JSON Schema v1
- [ ] SPF-005 Capability Registry — deny by default

SPF-004 closure validation:

- [x] 15 canonical contracts registered
- [x] local-only registry loading
- [x] fail-closed validation
- [x] targeted suite: 6 passed
- [x] full regression: 753 passed
- [x] production unchanged
- [x] writes disabled

<!-- SPF-005-CLOSE:BEGIN -->
## Shopping Platform Foundation

- [x] Close SPF-005 Capability Registry deny-by-default.
- [x] Verify 11 READ capabilities and 9 reserved WRITE capability identifiers.
- [x] Verify fail-closed unknown, write, mismatch, malformed decision, and policy exception behavior.
- [x] Pass 22 targeted tests and 775 full regression tests.
- [ ] Implement SPF-006 Read Adapter Contracts.
- [ ] Keep all Shopping write operations disabled.
- [ ] Preserve Ubuntu as a stateless infrastructure worker.
<!-- SPF-005-CLOSE:END -->

<!-- SPF-006-CLOSE:BEGIN -->
## Shopping Platform Foundation

- [x] Close SPF-006 Read Adapter Contracts.
- [x] Preserve CommerceReadPort and CmsReadPort as authoritative interfaces.
- [x] Verify Commerce/CMS capability isolation.
- [x] Verify vendor-neutral import and dependency boundaries.
- [x] Pass 28 targeted tests.
- [x] Pass 803 full regression tests.
- [ ] Implement SPF-007 Adapter Health Monitoring.
- [ ] Keep Shopping WRITE operations disabled.
- [ ] Keep Ubuntu stateless and free of Shopping business logic.
<!-- SPF-006-CLOSE:END -->

<!-- SPF-007-CLOSE:BEGIN -->
## Shopping Platform Foundation

- [x] Close SPF-007 Adapter Health Monitoring.
- [x] Establish vendor-neutral health states and failure taxonomy.
- [x] Enforce fail-closed timeout and dependency behavior.
- [x] Reject raw vendor error metadata.
- [x] Implement deterministic stateless health aggregation.
- [x] Pass 34 targeted health tests.
- [x] Pass 837 full regression tests.
- [ ] Implement SPF-008 Read-only Snapshots.
- [ ] Keep Shopping WRITE operations disabled.
- [ ] Keep Ubuntu stateless and free of Shopping business logic.
<!-- SPF-007-CLOSE:END -->

<!-- SPF-008-CLOSE:BEGIN -->
## Shopping Platform Foundation

- [x] Close SPF-008 Read-only Snapshots.
- [x] Implement deterministic canonical snapshot normalization.
- [x] Enforce immutable snapshot read models.
- [x] Enforce authorization before repository access.
- [x] Verify fail-closed authorization behavior.
- [x] Verify no persistence, vendor refresh, or write surface.
- [x] Pass 35 targeted snapshot tests.
- [x] Pass 872 full regression tests.
- [ ] Implement SPF-009 Validation and Schema Drift.
- [ ] Keep Shopping WRITE operations disabled.
- [ ] Keep Ubuntu stateless and free of Shopping business logic.
<!-- SPF-008-CLOSE:END -->

<!-- AICONTROLCENTER:SPF-009:CLOSED -->
## SPF-009 Validation and Schema Drift Closure

- [x] Close SPF-009 runtime JSON Schema validation.
- [x] Close SPF-009 conservative schema drift classification.
- [x] Enforce authorization-before-schema-discovery.
- [x] Preserve `discover_schema(*, context, adapter_name)` as the authoritative read contract.
- [x] Validate fail-closed, sanitization, immutability and isolation behavior.
- [x] Pass 58 targeted tests and 930 full-regression tests with 5 deselected.
- [ ] Execute SPF-010 final production-readiness and operational closure.

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
- SPF-010 final closure: COMPLETE.
- Foundation remaining tasks: 0.
- Next planning task: define post-Foundation read-only integration scope before any mutation capability.

<!-- BEGIN AICONTROLCENTER:SRI-03 -->
## Active — SRI-03 External Read Integration

### Completed

- [x] Canonical WooCommerce read wrapper
- [x] Canonical normalization and validation
- [x] GET-only bounded read transport
- [x] Caddy runtime validation
- [x] Mac LAN ingress validation
- [x] External WAN HTTP 80 validation
- [x] DDNS and public IPv4 validation
- [x] Authoritative ipTIME CAA blocker analysis

### Controlled Production DNS

- [ ] Inventory a platform-controlled domain and DNS provider
- [ ] Select the canonical Shopping production hostname
- [ ] Configure or validate the production A record
- [ ] Keep AAAA absent until IPv6 ingress is validated
- [ ] Validate CAA issuance policy
- [ ] Validate staging TLS
- [ ] Perform one controlled Production TLS issuance

### SRI-03 closure

- [ ] Make Caddy reboot-safe
- [ ] Confirm the WooCommerce upstream
- [ ] Create a dedicated WooCommerce READ-only credential
- [ ] Execute one production canonical GET
- [ ] Validate canonical schema output
- [ ] Run Shopping regression
- [ ] Run full regression
- [ ] Verify Git status and exact scope
- [ ] Finalize README CHANGELOG MASTER ROADMAP PROJECT_HISTORY and TODO
- [ ] Produce Notion handoff
- [ ] Commit and push SRI-03 closure
<!-- END AICONTROLCENTER:SRI-03 -->

<!-- SRI-06B-R1:TODO -->
## Post-SRI Execution Queue

### DPL preparation

- Define deployment package architecture and immutable artifact contract.
- Define Codex task templates with scope, acceptance criteria, tests and rollback rules.
- Preserve Host Caddy as the sole public edge.
- Preserve protected credentials outside Git.

### Operational hardening

- Implement reusable recovery and forward-reconciliation modules in AIControlCenter.
- Add persisted evidence schema validators.
- Add scheduled read-only Health, Schema, Snapshot and Drift execution.
- Add route ownership tests for /healthz and WordPress fallback.

### Restrictions

- No Shopping business write until a separately approved write sprint.
- No AI workload or application business logic on Ubuntu.
- No architecture change through Codex without Architect approval.
<!-- END SRI-06B-R1 -->

<!-- AICONTROLCENTER:DPL-01:START -->
## Active — DPL Deployment Package

The earlier `Active — SRI-03 External Read Integration` section is historical
and superseded. SRI is COMPLETE at
`ba6fdb6a69ee9398b44fdd0810102b078c38c7f8`; its final recorded regression
baseline is `984 passed, 5 deselected`.

### DPL-01

- [x] Inventory deployment and platform artifacts.
- [x] Record ownership and architecture decisions.
- [x] Register DPL-B01 through DPL-B06.
- [x] Define DPL-01 through DPL-08.
- [x] Preserve production-write and activation prohibition.

### Complete — DPL-02 / M1

- [x] Define canonical versioned DPL package/report JSON Schemas and registry.
- [x] Implement read-only inventory, validation, readiness, GET composition,
  and audit-ready evidence.
- [x] Exclude `UbuntuWorkerClient.execute`.
- [x] Activate no Ubuntu adapter.
- [x] Define one canonical Host Caddy to Commerce ingress contract.
- [x] Deny POST, PUT, PATCH, and DELETE across DPL API routes.

### Next — DPL-03

- [ ] Enforce read/plan/apply package and dependency separation.

Production activation remains NOT AUTHORIZED.
<!-- AICONTROLCENTER:DPL-01:END -->

## DPL-04 Closed / M2 Next Action

- [x] Close DPL-04A, DPL-04B, DPL-04C and DPL-04D.
- [x] Accept M2 readiness from the canonical passing fixture.
- [x] Implement M2-P1 controlled non-production pilot authorization policy.
- [ ] Complete M2-P2 controlled sandbox pilot activation and evidence.
- [ ] Implement persistent SQLite deployment audit before broader mutable
      deployment.

M2 activation has not started. Production activation is not authorized.

## M3 Permit Replay Queue

- [x] Close M3-A2A read-only permit/replay foundation.
- [x] Close M3-A2B durable reservation, consumption and failed-closed writer.
- [x] Close M3-A2C replay-state backup, recovery and concurrency validation.
- [x] Close M3-A3A read-only operational monitoring foundation.
- [x] Close M3-A3B alert routing and deduplication.
- [x] Close M3-A3C monitoring and alert operational drill.
- [x] Close M3-A4A read-only operational activation readiness gate.
- [ ] Start M3-A4B controlled Mac operational bootstrap.

Operational replay database creation, backup scheduling, restore and writer
activation remain prohibited. Raw nonce writes remain zero.
Production activation remains `NOT_AUTHORIZED`.
# Next deployment task

M3-A4B2B1C — Independent Approver Action and Live Permit Issuance. This is a
separate authorization gate. M3-A4B2B1B does not authorize or perform it.
# Next deployment increment

- M3-A4B2B2B — Fresh Permit and Authorized Mac Bootstrap Execution.
- Requires fresh preflight and a fresh exact-commit permit.
- Production activation remains `NOT_AUTHORIZED`.
# Deployment

- Obtain fresh independent approval bound to the R2 commit before any
  authorized Mac bootstrap attempt.
- Keep production activation unauthorized.
# After R5

- Obtain fresh independent approval.
- Run the current-user Mac bootstrap only under a separate authorization gate.
- Keep M3-A4B3 blocked until the actual bootstrap succeeds.

# After M3-A4B3

- M3-A4B3 is closed; do not reuse the consumed permit or claim.
- Proceed to `M3-A4C_ACTIVATION_VALIDATION_AND_CLOSEOUT`.
- Keep writers, monitoring, dispatch, Ubuntu, and production inactive unless a
  separate future authorization gate explicitly changes their state.

# After M3-A4C

- Design `M4_CONTROLLED_ACTIVATION_ARCHITECTURE` with a separate independent
  authorization gate and per-capability default deny.
- Do not activate from the M3-A4C readiness report.
- Track the existing 427 deprecation warnings separately.

# After M4-A1

- M4-A1 is closed; do not interpret its architecture decision as activation
  authority.
- Implement `M4-A2_CAPABILITY_AUTHORIZATION_CONTRACTS` as a separate task.
- Keep all five capabilities inactive and unauthorized by default.
- Preserve independent approval, capability-scoped permit/claim, evidence, and
  rollback requirements; dependencies never grant authorization.
- Keep Mac as the AIControlCenter Control Plane, Ubuntu stateless, and
  production `NOT_AUTHORIZED`.
- Keep the existing 427 deprecation warnings on their separate backlog track.

# After M4-A2

- M4-A2 is closed as contract and validation only; it created no real
  authorization, permit, claim, or activation.
- Implement `M4-A3_TEST_ONLY_AUTHORIZATION_SIMULATION` as a separate task.
- Preserve one-capability independent authorization and treat dependency
  references as non-authorizing evidence.
- Keep production `NOT_AUTHORIZED`, Ubuntu excluded, and runtime effects
  disabled.
- Keep external endpoint details and secrets outside this boundary; `.env`
  remains unnecessary.
- Keep the existing 427 deprecation warnings on their separate backlog track.
- [x] Close AUTO-01 autonomous delivery controller architecture.
- [x] Define typed autonomy, lifecycle, manifest, DAG, approval, retry,
  evidence and bounded executor contracts.
- [x] Add fail-closed JSON schemas and deterministic planning tests.
- [ ] Implement AUTO-02 persistent Codex runner, terminal independence and
  recovery behind separate architecture and human-approval gates.

AUTO-01 creates no runner or operational authority. Production remains
`NOT_AUTHORIZED`; no `.env` is required. Track the existing 427 deprecation
warnings separately.

<!-- SHOPPING-FIRST-REPRIORITIZATION:BEGIN -->
## Active Next Task

`SHOP-00_ARCHITECTURE_REPRIORITIZATION`

Do not begin AUTO-02, AUTO-03 or M4-A4 through M4-A6 without a new
architecture decision. The next production-facing milestone is a
read-only WooCommerce product vertical slice.
<!-- SHOPPING-FIRST-REPRIORITIZATION:END -->

<!-- SHOP-00-CLOSEOUT:BEGIN -->
## Active Shopping Task

`SHOP-01_PRODUCT_MANAGEMENT_READ_MODEL_AND_DASHBOARD`

Required first vertical slice:

WooCommerce product snapshot
→ existing AIControlCenter Shopping query
→ management read model
→ existing Dashboard surface
→ product list and integration-health view

Prohibited in SHOP-01:

- WooCommerce POST, PUT, PATCH or DELETE
- direct Dashboard-to-WooCommerce communication
- product draft persistence
- approval execution
- AI generation
- Ubuntu business logic
<!-- SHOP-00-CLOSEOUT:END -->

<!-- SHOP-01B-MANAGEMENT-READ-MODEL:BEGIN -->
## Active Shopping Task

`SHOP-01C_DASHBOARD_JSON_INTEGRATION`

Connect the completed Shopping management read model to the existing
`DashboardAPI` through an optional injected dependency.

Required behavior:

- preserve the existing `/dashboard` response
- add a `shopping_management` JSON section
- isolate Shopping failures from the rest of the Dashboard
- avoid direct WooCommerce dependencies
- add no mutation route
- add no product persistence
<!-- SHOP-01B-MANAGEMENT-READ-MODEL:END -->

<!-- SHOP-01C-DASHBOARD-INTEGRATION:BEGIN -->
## Active Shopping Task

`SHOP-01D_VALIDATION_AND_CLOSEOUT`

Validate and close the Product Management Dashboard read-only vertical
slice.

Required validation:

- `/dashboard.shopping_management` contract
- product summary and product list projection
- unavailable-state failure isolation
- Shopping mutation route count remains zero
- full regression
- documentation closeout
<!-- SHOP-01C-DASHBOARD-INTEGRATION:END -->

<!-- SHOP-01D-CLOSEOUT:BEGIN -->
## Active Shopping Task

`SHOP-02A_PRODUCT_DRAFT_WORKFLOW_ARCHITECTURE`

Define the AIControlCenter-owned product draft workflow before adding
state or write capabilities.

Required architecture decisions:

- canonical ProductDraft JSON contract
- lifecycle states
- draft ownership and persistence boundary
- source product snapshot reference
- human approval boundary
- audit reference model
- idempotency and revision rules
- WooCommerce write exclusion
- AI provider adapter boundary

Prohibited in SHOP-02A:

- WooCommerce mutation
- product publishing
- production authorization
- autonomous approval
- Ubuntu business logic
<!-- SHOP-01D-CLOSEOUT:END -->

<!-- SHOP-01E2-COMPATIBILITY-ADAPTER:BEGIN -->
## Active Shopping Task

`SHOP-01E3_WOOCOMMERCE_READ_ONLY_CONFIGURATION`

Configure and validate the existing WooCommerce read adapter without
enabling any write capability.

Required gates:

- secret values are never printed
- adapter is `woocommerce`
- write mode remains `read_only`
- approval remains required
- automation remains disabled
- bounded WooCommerce GET succeeds
- management Dashboard projection is not `UNAVAILABLE`
- Shopping mutation route count remains zero
<!-- SHOP-01E2-COMPATIBILITY-ADAPTER:END -->

<!-- SHOP-01E3C-SECURE-RUNTIME:BEGIN -->
## Active Shopping Task

`SHOP-02A_PRODUCT_DRAFT_WORKFLOW_ARCHITECTURE`

Define the AIControlCenter-owned Product Draft contract and lifecycle.

Separate deployment backlog:

`SHOP-01E3D_READ_ONLY_PROFILE_ACTIVATION`

The deployment task may only set the non-secret Shopping profile in
the Mac Control Plane process. It must not place WooCommerce
credentials in a plist or shell command.
<!-- SHOP-01E3C-SECURE-RUNTIME:END -->

## SHOP-02

- [x] SHOP-02A immutable ProductDraft workflow architecture and static contracts.
- [x] SHOP-02B immutable ProductDraft 1.0.0 domain and isolated in-memory repository adapter; no API route, persistence, or WooCommerce write.
- [x] SHOP-02C deterministic validation and human approval application service; contracts 1.0.0, deny-by-default authorization, HUMAN-only exact-revision decisions, in-memory audit/idempotency, and no external writes.
- [ ] SHOP-02D ProductDraft read API and Dashboard projection.
- [ ] SHOP-01E3D persistent activation remains separately deferred.

Production writes are `NOT_AUTHORIZED`; catalog population is independent.
# SHOP-02D closeout

- [x] Add the three GET-only ProductDraft routes.
- [x] Add deterministic collection, exact revision, review queue, and Dashboard projections.
- [x] Preserve ProductDraft contracts at 1.0.0 and distinguish empty from unavailable sources.
- [x] Keep WooCommerce writes, mutation routes, persistence, and production activation absent.
- [ ] Design SHOP-03 controlled WooCommerce write architecture; production writes remain `NOT_AUTHORIZED`.

## SHOP-03

- [x] SHOP-03A controlled Commerce write architecture with exact eligibility, deny-by-default authorization, instance-local idempotency, deterministic preview, and fake/dry-run adapter only.
- [ ] SHOP-03B separately authorized controlled write; real adapter remains `NOT_IMPLEMENTED` and production writes remain `NOT_AUTHORIZED`.
# SHOP-03B follow-up

- [x] SHOP-03B1 intercepted WooCommerce adapter, credential boundary, fail-closed transport, normalization, and reconciliation.
- [ ] SHOP-03B2 bind one exact product/revision/deployment intent and execution timestamp through a separate authorization gate before any production request.
## Shopping operator UI

- [x] UI-01 internal read-only Homepage at `GET /homepage`.
- [x] UI-02 internal read-only Product Management Console.
- [ ] OPS-01 staging Caddy, authentication, monitoring, and separately
  authorized public opening.

UI-01 uses only `GET /dashboard`; it adds no framework, mutation API, live
Commerce write, authentication change, or ProductDraft/deployment contract
change.

UI-02 consumes only the existing ProductDraft GET APIs, distinguishes `EMPTY`
from `UNAVAILABLE`, and adds no write control, persistence, or activation.

## PI-009A2

- [ ] define immutable runtime source artifact contract
- [ ] add source snapshot build/staging validation
- [ ] bind source identity to runtime identity
- [ ] remove repository PYTHONPATH dependence from production wrapper
- [ ] add source/runtime identity validator
- [ ] add focused regression tests
- [ ] validate rollback design
- [ ] require explicit authorization before wrapper/service mutation
- [ ] verify exact loaded `core.api.shadow` source path
- [ ] rerun PI-009 Technical Production Authorization Review

## PI-009A2 Architecture Freeze

- [x] confirm Candidate venv does not contain application source
- [x] confirm repository has no Python packaging descriptor
- [x] confirm exact Candidate source commit
- [x] confirm immutable `git archive` capability
- [x] select paired venv/source Runtime model
- [x] preserve current Runtime pointer semantics
- [ ] implement source artifact builder
- [ ] implement source artifact validator
- [ ] implement repository-managed immutable-source wrapper
- [ ] add focused tests
- [ ] obtain A2.2 source-artifact authorization
- [ ] create and validate immutable source artifact
- [ ] obtain A2.3 wrapper-cutover authorization
- [ ] install wrapper and perform one authorized service kickstart
- [ ] verify exact loaded source path
- [ ] rerun PI-009 Production Authorization Review

## PI-009A2 State Isolation

- [x] identify repository-relative conversation state
- [x] identify repository-relative scheduler state
- [x] add canonical `AICONTROLCENTER_DATA_ROOT` resolver
- [x] isolate conversation database from immutable source
- [x] isolate scheduler database from immutable source
- [x] validate read-only source plus external writable state
- [ ] complete A2.1 immutable source artifact tooling
- [ ] create new source commit identity
- [ ] build new Runtime Candidate from repaired source
- [ ] validate new Candidate/source/state identity
- [ ] authorize operational source artifact creation
- [ ] authorize immutable-source wrapper cutover
- [ ] rerun final PI-009 gate

## PI-009A2 A2.1 Completion

- [x] repair application state isolation
- [x] implement immutable source artifact builder
- [x] implement immutable source validator
- [x] enforce source content digest
- [x] enforce state-isolation module presence
- [x] implement immutable-source wrapper template
- [x] remove mutable repository application import path
- [x] enforce Python `-P`
- [x] preserve external `AICONTROLCENTER_DATA_ROOT`
- [x] validate immutable source plus external state
- [x] confirm canonical bootstrap is HEAD-only
- [ ] authorize new Runtime Candidate build
- [ ] build new Runtime Candidate
- [ ] validate new Candidate
- [ ] authorize operational source artifact creation
- [ ] validate operational immutable source
- [ ] authorize wrapper cutover and one kickstart
- [ ] rerun PI-009 final gate

## PI-009A2 A2.2A

- [x] authorize exactly one Runtime Candidate build
- [x] execute canonical Runtime build exactly once
- [x] validate canonical build report
- [x] validate Runtime source marker and metadata
- [x] validate Runtime dependencies
- [x] validate immutable source + external state execution
- [x] confirm Runtime pointer unchanged
- [x] confirm service unchanged and healthy
- [ ] authorize operational source artifact creation
- [ ] create `runtime/sources/7b171f135dc7`
- [ ] validate operational immutable source
- [ ] authorize wrapper cutover and one kickstart
- [ ] rerun PI-009 final Production gate

## PI-009A2 A2.2B

- [x] authorize immutable source artifact creation
- [x] invoke source builder exactly once
- [x] validate builder JSON
- [x] validate source manifest
- [x] validate source content digest
- [x] validate read-only permissions
- [x] validate Runtime/source identity
- [x] validate operational immutable-source execution
- [x] validate external application state
- [x] confirm active Runtime unchanged
- [x] confirm live service unchanged
- [ ] authorize A2.3 controlled live cutover
- [ ] switch Runtime pointer to `7b171f135dc7`
- [ ] install immutable-source live wrapper
- [ ] perform exactly one launchd kickstart
- [ ] validate live immutable source execution
- [ ] run PI-009 final Production gate

## PI-009A2 A2.3

- [x] state continuity migration
- [x] immutable wrapper installation
- [x] canonical Runtime activation
- [x] service restore
- [x] immutable source validation
- [x] external state validation
- [x] HTTP validation
- [ ] PI-009 final technical Production review
- [ ] explicit human Production authorization

## PI-009 Final Production Gate

- [x] immutable Runtime/source live cutover
- [x] persistent-state continuity
- [x] final deployment regression
- [x] final operational validation
- [x] corrected launchd final-gate parser false blocker
- [x] explicit human Production authorization
- [x] machine-readable authorization evidence
- [ ] synchronize final milestone to Notion
