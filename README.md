# AIControlCenter

## AI-PROVIDER-01C-A Control Plane Workflow Integration

The canonical `BrainAgent.ask` workflow now selects an explicit configured or
request-supplied provider through `ProviderRouter`, which is the application
provider boundary. Business logic receives only normalized JSON-safe results
from `ProviderAdapter`; it owns no vendor SDK transport behavior. Unknown
providers fail closed, and no automatic cross-provider fallback or retry is
allowed. Focused FakeProvider tests made zero network calls and no authenticated
provider call occurred. Production Runtime remains `7b171f135dc7`. 01C-B will
create a new Candidate Runtime; 01C-C requires explicit human authorization for
Production promotion. Notion is `DEFERRED_UNTIL_FINAL_PHASE`.

## AI-PROVIDER-01B Authenticated OpenAI Transport

The OpenAI Responses API transport is implemented behind the vendor-neutral
`ProviderAdapter` contract. `OPENAI_API_KEY` remains external, is read only at
invocation time, and must never be stored in Git. Requests have explicit model
and input, bounded timeout/output, exactly one attempt, and no cross-provider
fallback. Mocked repository tests made no network request; the human-controlled
authenticated smoke is pending. Production Runtime `7b171f135dc7` remains
untouched, AI-PROVIDER-01C owns candidate Runtime integration/promotion, and
Notion is `DEFERRED_UNTIL_FINAL_PHASE`. See
`docs/architecture/AI-PROVIDER-ADAPTER-ARCHITECTURE.md`.

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
<!-- AICONTROLCENTER:ACTIVATION_01B_C2:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_C1_CLOSEOUT:START -->
## ACTIVATION-01B-C1 Contract Foundation

Status: `COMPLETE`

Added three versioned read-only inspection contracts:

- `ActivationInspectionPolicy`
- `ActivationRouteManifest`
- `ActivationInspectionReport`

Validation evidence:

- Focused contract gate: `41 passed`
- Safe deployment regression: `1017 passed`
- Warnings: `9`
- Operational harness suites: `DEFERRED`

Deferred operational suites require isolated test-root
environments and are tracked separately as test-infrastructure
work.

Architecture base commit:

`dc482780fdd36ba50d4947e8193380d7426d8367`

Production remains `NOT_AUTHORIZED`.
<!-- AICONTROLCENTER:ACTIVATION_01B_C1_CLOSEOUT:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_ARCHITECTURE:START -->
## ACTIVATION-01B Read-Only Activation Inspector

Status: `ARCHITECTURE_FROZEN`

Architecture:

`docs/deployment/ACTIVATION-01B-READ-ONLY-INSPECTOR-ARCHITECTURE.md`

Runbook:

`docs/operations/macos/ACTIVATION-01B-READ-ONLY-INSPECTOR-RUNBOOK.md`

The frozen design defines a JSON-first, fail-closed inspector
for Git, Runtime, Python, launchd, process, listener and direct
localhost HTTP evidence.

The inspector implementation and real-host inspection have not
started.

Runtime activation, service restart, rollback, public opening,
Ubuntu changes and Production authorization remain prohibited.

Architecture predecessor commit:

`43975f6e26986fd91c9a715786e7c68deb63f612`
<!-- AICONTROLCENTER:ACTIVATION_01B_ARCHITECTURE:END -->

<!-- AICONTROLCENTER:ACTIVATION_01A:START -->
## ACTIVATION-01A Runtime Activation

Status: `COMPLETE`

Contract documentation commit: `d14058553baa1dfc45e027a59ff580013584913b`

Gate: `ACTIVATION-01A — Architecture and Runbook Only`

The atomic Runtime activation contract is documented at
`docs/operations/macos/ACTIVATION-01A-RUNTIME-ACTIVATION-CONTRACT.md`.

Bound baseline:

- Candidate Runtime: `acd80ab9f6ae`
- Active Runtime: `b9ad351a7241`
- Canonical serving target: `core.api.shadow:app`
- LaunchDaemon: `system/com.aicontrolcenter.api.shadow`
- Localhost listener: `127.0.0.1:18100`
- Production: `NOT_AUTHORIZED`

No Runtime switch, service restart, rollback, launchd or Caddy change,
public opening, Ubuntu change or Production authorization occurred.

The candidate application source remains repository-bound through
effective `PYTHONPATH`. ACTIVATION-01B is the next read-only gate after
the ACTIVATION-01A documentation commit.
<!-- AICONTROLCENTER:ACTIVATION_01A:END -->

## Current verified platform status

AIControlCenter remains the Mac mini M4-owned Control Plane, with Ubuntu only
as an optional stateless infrastructure worker. Controlled bootstrap tests now
use immutable trusted evidence binding and a deterministic canonical
non-production evidence generator instead of historical host evidence. Git
identity inspection is file-backed and read-only, with loose-ref precedence,
exact packed-ref fallback, detached-HEAD support, and fail-closed bounded
symbolic resolution.

Source/documentation commit
`acd80ab9f6aeb848900e1a19e3fa3afd69face8a` produced validated side-by-side
release `acd80ab9f6ae`. The canonical serving target is
`core.api.shadow:app`; its `ReadOnlyASGI` Shadow application composes internal
FastAPI target `core.api.app:app`. Dependency installation, application import,
the Full Suite, source marker, and metadata validation passed. FastAPI was
`0.139.0`, Uvicorn was `0.51.0`, and `jsonschema` was available.

The canonical macOS Runtime builder requires an explicit `build` or `activate`
mode and fails closed otherwise. Build uses owned staging, validates metadata
and the exact source marker, atomically finalizes an immutable release, and
preserves `runtime/current`. Activation is separately authorized, accepts only
an already finalized validated release, and atomically switches
`runtime/current` without installing dependencies or restarting services. The
builder is executable with Git mode `100755`, protected by a deterministic
regression test. Runtime current remains active release `b9ad351a7241`;
`runtime/current` was unchanged and new release `acd80ab9f6ae` was not
activated. Rollback foundations exist through side-by-side releases and an
atomic-current design, but neither activation nor rollback has occurred.

Direct localhost smoke returned 200 for `/health`, `/runtime/health`,
`/homepage/status`, `/homepage`, `/homepage/product-management`, and
`/datacenter/status`; `POST /health` returned 405. Exact smoke PID and listener
cleanup passed. The builder report was valid structured JSON on stdout and was
recovered and validated from the builder log after the wrapper found no
canonical report file. That report persistence gap and an unavailable optional
host `rg` command are operational tooling debt, not release defects.

The internal Homepage and Product Management Console have completed direct
localhost HTTP smoke, but not activation, staging, Caddy authentication, or
public exposure. Python and dependencies are release-owned; application source
is still loaded from the mutable repository through `PYTHONPATH`
(`source_bundled_inside_release=false`, `repository_source_binding=true`). The
release must not be described as fully source-immutable. Source bundling,
source manifesting, and source-independent launch remain future work.

The next controlled sequence is: documentation commit; non-force push and
remote verification; new-chat handoff before the activation risk boundary;
ACTIVATION-01A architecture and runbook only; read-only activation preflight;
separately authorized atomic switch; exact service restart; post-activation
validation; rollback validation; and authenticated Caddy staging. Runtime
activation, rollback execution, service restart, public staging, production,
and production writes remain `NOT_AUTHORIZED`. No service, launchd, Caddy,
Ubuntu, public, or production change occurred.

M3-A4B2B2B-R4 aligns the strict preflight and live permit contracts. The exact
Boolean `ubuntu_participation=false` is accepted only as Ubuntu
non-participation evidence; all unsafe alternatives remain default-deny.
Permit issuance and orchestration now share an immutable typed result. The
authorized attempt was `BLOCKED_PRE_AUTHORIZATION`; no actual authorization,
permit, claim, bootstrap, or managed target exists. Fresh approval must bind
R4, production remains `NOT_AUTHORIZED`, and M3-A4B3 remains blocked.

Recovery-2 closes the first blocked R3 recovery with a bounded read-only
`/usr/bin/git` adapter isolated in `core.deployment.git_readonly_evidence`.
Public audit/replay inspectors, PRE_ACTIVATION monitoring, and post-claim
failure evidence are independently validated. The validation runner remains
validation-only; actual bootstrap is `NOT EXECUTED`, managed targets remain
absent, fresh approval must bind the final commit, and production is
`NOT_AUTHORIZED`.

The previous M3-A4B2B2B-R3 attempt was `BLOCKED`. R3 recovery adds the
reviewed default live composition and mandatory pytest-only end-to-end
orchestration. The existing execution runner remains validation-only; the live
runner uses the dedicated composition root. No actual Mac bootstrap ran,
actual managed targets remain absent, fresh independent approval must bind the
recovery commit, and production activation remains `NOT_AUTHORIZED`.

## M3-A4B2B2B-R1 closure

Existing safe Mac application-state parents are compatible with controlled
bootstrap without changing parent metadata or unrelated siblings. Deployment
control owns only absent `audit`, `security` and `monitoring` children. Mode
`0755` is accepted with an explicit restriction; managed directories remain
`0700` and managed files `0600`. Recovery was read-only: no operational permit,
claim or bootstrap occurred. Fresh approval is required and Production remains
`NOT_AUTHORIZED`.

## M3-A4B2B1A closure

The deterministic operational permit issuance review package is AVAILABLE.
M3-A4A, M3-A4B1, M3-A4B2A, M3-A4B2B0 and M3-A4B2B1A are CLOSED after
validation. Human identities and restriction acknowledgements are NOT PROVIDED.
No permit is issued or claimed, no bootstrap is authorized or executed, no
operational target is created, and production remains NOT_AUTHORIZED. Next:
M3-A4B2B1B.

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

### M3-A4B2B0

M3-A4A, M3-A4B1, M3-A4B2A and M3-A4B2B0 are closed. The deterministic,
read-only Mac operational bootstrap host preflight is available. Operational
permit is not issued, authorization is not granted, bootstrap is not executed,
operational directories and databases are not created, and Production
activation is `NOT_AUTHORIZED`. Next: M3-A4B2B1 Operational Permit Issuance.

### M3-A4B2A

M3-A4A, M3-A4B1 and M3-A4B2A are closed. The controlled Mac bootstrap
executor is implemented and validated only beneath injected pytest temporary
paths. Synthetic permit consumption, audit/replay schema bootstrap, baseline
backup/restore and failure cleanup are validated. No operational permit was
issued, operational bootstrap was not executed, operational state was not
created, writers and monitoring were not activated, and Production activation
is `NOT_AUTHORIZED`. Next: M3-A4B2B Authorized Mac Operational Bootstrap
Execution.

### M3-A4B1

M2, M3-A1, M3-A2, M3-A3, M3-A4A and M3-A4B1 are closed. Controlled
non-production bootstrap authorization contracts and a single-use registry
port are available; synthetic permit issuance is validated. No operational
permit was issued, bootstrap authorization was not granted, bootstrap was not
executed, operational paths were not created, writers were not activated, and
Production activation is `NOT_AUTHORIZED`. Next: M3-A4B2 Controlled Mac
Operational Bootstrap.

### M3-A4A

M2, M3-A1, M3-A2, M3-A3 and M3-A4A are closed. The pure activation readiness
gate and controlled bootstrap plan are available, but neither authorizes nor
executes bootstrap or activation. Operational databases are not created;
operational writers and monitoring are not activated; external alert dispatch
is not implemented; bootstrap authorization is not granted; Production
activation is `NOT_AUTHORIZED`. Next: M3-A4B Controlled Mac Operational
Bootstrap.

### M3-A3C

M3-A1, M3-A2, M3-A3A, M3-A3B and M3-A3C are closed; the M3-A3 Monitoring and
Alert Track is closed. The deterministic end-to-end monitoring drill and
simulated logical delivery are validated using only an object-scoped in-memory
sink. External dispatch and alert persistence are not implemented. Operational
monitoring is not activated, operational databases were not created, and
Production activation is `NOT_AUTHORIZED`. Next: M3-A4 Controlled Operational
Activation Gate.

### M3-A3B

M3-A1, M3-A2, M3-A3A and M3-A3B are closed. Logical alert routing,
deterministic deduplication and severity escalation policy are available.
External alert dispatch and alert-routing persistence are not implemented.
Operational monitoring is not activated, operational databases were not
created, and Production activation is `NOT_AUTHORIZED`. Next: M3-A3C
Monitoring and Alert Operational Drill.

### M3-A2A

M2 controlled pilot validation, M3-A1 and M3-A2A are closed. Deterministic
read-only permit/replay SQLite inspection is available for an explicitly
injected Mac application-state path. The operational permit/replay database
was not created; durable reservation, consumption and persistent nonce writes
are not enabled; Production activation is `NOT_AUTHORIZED`. Next: M3-A2B
Durable Permit Reservation and Consumption.

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

## SHOP-03A controlled Commerce write boundary

SHOP-03A is complete with immutable eligibility, exact deny-by-default authorization, successful-plan idempotency, deterministic preview, and only an isolated fake/dry-run Commerce write adapter. A real WooCommerce write adapter is `NOT_IMPLEMENTED`; there is no mutation route or persistent queue. ProductDraft contracts remain 1.0.0 and production writes remain `NOT_AUTHORIZED`. SHOP-03B requires separate explicit architecture and authorization.

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

Runtime identity requires immutable `metadata.json` and
`.aicontrolcenter-source-commit` files generated together during explicit
build mode. The marker is an exact lowercase 40-character Git SHA plus one
newline. Build finalizes only after generation and validation and does not
change `runtime/current`. Explicit, separately authorized activate mode
revalidates the finalized release before the atomic switch, and the Shadow
daemon fails closed when the marker is missing or invalid. Existing immutable
releases are not repaired in place.

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

## M3-A2C Replay-State Recovery

M3-A1 and M3-A2A through M3-A2C are CLOSED. Explicit-path online SQLite backup,
canonical manifest, restore, exact recovery and post-recovery concurrency were
validated only with pytest temporary databases. The operational replay DB was
not created; no backup schedule, restore or writer was activated; raw nonce
writes remain zero; and Production activation is `NOT_AUTHORIZED`. Next:
M3-A3 Operational Monitoring and Alerts.
# M3-A4B2B1B status

M3-A4B2B1A is CLOSED. M3-A4B2B1B is CLOSED after validation: the human
approval gate is AVAILABLE, synthetic dual-identity approval and in-memory
permit issuance are VALIDATED, and the current recommended review is DENIED.
The requester/operator is `mac-account:kyouhan`; the independent approver is
`UNASSIGNED`, so independent approval and acknowledgement are NOT PROVIDED.
No operational permit was issued or claimed, bootstrap remains unauthorized
and unexecuted, and production activation is `NOT_AUTHORIZED`. Next:
M3-A4B2B1C Independent Approver Action and Live Permit Issuance.
# M3-A4B2B2A authorized Mac bootstrap execution

The authorized Mac bootstrap execution capability is available and validated
in test-only confinement. Atomic permit claim and fail-closed cleanup passed;
controlled operational mode was not executed, no operational targets or
databases were created, writers and monitoring remain inactive, and production
activation is `NOT_AUTHORIZED`. A fresh preflight and fresh permit are required
for M3-A4B2B2B.
# M3-A4B2B2B-R2

The controlled non-production operational activation authorization boundary is
implemented and validated as a default-deny capability. No real permit, claim
or Mac operational bootstrap was performed; production remains unauthorized.
# R5 acknowledgement compatibility

M3-A4B2B2B-R5 preserves full restriction acknowledgements separately from the
exact two-entry executor warning projection. Compatibility is validated before
authorization/issuance and again before claim. The actual bootstrap remains
`NOT EXECUTED`; production is `NOT_AUTHORIZED`.

# M3-A4B3 bootstrap evidence and recovery

The single controlled non-production bootstrap at commit
`f7a81b73b86c170300bb6b80f437dbb753362f7e` is now content- and
digest-validated from read-only snapshots. Audit and replay are `HEALTHY` with
zero events, and both baseline backups passed isolated restores. The permit is
permanently consumed; writers, monitoring, dispatch, Ubuntu, and production
authorization remain false. Next: `M3-A4C_ACTIVATION_VALIDATION_AND_CLOSEOUT`.

# M3-A4C controlled activation closeout

M3 is closed at `0f23abdf362965c09db5f4f35483cbff47853643` with
`READY_FOR_SEPARATELY_AUTHORIZED_CONTROLLED_ACTIVATION`. This is not
activation or production authorization. The Mac remains the Control Plane;
writers, monitoring, dispatch, Ubuntu participation, and production remain
false. Future activation requires a separate gate. The 427 warnings remain
backlog.

# M4-A1 controlled activation architecture

M4 begins with pure architecture contracts bound to M3 closeout commit
`89d10da82545e6cfd173085719076bb71e14c120`. Five capabilities default to
inactive and unauthorized and require independent capability-scoped approval,
permit, claim, evidence, validation, and rollback boundaries. The deterministic
planner has no operational side effects. Its
`READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS` decision is not authorization.
Mac remains the Control Plane, Ubuntu remains stateless, production is
`NOT_AUTHORIZED`, and the 427 warnings remain separate backlog.

# M4-A1R1 SQLite fixture isolation

M4-A1 commit `b719aa445af864c907ac5d384c2c8347d2d6688a` is closed with a
formal retained-source versus disposable-working-copy SQLite fixture boundary.
All inspection and recovery validation uses copied database/WAL/SHM sets;
retained bytes, modes, sizes, mtimes, and digests remain unchanged. Actual
operational state was not accessed or changed, `.env` is not required, and
production remains `NOT_AUTHORIZED`. The architecture-only decision remains
`READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS`; next is
`M4-A2_CAPABILITY_AUTHORIZATION_CONTRACTS`.

# M4-A2 capability authorization contracts

M4-A1 and M4-A1R1 are closed. M4-A2 defines immutable, canonical,
single-capability request and independent-approval contracts for all five
registry capabilities. Exact Git, M3, M4-A1, identity, restriction, dependency,
and bounded-time validation produces only a deterministic test grant plan.
`READY_FOR_TEST_ONLY_AUTHORIZATION_SIMULATION` creates no authorization,
permit, claim, writer, monitoring runtime, dispatch, or activation.

Authorization never implies activation or another capability. Production
remains `NOT_AUTHORIZED`, Ubuntu remains excluded, external-notification
endpoint details and secrets are outside scope, and `.env` is not required.
The existing 427 deprecation warnings remain separate backlog. Next:
`M4-A3_TEST_ONLY_AUTHORIZATION_SIMULATION`.

# M4-A3 test-only authorization simulation

M4-A1, M4-A1R1, M4-A2, and M4-A3 are closed. M4-A3 provides deterministic
in-memory simulation for all five independent capabilities. Every artifact is
unmistakably test-only and operationally invalid; live boundaries reject it.
No real authorization, operational permit, claim, writer, monitoring, dispatch,
notification, Ubuntu action, or activation occurred. Production remains
`NOT_AUTHORIZED`, `.env` is not required, and the 427 warnings remain backlog.
Decision: `READY_FOR_READ_ONLY_OPERATIONAL_OBSERVATION`. Next:
`M4-A4_READ_ONLY_OPERATIONAL_OBSERVATION`.
# AUTO-01 autonomous delivery controller architecture

AUTO-01 is closed as architecture and deterministic planning only.
AIControlCenter remains the single Control Plane; Codex is a replaceable,
bounded executor only. Typed autonomy levels, lifecycle gates, JSON-first sprint
manifests, deterministic DAG planning, approval and retry policies, evidence
requirements and an abstract executor port are defined. No runner, subprocess,
launchd service, operational write, authorization, permit, claim, monitoring,
dispatch or activation was created.

M4-A3 remains CLOSED with `READY_FOR_READ_ONLY_OPERATIONAL_OBSERVATION`.
AUTO-01 decides `READY_FOR_PERSISTENT_RUNNER_ARCHITECTURE`. AUTO-02 will address
terminal independence, persistent runner and recovery architecture. Human
approval remains mandatory for L4/L5 and post-claim recovery; automatic retry
after a real claim is prohibited. Ubuntu remains stateless-worker-only, `.env`
is not required, production is `NOT_AUTHORIZED`, and the 427 deprecation
warnings remain separate backlog.

<!-- SHOPPING-FIRST-REPRIORITIZATION:BEGIN -->
## Primary Product Roadmap

The active product roadmap is:

1. Shopping Platform
2. AI Integration Platform
3. Personal AI Assistant

Shopping must work without AI. AI enhances Shopping but does not own
Commerce. The Assistant consumes service APIs but does not own service
business logic.

AUTO-01 is closed as an architecture foundation. AUTO-02, AUTO-03 and
M4-A4 through M4-A6 are deferred until product-facing milestones require
them. Production remains `NOT_AUTHORIZED`.
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

## SHOP-02A Product Draft Workflow

SHOP-01E read foundation is closed; SHOP-01E3D persistent activation remains deferred. SHOP-02A defines immutable, revision-bound ProductDraft contracts and human-only approval architecture. WooCommerce remains product truth. Production writes are `NOT_AUTHORIZED`; the observed catalog baseline remains zero products and one category, independent of draft work. Next: `SHOP-02B_PRODUCT_DRAFT_DOMAIN_IMPLEMENTATION`.

## SHOP-02B Product Draft Domain

SHOP-02B implements the immutable ProductDraft 1.0.0 value objects, revision aggregate, closed lifecycle evaluator, deterministic serialization, repository port, and isolated in-memory adapter. The adapter is non-production: no persistent storage, API mutation route, WooCommerce write, or deployment authorization was added. Production writes remain `NOT_AUTHORIZED`. Next: `SHOP-02C_PRODUCT_DRAFT_VALIDATION_APPROVAL_SERVICE`.

## SHOP-02C Product Draft Application Services

SHOP-02C adds deterministic contract validation and authorized, exact-revision human review application services. Authorization is deny-by-default; APPROVE, REJECT, and REVOKE are HUMAN-only. Audit and idempotency adapters are isolated in-memory test infrastructure. ProductDraft contracts remain 1.0.0. No API mutation route, persistent storage, or WooCommerce write was added, and production writes remain `NOT_AUTHORIZED`. Next: `SHOP-02D_PRODUCT_DRAFT_READ_API_DASHBOARD`.
# SHOP-02D ProductDraft reads

AIControlCenter exposes GET-only ProductDraft reads at `/shopping/product-drafts`, `/shopping/product-drafts/{draft_id}`, and `/shopping/product-drafts/{draft_id}/revisions/{revision_id}`. The Dashboard key is `product_draft_review`. Its replaceable source is unavailable by default; an explicitly configured empty source is valid and distinct from `UNAVAILABLE`. Contracts remain 1.0.0. No mutation routes, WooCommerce writes, or persistent ProductDraft storage were added. Production writes remain `NOT_AUTHORIZED`; SHOP-03 controlled WooCommerce write architecture is next.
# SHOP-03B1 controlled live-write boundary

SHOP-03B is user-attested as authorized at `2026-08-03T08:54:00+09:00` for architecture, implementation, and intercepted validation. SHOP-03B1 adds a synchronous, injected WooCommerce write boundary under ProductDraft deployment. Credentials are obtained only at call time and passed separately from immutable request metadata; the default credential provider and transport fail closed. There is no concrete network transport, no mutation route, and every result remains `INTERCEPTED_VALIDATION` with `live_write_performed: false`.

No exact product, ProductDraft revision, deployment intent, or execution timestamp is authorized. External requests: 0. Live writes: 0. Production activation: `NOT_AUTHORIZED`. ProductDraft and deployment-intent contracts remain version 1.0.0. SHOP-03B2 is the next one-product controlled pilot.
## UI-01 internal Shopping Homepage

The internal read-only Shopping operations Homepage is available at `GET
/homepage`. It consumes only same-origin `GET /dashboard`, including the exact
`shopping_management` and `product_draft_review` projections. It adds no
frontend framework, public Caddy exposure, authentication change, mutation API,
or live Commerce write. See `docs/homepage/UI-01-shopping-dashboard.md`.

## UI-02 internal Product Management Console

The read-only console is available at `GET /homepage/product-management`. It
uses only the three existing same-origin ProductDraft GET resources, keeps
empty and unavailable states distinct, and exposes no mutation or live Commerce
control. It is not publicly exposed and production activation remains
`NOT_AUTHORIZED`. See `docs/homepage/UI-02-product-management-console.md`.
Next: `OPS-01_STAGING_CADDY_AUTH_MONITORING`.

## PI-009A1 Deployment Test Gate

PI-009A1 is complete.

The deployment regression harness and dependency-boundary policy were repaired
and the complete deployment suite passed with 1133 tests.

Production remains unauthorized.

The remaining technical Production blocker is `RUNTIME_SOURCE_ISOLATION`:
the service must execute immutable release source instead of importing
application code from the mutable repository working tree.

## PI-009A2 Runtime Source Isolation

The PI-009A2 architecture is frozen.

AIControlCenter production Runtime identity will consist of a paired immutable
venv and Git source snapshot. The existing current pointer remains unchanged.

Repository implementation is allowed first. Runtime source creation and wrapper
cutover require separate explicit human authorizations.

Production remains unauthorized.

### PI-009A2 Application State Isolation

Immutable-source validation exposed two repository-relative SQLite state paths.

Memory and scheduler state now use the canonical
`AICONTROLCENTER_DATA_ROOT` contract.

Production source remains read-only while writable state lives under the
AIControlCenter application data root.

The former Candidate `acd80ab9f6ae` cannot be promoted as the final
immutable-source release. A new Candidate is required.

### PI-009A2 A2.1 Complete

Immutable Runtime source artifact tooling and the immutable-source wrapper
template are implemented.

The source artifact is read-only and application state remains external through
`AICONTROLCENTER_DATA_ROOT`.

The canonical Runtime bootstrap is HEAD-only. Therefore the A2.1 completion
commit is the source identity for the next Runtime Candidate.

No operational source artifact or service cutover has occurred.

Production remains unauthorized.

### PI-009A2 A2.2A Runtime Candidate Validated

Runtime Candidate `7b171f135dc7` was built exactly once through the canonical
Runtime bootstrap from source commit `7b171f135dc7882546bf7f733208778f1aef4943`.

The canonical build, dependency validation, full test suite and temporary
immutable-source/external-state execution all passed.

The active Runtime, live wrapper and service remained unchanged.

Production remains unauthorized.

### PI-009A2 A2.2B Immutable Source Validated

Runtime Candidate `7b171f135dc7` now has a matching operational immutable
source artifact built from source commit `7b171f135dc7882546bf7f733208778f1aef4943`.

The artifact is read-only, has no Git metadata, matches the Runtime identity,
and successfully loads the shadow application with writable state externalized.

The active Runtime and live wrapper remain unchanged.

Production remains unauthorized.

### PI-009A2 A2.3 Live Cutover

Runtime `7b171f135dc7` is now serving from its paired immutable source artifact.
Persistent application state is externalized under the macOS AIControlCenter
application data root. Repository source and repository-local DB state are no
longer part of the live execution boundary.

Production authorization remains separate.

### PI-009 Production Authorization

Runtime `7b171f135dc7` with source commit `7b171f135dc7882546bf7f733208778f1aef4943` is authorized for
Production under PI-009.

The authorization followed a clean final technical gate, immutable Runtime/source
validation, external persistent-state validation, HTTP validation and a
deployment regression result of 2337 passed with 5 deselected.

Production authorization is recorded as governance evidence; no operational
restart or reactivation was required.

### AI-PROVIDER-01C-B Candidate Validated

Candidate Runtime/source `102b8f1fa862`, bound to commit
`102b8f1fa8628d00d25575cb94538826a1a04e10`, passed canonical build,
immutable-source, and network-free FakeProvider workflow validation.
Production remains on `7b171f135dc7`; promotion requires separate explicit
AI-PROVIDER-01C-C authorization. Notion is `DEFERRED_UNTIL_FINAL_PHASE`.

### Production AI Provider Workflow

Production Runtime `102b8f1fa862` now executes the canonical AI provider path:

`BrainAgent -> ProviderRouter -> ProviderAdapter -> OpenAIAdapter`

The immutable Production artifact has passed a corrected authenticated workflow
validation. Persistent daemon credential wiring remains deferred to SEC-01.
