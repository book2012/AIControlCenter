# AI Home Datacenter Architecture

## PA-04 — Notification Platform v1

Status after Git closeout: `NOTIFICATION_PLATFORM_V1_VALIDATED`; PA-04 is
validated and closed. AIControlCenter owns notification intent, routing policy,
provider selection, governance, authorization, audit, retry policy, and the
future delivery lifecycle. External notification providers own transport
capability only. n8n, OpenClaw, WordPress, providers, and Ubuntu own neither
platform-wide notification business logic nor Production authorization.

`core.notifications` is the provider-neutral domain/platform boundary;
`integrations.notifications` contains replaceable observation-only provider
adapters; and `ops.macos.runtime.application` is the outer composition root.
Core imports neither `ops.*` nor `integrations.*`
(`CORE_OPS_IMPORT_COUNT=0`, `CORE_INTEGRATIONS_IMPORT_COUNT=0`). Provider and
routing statuses are separate: provider statuses are `AVAILABLE`,
`UNAVAILABLE`, `NOT_CONFIGURED`, `NOT_DEPLOYED`, `DEGRADED`, and `UNKNOWN`;
routing statuses are `PLANNED` and `BLOCKED`. V1 defines no actual delivery
lifecycle because provider execution is not implemented.

Observations normalize fail-closed. Only explicitly `AVAILABLE`,
`configured=true`, `available=true` providers are routable; malformed,
contradictory, exception-producing, mismatched, duplicate, or invalid providers
are not. Identities are bounded by `^[a-z0-9][a-z0-9._-]{0,63}$`; invalid
identities are never echoed and become literal `UNKNOWN`. Telegram is the known
reference provider: canonical truth is optional and `NOT_DEPLOYED`, while
configuration/readiness remain unknown unless explicitly observed. `DEPLOYED`
or `PRODUCTION` alone proves no availability, and no environment, credential,
endpoint, host, port, authentication, or network convention is inferred.

`core.capabilities.manifest` is the narrow shared canonical metadata lookup. It
validates its Draft 2020-12 schema and the manifest, requires exactly one
requested `service_id`, and fails closed for all invalid or unreadable input.
OpenClaw and n8n reuse it without changing PA-02/PA-03 outward behavior; it is
not a second `ServiceTopology` or lifecycle framework.

The exact new API is `GET /api/notifications/platform` and
`GET /api/notifications/providers`. It contains no action route, delivery,
retry, transport execution, Production authorization, or infrastructure
mutation. Existing `GET /notifications` and `POST /notifications` remain
unchanged and explicitly **LEGACY / OUTSIDE PA-04 SCOPE**; PA-04 does not call,
wrap, expand, authorize, or depend on them. Migration/deprecation is future,
separately governed work.

Final exact-code focused validation passed 85 tests after identity hardening;
the canonical regression passed `RC=0` on exactly one PA-04 invocation; and
`git diff --check` passed. No Production mutation, Production notification,
external provider I/O, or PA-04 execution occurred. Legacy POST was exercised
only by TestClient compatibility tests. No launchd, Docker, `runtime/current`,
credential, Caddy, WordPress, Ubuntu, or live-provider mutation occurred. No
Notion synchronization is claimed. OPS-01B and PA-01 through PA-03 remain
closed and unchanged. See
[`docs/architecture/PA-04-NOTIFICATION-PLATFORM.md`](docs/architecture/PA-04-NOTIFICATION-PLATFORM.md).

## PA-03 — n8n external automation capability boundary

Status after Git closeout: `N8N_CONTROL_PLANE_ADAPTER_V1_VALIDATED`; PA-03 is
closed. n8n is a replaceable external automation capability, not the
AIControlCenter Control Plane. AIControlCenter retains business logic, workflow
and orchestration policy, Production authorization, governance, audit,
deployment control, infrastructure mutation authority, and business/customer
state.

The final dependency direction is `ops.macos.runtime.application` →
`integrations.n8n` → `core.capabilities`, with dependency injection into
`core.api.create_app`. Core imports neither `ops.*` nor `integrations.*`.
Existing `core.capabilities` contracts and `CapabilityStatusService` are reused;
there is no second capability framework. Platform-neutral `create_app`
performs no n8n discovery and fails closed with value-free `UNAVAILABLE`
evidence when no adapter is injected. macOS outer application composition
injects the n8n adapter and truthfully projects `NOT_DEPLOYED`.

Canonical manifest/schema validation occurs before the unique n8n identity is
trusted. Current canonical truth is optional, `NOT_DEPLOYED`,
`runtime_health=false`, `runtime=UNASSIGNED`, and `supervisor=UNASSIGNED`. No
sufficiently proven executable, lifecycle, log, or runtime identity exists;
therefore PA-03 adds no PA-01 `service_platform` lifecycle definition.
Configuration, authentication, runtime, and transport remain `UNKNOWN` unless
explicitly injected as evidence. Implementation uses no invented n8n endpoint,
environment, or authentication convention.

The only PA-03 v1 API projection is `GET /api/capabilities/n8n`; no
POST/PUT/PATCH/DELETE capability implementation exists. PA-03 provides no
workflow execution, workflow enable/disable, webhook creation, credential
creation, schedule mutation, Production authorization, or infrastructure
mutation. Secret/config evidence is value-free: URLs, API keys, tokens,
cookies, headers, webhook secrets, environment values, configuration contents,
and exception messages are not projected. Shared governance explicitly states
`platform_business_policy_ownership=false` for external capabilities, and
PA-02 OpenClaw remains compatible.

Focused PA-03 validation passed 96 tests. The canonical deployment regression
passed with `RC=0` on exactly one PA-03 canonical invocation, and
`git diff --check` passed. No Production mutation or n8n workflow, credential,
Docker, launchd, `runtime/current`, or live-service operation occurred. No
Notion synchronization is claimed. OPS-01B, PA-01, and PA-02 remain closed and
unchanged.

## PA-02 — OpenClaw external capability boundary

Status after Git closeout: `OPENCLAW_ADAPTER_V1_VALIDATED`; PA-02 is closed.
OpenClaw is an optional, replaceable external capability, not a Control Plane.
AIControlCenter retains business logic, governance, Production authorization,
deployment control, workflow policy, infrastructure mutation authority, audit,
and business/customer state.

The final dependency direction is
`ops.macos.runtime.application` → `integrations.openclaw` →
`core.capabilities`, with the macOS outer composition injecting the adapter into
`core.api.create_app`. Core imports neither `ops.*` nor `integrations.*`.
Platform-neutral `create_app` performs no OpenClaw discovery and, without an
injected adapter, fails closed with value-free `UNAVAILABLE` evidence. The
macOS outer composition injects the adapter and truthfully projects
`NOT_DEPLOYED` from the schema-validated canonical manifest.

The canonical manifest identifies exactly one OpenClaw entry as optional,
`NOT_DEPLOYED`, and `runtime_health=false`; it is schema-validated before that
unique entry is trusted. No trustworthy launchd, runtime, or Service Platform
identity is proven, so PA-02 adds no `service_platform` lifecycle definition.
Endpoint, authentication, transport, and runtime identity remain
`UNKNOWN`/unproven by default. The implementation uses no `OPENCLAW_ENDPOINT`
or `OPENCLAW_API_KEY` convention.

The only API surface is `GET /api/capabilities/openclaw`; no
POST/PUT/PATCH/DELETE capability implementation exists. PA-02 v1 provides no
prompt forwarding, tool/action execution, lifecycle execution, Production
authorization, or infrastructure mutation. Secret/config evidence is
value-free: no endpoint URL, key, token, cookie, header, environment value,
credential value, or exception message is projected.

Focused PA-02 validation passed 79 tests. The canonical deployment regression
passed with `RC=0` on exactly one PA-02 canonical invocation, and
`git diff --check` passed. No Production mutation or additional deployment,
`launchctl`, `runtime/current`, credential, or live-service operation occurred.
No Notion synchronization is claimed. PA-01 and OPS-01B remain closed and
unchanged; WordPress and unrelated Shadow maintenance remain separate future
work.

## PA-01 — Control Plane Service Platform v1

Status after Git closeout: `CONTROL_PLANE_SERVICE_PLATFORM_V1_VALIDATED`;
PA-01 is closed.

PA-01 introduced Control Plane Service Platform v1. The canonical service
manifest is the service-definition source of truth, and `ServiceDefinition` is
a pure core service-level contract. `ServiceHealth` remains the sole owner of
aggregate runtime health, and `core` has zero direct `ops.*` imports.

The macOS outer composition is `ops/macos/runtime/service_platform.py`. Its
`inspect_platform_services()` composes `ServiceTopology.platform_services()`,
existing `ServiceHealth` launchd and heartbeat observation, strict filesystem
readiness, and immutable runtime/source validation. Filesystem contracts use
stable owner/group names resolved only at the macOS boundary. Exact file type,
symlink, mode, owner, and group validation remains fail-closed. Only `ENOENT`
is missing; other filesystem or identity inspection errors fail closed with
value-free evidence.

Canonical immutable `runtime/current` and Source validation reuses the existing
authoritative immutable-source validator and does not execute Production
worktree code. PA-01 lifecycle capability remains inspect-only. Dry-run may
describe bootstrap as planning metadata only, eligible only for `NOT_DEPLOYED`
with trusted launchd observation, ready filesystem, and immutable runtime/source
preconditions. It includes no authorization and performs no mutation, retry,
rollback, or kickstart.

Application Scheduler and canonical API were reference services without
changes to validated Production lifecycle behavior. The canonical API
entrypoint remains `ops.macos.runtime.application:app`; Shadow remains separate.
Final focused validation passed 94 tests under umask `077`. The final candidate
passed the canonical deployment regression with `RC=0` on exactly one canonical
invocation. `git diff --check` passed. No Production mutation occurred. No
Notion synchronization is claimed. WordPress and Shadow maintenance remains
deferred and separate.

## Immutable Production Source and canonical process recovery invariants

The Mac mini M4 remains the always-on Brain and sole Control Plane. Host Caddy
is the only public edge. WordPress is the CMS Engine, WooCommerce is the
Commerce Engine, and Ubuntu is an optional stateless infrastructure worker; it
owns no AI workload, application or business state, governance, authorization,
audit, deployment control, or Control Plane authority.

An active Production release is a paired identity:

- `runtime/venvs/<runtime-id>` contains the dependency Runtime.
- `runtime/sources/<runtime-id>` contains immutable tracked application Source.
- `runtime/current` selects the Runtime ID, and Runtime, Source, and approved
  full commit must agree exactly.

Immutable Source validation rejects both writable filesystem objects and
generated Python bytecode contamination, including `__pycache__`, `*.pyc`, and
`*.pyo`. Privileged Python executors that import project-local sibling modules
must set `sys.dont_write_bytecode = True` before those imports; environment
variables are defense in depth, not the sole protection. A contaminated
immutable release is retired and replaced by a newly built and independently
validated release. It is never repaired in place.

Production lifecycle control preserves strict read, plan, authorization, and
apply boundaries. One human authorization maps to one bounded mutation
invocation. Successful mutation followed by wrapper or observation failure
transitions to read-only reconciliation; it grants neither automatic retry nor
automatic rollback. Duplicate requests fail closed before authorization and
mutation if observed state no longer satisfies the expected precondition.
Authorization read inside a heredoc uses `/dev/tty`; expected-absence probes
must be safe under `set -e` and `pipefail`; generated wrapper redirections must
remain atomic; and JSON gates validate the actual emitted versioned schema.

Runtime health consumes `config/services/mac-standalone-production.json` as its
single service-topology contract. Logical identity, required/optional policy,
lifecycle, deployment state, and launchd labels are defined there; inspection
adapters only observe the lifecycle identifiers supplied by that contract.
Malformed topology fails closed. Runtime-health and scheduler-heartbeat reads
must not create, migrate, or update persistent state.

Endpoint-local success is not equivalent to whole-runtime health. A recovered
canonical API/Homepage may be operational while `/runtime/health` truthfully
reports degraded dependencies or stale heartbeats. Operational status must
preserve that distinction and must not promote HTTP status alone into a
platform-health claim.

## SHOP-AI-01A ProductDraft generation foundation

Status: `SHOP-AI-01A_PRODUCT_DRAFT_GENERATION_FOUNDATION_READY` at verified
implementation HEAD `52db3600ae76c70926e27ce930be70fe34f98452`.

`core/shopping/` remains the canonical Shopping domain and the existing SHOP-02
`ProductDraft`, `ProposedFields`, and immutable `ProductDraftRevision` model are
reused rather than replaced. The Shopping-owned structured generation contract
is version `1.0.0`. Generated fields carry AI `SuggestionProvenance`; the
candidate revision remains `LifecycleState.DRAFT` and causes no automatic
validation, human approval, or deployment intent.

The adapter reuses the canonical `core.providers.ProviderAdapter` with one
injected provider, `RetryPolicy(max_attempts=1)`, a bounded timeout, and no
provider fallback. Source context is canonicalized and snapshotted, and the
provider request ID remains traceable. The operation key is consumed before
provider invocation, providing **AT-MOST-ONE provider invocation per consumed
operation key within the injected coordinator's durability scope** and
concurrent duplicate suppression. This is not global exactly-once semantics.
The current `InMemoryProductDraftGenerationOperationCoordinator` is
non-production.

No durable ProductDraft persistence, durable operation ledger, transactional
revision/audit/operation Unit of Work, generation API, Dashboard mutation,
recommendation or ranking engine, WooCommerce write integration, Production
mutation authority, automatic retry, or automatic rollback was added. See
[`SHOP-AI-01A architecture`](docs/architecture/SHOP-AI-01A-PRODUCT-DRAFT-GENERATION-FOUNDATION.md).
Next: `SHOP-AI-01B_DURABLE_PRODUCT_DRAFT_GENERATION_TRANSACTION`.

## SHOP-01A reconciled Shopping baseline

SHOP-01A is retrospective baseline hardening over the existing SHOP-01/02/03
chronology. The canonical domain remains `core/shopping/`. At SHOP-01A1 HEAD
`f95ba9ae2133b55db06c362df321b16785f21423`, `/shopping` and the Shopping
dashboard share `build_default_shopping_service()`. The API is GET-only; one
read invocation permits one outbound HTTP GET attempt and automatic retry is
disabled.

The Mac mini M4 is the always-on Brain and AIControlCenter the single Control
Plane. WordPress is CMS/presentation, WooCommerce is the Commerce Engine, and
Ubuntu is a stateless infrastructure Worker with no Shopping business logic.
Production mutation authority is disabled. The intercepted
`WooCommerceControlledWriteAdapter` is retained library code, but no concrete
Production write transport, Production credential provider, runtime/API
wiring, or mutation endpoint exists. See the
[`SHOP-01A2 reconciliation`](docs/architecture/SHOP-01A2-REPOSITORY-UTILIZATION-AND-ARCHITECTURE-RECONCILIATION.md).

## SEC-02 Governance Control Plane

Status: `SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY`

The A0-A10 architecture phase is complete. Authorization follows only
`REQUESTED -> AUTHORIZED`, `REQUESTED -> REJECTED`, `AUTHORIZED -> STALE`, or
`AUTHORIZED -> CONSUMED`; `STALE`, `CONSUMED`, and `REJECTED` are terminal and
non-reusable. Current preconditions must `MATCH` before invocation permission.
Consumption is separate from invocation, and one orchestration permission
represents one bounded invocation. Remaining mutation budget is accounting
only, never retry authority.

`FAILED`, `UNCERTAIN`, `DRIFT`, failed postcondition, or failure evidence
produces `STOP`. There is no automatic retry or automatic rollback. Adapters
cannot authorize, widen scope or budget, retry, or roll back. Governance API
and dashboard projection is READ ONLY. See
[`docs/architecture/SEC-02A10-ARCHITECTURE-CLOSURE.md`](docs/architecture/SEC-02A10-ARCHITECTURE-CLOSURE.md).

SEC-02 freezes a reusable governance boundary under
`core/governance/control_plane/`, with pure domain rules, application-owned
orchestration and ports, bounded adapters, and a versioned contract family.
The canonical architecture is
[`docs/architecture/SEC-02-GOVERNANCE-CONTROL-PLANE.md`](docs/architecture/SEC-02-GOVERNANCE-CONTROL-PLANE.md),
the v1 semantic catalog is
[`docs/contracts/SEC-02-GOVERNANCE-JSON-V1.md`](docs/contracts/SEC-02-GOVERNANCE-JSON-V1.md),
and operator safety policy is
[`docs/operations/SEC-02-CONTROLLED-MUTATION-POLICY.md`](docs/operations/SEC-02-CONTROLLED-MUTATION-POLICY.md).

The Mac mini M4 remains the always-on Brain and AIControlCenter the sole Control
Plane. Ubuntu remains an optional stateless infrastructure Worker using bounded
JSON APIs; it owns no AI workload, business logic, application/governance/replay
state, authorization, or audit authority. SEC-02 creates no generic remote
command path. Existing deployment, governance-operations, and shopping domains
retain their business ownership and are wrapped through ports where useful.

SEC-02A is not a Production mutation implementation. No concrete Production
mutation adapter was implemented. Production mutation remains separately
human-authorized.

## AI provider boundary

AIControlCenter owns provider governance, routing, policy and normalization.
Business logic selects an explicit provider through `ProviderRouter` and talks
only to the replaceable `ProviderAdapter` contract; vendor SDK behavior belongs
behind adapters. Unknown and duplicate providers fail closed, retries are
bounded, and cross-provider fallback is prohibited. Credentials are external
secrets and API keys never belong in Git.

AI-PROVIDER-01A adds only a no-network OpenAI boundary and deterministic fake
adapter. AI-PROVIDER-01B is reserved for separately authorized credential
installation and authenticated connectivity. Production Runtime `7b171f135dc7`
and PI-009 authorization remain unchanged. Notion sync is `PENDING`. The
canonical decision is `docs/architecture/AI-PROVIDER-ADAPTER-ARCHITECTURE.md`.

AI-PROVIDER-01C-A integrates the existing canonical `BrainAgent.ask` workflow:
`BrainAgent -> ProviderRouter -> ProviderAdapter -> provider implementation`.
Provider selection is explicit from the request or configured Control Plane
policy. Business logic owns no vendor transport behavior, vendor objects cannot
cross the adapter boundary, unknown providers fail closed, and no automatic
cross-provider fallback occurs. This is repository-only; no authenticated call
or Runtime change occurred. 01C-B creates a Candidate Runtime and 01C-C requires
explicit human Production-promotion authorization. Notion is
`DEFERRED_UNTIL_FINAL_PHASE`.

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

## Canonical Runtime serving-target authority

The two canonical macOS launchd runners,
`ops/macos/launchd/run-shadow-api.sh` and
`ops/macos/launchd/run-shadow-daemon.sh`, are the serving-target authority.
Both runners must declare exactly one complete target and must agree on the
same value. The canonical production serving target is
`core.api.shadow:app`. The Shadow application composes the internal FastAPI
application exposed as `core.api.app:app`; that internal target is
diagnostic/composition-only and must never be selected as the direct
production serving target.

Runtime Contract discovery fails closed when either canonical launcher is
missing, conflicting, declares multiple targets, or provides a malformed or
abbreviated target. Only unanimous agreement on one complete launcher target
can produce a selected serving target. Health endpoint discovery retains only
valid path-shaped endpoints, removes duplicates, and emits deterministic
output. This discovery contract is read-only and grants no build, activation,
restart, launchd or Caddy mutation, public opening, Ubuntu change, production
write, or production authorization; production remains `NOT_AUTHORIZED`.

## RUNTIME-BUILD-04A release and source boundary

Source/documentation commit
`acd80ab9f6aeb848900e1a19e3fa3afd69face8a` produced side-by-side release
`acd80ab9f6ae`. Each finalized release owns its Python interpreter and installed
dependencies, so dependency releases are immutable and can coexist. The build
and validation completed without changing `runtime/current`, which remained on
active Runtime `b9ad351a7241`; the new release was not activated.

The canonical serving target is `core.api.shadow:app`. The Shadow application
is `ReadOnlyASGI` and composes the internal FastAPI application
`core.api.app:app`. Direct localhost shadow smoke ran from the new release and
confirmed HTTP 200 for `/health`, `/runtime/health`, `/homepage/status`,
`/homepage`, `/homepage/product-management`, and `/datacenter/status`, plus HTTP
405 for `POST /health`. Exact smoke PID cleanup and listener cleanup passed.

The current immutability boundary is narrower than a fully source-immutable
application release: Python and dependencies are release-owned, but application
source is loaded from the mutable repository through `PYTHONPATH`.
`source_bundled_inside_release` is false and `repository_source_binding` is
true. Source bundling, a source manifest, and source-independent launch remain
future architecture work.

The builder emitted a valid structured JSON report on stdout. The host wrapper
found no canonical build-report JSON file, so the report was recovered and
validated from the builder log. That persistence mismatch is operational
tooling debt, not a release failure. An unavailable optional host `rg` command
was likewise not a release defect.

This release evidence does not grant activation authority. Runtime activation,
rollback execution, service restart, public staging, production, and production
writes remain `NOT_AUTHORIZED`. No service, launchd, Caddy, Ubuntu, public, or
production change occurred. The Mac mini M4 remains the sole Control Plane;
Ubuntu remains an optional stateless infrastructure worker with no AI workload,
business logic, application state, or Control Plane authority.

## Verified test, Git identity, and immutable Runtime boundaries

The Mac mini M4 remains the always-on Brain and sole Control Plane; Ubuntu
remains an optional stateless infrastructure worker and owns no AI workload,
business logic, application state, or Control Plane authority.

Controlled bootstrap validation receives identities, authorization, permit,
and claim identifiers and digests only through an immutable
`TrustedBootstrapEvidenceBinding`. Missing, incomplete, inconsistent, or
self-asserted-only binding evidence fails closed. The
`ControlledBootstrapEvidenceGenerator` deterministically emits the exact
canonical 14-artifact non-production evidence set, and operational snapshots
consume the public `ControlledMacBootstrapExecutor` contracts. Historical
retained host evidence and fixed historical identities are not test
dependencies; writable test state is confined beneath `/private/tmp` with
restrictive permissions.

Repository identity observation is deterministic, file-backed, and strictly
read-only. Exact loose refs take precedence over exact `packed-refs` fallback;
detached full object IDs are supported, while symbolic resolution is bounded
and cycle-detected. Unsafe, malformed, abbreviated, missing, or ambiguous refs
fail closed. This boundary executes no subprocess and writes no Git metadata,
and inventory responses retain the sanitized error boundary.

Every new immutable Runtime release must atomically publish both
`metadata.json` and a valid lowercase full-SHA
`.aicontrolcenter-source-commit` marker before activation. Existing immutable
releases must never be patched in place, and installed services must never
reference the mutable repository `.venv`. A separately authorized new release
must be built and validated before an atomic `runtime/current` switch. These
contracts grant no Runtime build or activation, public access, or production
write authority; production remains `NOT_AUTHORIZED`.

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
      .aicontrolcenter-source-commit
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

The runtime identity contract consists of both `metadata.json` and
`.aicontrolcenter-source-commit`. The generator validates the full Git commit
as exactly 40 lowercase hexadecimal characters, then atomically publishes both
files before activation. The marker contains that commit followed by one
newline. Missing or invalid identity metadata fails closed. Existing immutable
releases are never repaired in place; a replacement runtime must be built from
committed Git source.

### Runtime Activation Gate

The canonical macOS Runtime builder has two explicit public modes and three
internal phases:

```text
--mode build
  Runtime Contract validation
  -> repository commit validation
  -> clean Git validation
  -> owned staging virtual environment
  -> dependency installation
  -> application import validation
  -> test suite
  -> metadata generation
  -> metadata schema validation
  -> atomic finalization as an immutable commit-specific release

--mode activate
  finalized release validation
  -> exact source-marker and metadata validation
  -> atomic runtime/current switch
```

Build mode cannot change `runtime/current`. Finalized releases are immutable;
an existing release fails closed and is never repaired or patched in place.
Activation is a distinct, explicit, independently authorized operation. An
invocation without a valid explicit mode fails closed, and the mutable
repository `.venv` is never an activation candidate.

Metadata or source-marker failure prevents finalization and activation. A
service restart is a further, separate operational gate and is performed by
neither mode. The Mac mini M4 remains the sole Control Plane. Ubuntu remains
an optional stateless infrastructure worker and owns no AI workload, business
logic, application state, or Control Plane authority. Production remains
`NOT_AUTHORIZED`.

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

## SHOP-02A Product Draft Boundary

AIControlCenter owns immutable ProductDraft revisions, validation, human review, authorization/audit references and non-executable deployment intent. WooCommerce remains commerce product truth; WordPress remains the CMS Engine; Ubuntu owns no workflow state. Approval is human-only and exact-revision-bound. `DEPLOYMENT_READY` is not deployment, and production writes remain `NOT_AUTHORIZED`. See `docs/architecture/SHOP-02A-PRODUCT-DRAFT-WORKFLOW.md`.

## SHOP-02B Product Draft Domain

The ProductDraft 1.0.0 domain is implemented under `core/shopping/product_drafts/` as immutable values and revisions with a pure, closed lifecycle evaluator. Exact revision concurrency and SHA-256 canonical-JSON idempotency are mediated through a replaceable repository port. Its only adapter is isolated in memory and is explicitly non-production. There is no mutation API, durable store, WooCommerce write, or production activation. SHOP-02C adds validation and human-approval application services next; production writes remain `NOT_AUTHORIZED`.

## SHOP-02C Product Draft Application Boundary

Application services under `core/shopping/product_drafts/application/` validate canonical immutable revisions and orchestrate REQUEST_REVIEW, APPROVE, REJECT, and REVOKE through the existing lifecycle evaluator. Authorization is replaceable and deny-by-default; accepted decisions require exact resource binding and HUMAN reviewers for decision operations. Deterministic audit references and command idempotency are instance-local and in-memory only. ProductDraft contracts remain 1.0.0. There are no mutation routes, Commerce writes, persistent stores, or production activation; production writes remain `NOT_AUTHORIZED`. SHOP-02D adds the read API and Dashboard projection next.
# SHOP-02D read boundary

ProductDraft query ownership remains in AIControlCenter. A replaceable `ProductDraftReadSource` supplies immutable snapshots to deterministic JSON-safe queries and the `product_draft_review` Dashboard projection. The default runtime source is safely unavailable, while an empty configured source is available with zero results. WooCommerce remains published product truth; this boundary has no writes or persistence and ProductDraft contracts remain 1.0.0.

## SHOP-03A controlled Commerce write architecture

Approved immutable ProductDraft revisions can now be evaluated into an immutable controlled write plan through explicit freshness, exact source/revision/intent binding, deny-by-default authorization, and instance-local idempotency. Only a deterministic fake/dry-run adapter exists. No API mutation route, persistent queue, network dependency, or real Commerce mutation exists. ProductDraft contracts remain 1.0.0; production writes are `NOT_AUTHORIZED`, and SHOP-03B is separately gated. See `docs/architecture/SHOP-03A-CONTROLLED-WOOCOMMERCE-WRITE.md`.
# SHOP-03B1 Commerce write adapter boundary

The ProductDraft deployment package owns the controlled WooCommerce write port without coupling to the existing read adapter. An immutable SHOP-03A plan carries its digest-bound proposed fields into an explicit WooCommerce allowlist. Credentials arrive from an injected call-time provider and never enter request metadata. A synchronous injected transport receives the safe request, credential value, and bounded timeout as separate arguments. No concrete transport exists; defaults fail closed.

Responses are reduced to allowlisted fields and deterministic digests, then reconciled as `MATCHED`, `MISMATCH`, `REMOTE_IDENTIFIER_MISMATCH`, `RESPONSE_INVALID`, `TRANSPORT_UNAVAILABLE`, or `CREDENTIAL_UNAVAILABLE`. No retry or compensating write exists. SHOP-03B1 is intercepted validation only and cannot claim `LIVE_APPLIED`.
## UI-01 presentation boundary

`GET /homepage` is a package-local HTML/CSS/JavaScript operator view on the
existing Homepage router. Presentation reads only `GET /dashboard`; Shopping,
ProductDraft, approval, deployment, and Commerce-write authority remain in
their existing owners. ProductDraft and deployment contracts are unchanged.
Public exposure remains pending OPS-01 and production writes remain
`NOT_AUTHORIZED`.

## UI-02 Product Management presentation boundary

`GET /homepage/product-management` is package-local presentation on the existing
Homepage router. It consumes only the three existing same-origin ProductDraft
GET resources. AIControlCenter retains lifecycle, validation, review,
deployment-intent, policy, and audit authority; WooCommerce retains public
Commerce truth and the browser has no business or write authority. There is no
public exposure or production activation. Next:
`OPS-01_STAGING_CADDY_AUTH_MONITORING`.

## Runtime Source Isolation Requirement

A production Runtime identity must identify both its Python dependency
environment and its application source.

The mutable AIControlCenter Git working tree must not be treated as the
production application-source artifact.

Target runtime layout:

`runtime/venvs/<runtime-id>`

and:

`runtime/sources/<runtime-id>`

must represent the same approved release identity.

The production wrapper must resolve application source from the immutable
runtime source artifact and must fail closed when source identity, runtime
identity, or expected commit do not match.

## PI-009A2 Runtime Source Isolation

PI-009A2 freezes a paired immutable Runtime artifact model:

- `runtime/venvs/<runtime-id>` — Python dependency environment
- `runtime/sources/<runtime-id>` — immutable tracked application source

`runtime/current` continues to select the venv Runtime identity.

The production wrapper must derive the matching source artifact from the same
Runtime ID and must require exact full source-commit agreement.

The mutable Git working tree is not a valid production application source.

## Immutable Live Runtime Boundary

The live AIControlCenter shadow service uses:

- Runtime: `runtime/venvs/7b171f135dc7`
- Source: `runtime/sources/7b171f135dc7`
- State: `~/Library/Application Support/AIControlCenter/data`

Mutable Git source and repository-local SQLite state are outside the live
application boundary.

## Production Authorization Boundary

PI-009 Production authorization is represented as governance evidence tied to
an exact immutable Runtime/source identity.

Production authorization does not mutate the immutable source artifact.

Current authorized deployment:

- Runtime: `7b171f135dc7`
- Source commit: `7b171f135dc7882546bf7f733208778f1aef4943`
- Runtime source: immutable
- Persistent state: external macOS application data root
- Control Plane: AIControlCenter on Mac mini M4
- Ubuntu role: stateless infrastructure worker

## AI Provider Candidate Deployment Boundary

AI-PROVIDER-01C-B produced the non-active deployment pair:

- Candidate Runtime: `runtime/venvs/102b8f1fa862`
- Candidate source: `runtime/sources/102b8f1fa862`
- Source commit: `102b8f1fa8628d00d25575cb94538826a1a04e10`

Candidate validation runs from the immutable source with matching Runtime
Python and external temporary state. FakeProvider is the network-free workflow
boundary. Candidate existence is not activation authority: Production remains
on `7b171f135dc7`, and AI-PROVIDER-01C-C requires separate explicit promotion
authorization.

## Production AI Provider

Active Runtime:

`102b8f1fa862`

Canonical Control Plane path:

`BrainAgent -> ProviderRouter -> ProviderAdapter -> OpenAIAdapter`

AIControlCenter owns provider selection, governance and business logic.

Vendor-specific transport remains isolated behind ProviderAdapter.

Automatic cross-provider fallback remains prohibited.

Persistent daemon credential delivery is owned by SEC-01.

# SEC-01C-R1 immutable-source repair

SEC-01C consumed two installs and one restart. Its frozen wrapper preserved secret injection but used mutable repository cwd and `PYTHONPATH`; HTTP recovery did not satisfy the immutable Production gate, and no automatic rollback occurred. The repository wrapper now dynamically pairs `runtime/venvs/<ID>` and `runtime/sources/<ID>` from `runtime/current`, verifies identity/content, preserves external data, isolates `PYTHONPATH`, enters immutable source, and uses Runtime Python `-P`. It is not installed by R1; the current live installation remains blocked pending new exact human authorization for replacement and one restart. Runtime `102b8f1fa862` has importable `jsonschema`; Notion remains `DEFERRED_UNTIL_FINAL_PHASE`.
# Security architecture update (SEC-01B)

Provider credentials follow [Protected File-Per-Provider Secrets with Deterministic Wrapper Injection](docs/architecture/PROVIDER-SECRET-DELIVERY.md): external protected storage, wrapper-owned validation/injection, and environment-backed adapter consumption. Business logic has no secret-file responsibility.

## SEC-01C Production secret delivery closeout

SEC-01C is `COMPLETE`; milestone `PRODUCTION_DAEMON_SECRET_DELIVERY_VALIDATED`.
After R1 restored immutable-source execution, R2 identified the workers config as
`VERSIONED_APPLICATION_CONFIG`, R3 froze its immutable-source binding without an
intended live mutation, R3Q stopped on precondition drift with zero edits and
restarts, and separately authorized R3Q2 performed one representation-only
worker.env correction plus exactly one restart. The daemon now has no mutable
repository source/config dependency, and provider-secret presence was validated
without value exposure or provider network calls. SEC-01 remains open; next is
SEC-01D Secret Lifecycle & Recovery Validation. Notion is
`DEFERRED_UNTIL_FINAL_PHASE`. See
[the closeout](docs/operations/SEC-01C-PRODUCTION-SECRET-DELIVERY-CLOSEOUT.md).

## SEC-01 Production provider-secret lifecycle architecture

SEC-01 is complete at `PRODUCTION_SECRET_LIFECYCLE_VALIDATED`. The Mac mini M4
is the always-on Brain and AIControlCenter is the single Control Plane. Ubuntu
remains an optional stateless infrastructure Worker consumed through JSON APIs;
it owns no AI workload, business logic, application state, governance,
authorization, or provider-secret policy. Operations remain headless and
Git-first.

Provider credentials use **Protected File-Per-Provider Secrets with
Deterministic Wrapper Injection**. The deterministic service wrapper validates
and injects protected provider files; business logic never reads secret files.
There is no `launchctl setenv` persistence, plaintext secret in a plist, or
silent cross-provider fallback. Missing or invalid provider material fails
closed, and no credential value or identifier belongs in documentation.

Production is immutably bound to Runtime `102b8f1fa862` and source
`/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/sources/102b8f1fa862`.
A desired state or staged candidate is not activation authority. Every
Production mutation requires explicit, scope-bounded human authorization; a
failed controlled mutation authorizes neither automatic rollback nor retry.

Authoritative reboot-crossing evidence belongs under
`/Users/kyouhan/Library/Application Support/AIControlCenter/governance/evidence/SEC-01`;
`/private/tmp` is not authoritative across reboot. Permanent exceptions are:

- `SEC-01D-B-REPEATED-RESTART-AUTHORIZATION-SCOPE-EXCEPTION`: D-B ran the
  restart workflow twice under authorization for exactly one. This was not
  retroactively authorized or erased, although Production remained healthy.
- `SEC-01D-C3-BOOT-PARSER-DEFECT`: greedy parsing captured `usec` instead of
  `sec`; the original reboot authorization became `STALE_UNCONSUMED`, and C3-R1
  corrected the parser before the authorized reboot.
- `SEC-01D-C5-EVIDENCE-RETENTION-DEFECT`: reboot evidence in `/private/tmp` was
  lost. C5-R2 used transcript-bound recovery. Exact reboot count was no longer
  machine-verifiable; the operator attested one reboot and boot epoch proved a
  reboot boundary. Lost C3/C4 files were not restored.

The final regression gate uses the canonical deployment harness
`ops/macos/validation/run-deployment-regression-gate.sh`. It provisions
`AICONTROLCENTER_GIT_EVIDENCE_TEST_ROOT`,
`AICONTROLCENTER_OPERATIONAL_EXECUTION_TEST_ROOT`, and
`AICONTROLCENTER_OPERATIONAL_LIVE_TEST_ROOT`, then forwards selectors with
`python -m pytest "$@"`. FINAL R1 bypassed that contract with raw pytest and
reported 2 failed, 2338 passed, 5 deselected, and 62 errors; it is retained as
`INVALID_RAW_PYTEST_GATE_INVOCATION`, not an application or documentation
failure. FINAL R2 diagnosed this read-only with no mutation. FINAL R3 passed
3/3 representative selections (17 tests) through the harness. Authoritative
FINAL R4 used the canonical harness and passed 2402 tests with 5 deselected and
437 warnings; warnings are not failures. Tests did not modify the repository,
Production PID was unchanged, canonical secret metadata was preserved, the
candidate was absent, and Production mutation was zero.

<!-- AIHD_RUNTIME_HEALTH_PRODUCTION_2026_08_13 -->
## OPS-01B Application Scheduler log readiness

Application Scheduler lifecycle readiness includes an explicit launchd log
contract. `/var/log/aicontrolcenter` must remain a real `root:wheel 0755`
directory. The Scheduler stdout and stderr paths must each be real,
non-symlink `kyouhan:staff 0640` files.

The existing `core.runtime.service_health.ServiceHealth` runtime-observation
projection receives this contract through its application composition adapter
and fails overall health closed when required Scheduler log readiness is
missing, invalid, or cannot be inspected. It imports no `ops.*` adapter.
The immutable Production runner launches `ops.macos.runtime.application:app`.
That outer macOS composition root injects
`application_scheduler_logs.inspect_contract` into the platform-neutral
`core.api.app.create_app(...)` factory; the core default remains fail-closed.
`application_scheduler_bootstrap.py` is the canonical Scheduler deployment
lifecycle gate. It consumes the same read-only log contract and performs the
service-registration eligibility probe in dry-run and apply modes. Apply alone
may issue exactly one bootstrap after all gates pass.
`application_scheduler_logs.py validate` exposes the same read-only contract.
Its separate bounded `provision` primitive may create only missing files;
it does not remediate an invalid existing object, invoke `launchctl`, retry,
roll back, bootstrap, or kickstart. Root identity is only a local execution
precondition, not human authorization. The outer governed executor owns and
must consume authorization immediately before each bounded Production
invocation.

Application Scheduler Production recovery was already operational before this
recurrence-prevention closeout. Focused recurrence validation passed. The first
canonical deployment regression invocation then failed with 13 test failures:
Scheduler fixtures were sensitive to the process umask, and one controlled-live
test hashed the independently mutable real-home AIControlCenter tree. Those
defects were corrected only in tests, without weakening Product contracts. The
corrected focused scope passed 39 tests under umask `077`, with the controlled
live root explicitly confined to `/private/tmp`. Because test changes followed
the first invocation, the canonical regression was invoked exactly twice; the
second invocation passed with `RC=0`. No canonical test count is asserted for
that passing invocation.

No Production mutation occurred during recurrence-prevention validation. No
additional activation, bootstrap, log provisioning, kickstart, retry, or
rollback was performed. OPS-01B recurrence prevention is validated, and
OPS-01B is closed. WordPress and Shadow work remain separate future work.

## Production Runtime Health Operational Contract — 2026-08-13

The Runtime Health model is deployed to Production release
`ed2424e39bb1`
(`ed2424e39bb12e363ae7a1967c677e661ae7ec0e`).

The Mac mini remains the AIControlCenter Control Plane.
The Production API lifecycle is owned by launchd service
`com.aicontrolcenter.api` and serves the canonical API on
`127.0.0.1:58081`.

The production service-topology projection is:

- `aicontrolcenter-api`: required, launchd-managed, `RUNNING`.
- `telegram`: optional and currently `NOT_DEPLOYED`.
- `application-scheduler`: required and currently `NOT_DEPLOYED`.
- Scheduler heartbeat: currently `STALE`.
- Topology contract: `VALID`.
- Aggregate Runtime Health: `healthy=false` until the required Application
  Scheduler is deployed and its heartbeat becomes fresh.

`healthy=false` in this state is an intentional truthful degraded-state
projection, not an API deployment failure.

The Homepage scheduler projection and the Runtime Health
`application-scheduler` lifecycle projection are different operational
concepts. An application-level scheduler status such as `ONLINE` must not be
interpreted as proof that the dedicated launchd Application Scheduler service
is deployed.

### Production ingress contract

Public ingress is:

`WAN :80/:443`
→ router forwarding
→ Mac Caddy `:58080/:58443`
→ canonical API `127.0.0.1:58081`.

Shadow `127.0.0.1:18100` is not a public Caddy upstream.

### Candidate-validation contract

A candidate release must be capable of Shadow validation without changing the
Production `runtime/current` pointer.

Release `ed2424e39bb1` was validated using a pinned ephemeral candidate lane on
`127.0.0.1:18101`, while the canonical API, existing Shadow and public ingress
remained unchanged.

Known deployment-tooling debt is tracked separately:

- the existing Shadow runner derives its effective Runtime/Source selection
  from `runtime/current` before its runtime-link override is processed;
- the legacy Shadow executor contains automatic external rollback behavior that
  does not match the current one-authorization/one-bounded-mutation governance
  model.

## PA-05 — WooCommerce Headless Adapter v1

PA-05 is validated at milestone
`WOOCOMMERCE_HEADLESS_ADAPTER_V1_VALIDATED`. AIControlCenter remains the sole
Control Plane and owner of shopping business logic. `core.shopping` is
authoritative for ProductDraft lifecycle, product policy, workflow,
recommendation, customer automation, governance, and business logic.
WordPress is CMS-only; WooCommerce is commerce-engine-only;
`integrations.woocommerce` is replaceable and read-only. The outer composition
root is `ops.macos.runtime.application`; core imports neither `ops.*` nor
`integrations.*` (`CORE_OPS_IMPORT_COUNT=0`,
`CORE_INTEGRATIONS_IMPORT_COUNT=0`).

The canonical Production manifest contains no WooCommerce service identity.
Absence is not interpreted as `NOT_DEPLOYED`: deployment, configuration, and
authentication remain `UNKNOWN`, catalog/API availability is unproven, and
the default capability status is fail-closed `UNAVAILABLE`. Lookup failures
that are missing, duplicate, malformed, schema-invalid, or unreadable invent
no `canonical_manifest` evidence. Validated manifest evidence is emitted only
when exactly one WooCommerce identity is returned successfully.

`core.capabilities` owns governance. Its reserved facts cannot be overridden
by integrations: `authority=AICONTROLCENTER`, `read_only=true`,
`production_authorization=false`, `infrastructure_mutation=false`,
`platform_business_policy_ownership=false`, and `action_execution=false`.
`CapabilityGovernanceExtensions` is typed and boolean-only; WooCommerce adds
only `commerce_engine_only=true` and `automatic_retry=false`.

The provider-neutral `UnavailableCapabilityObserver` consolidates unavailable
fallbacks. Platform-neutral `create_app` performs no WooCommerce, n8n, or
OpenClaw external discovery, preserving PA-02 and PA-03 outward fail-closed
compatibility. PA-05 exposes only `GET /shopping/providers/woocommerce`; it
adds no mutation endpoint or product, order, inventory, customer, coupon,
execute, retry, or Production mutation action.

Final focused validation passed 91 tests after the final architecture
correction. Canonical deployment regression passed `RC=0` and was executed
exactly once for PA-05. No Production WooCommerce request, WordPress or
WooCommerce mutation, Shopping SQLite mutation, external commerce I/O, or
Docker, launchd, `runtime/current`, Caddy, Ubuntu, credential, database,
plugin, or theme mutation occurred.

Next production sprint: `SHOP-CMS-01 — WordPress + WooCommerce Runtime
Foundation`. It will establish runtime, persistent-state, secret, backup,
health/readiness, manifest, and activation architecture before public
storefront exposure. This does not claim an existing Production
WordPress/WooCommerce runtime, public storefront availability, or Notion
synchronization.

## SHOP-CMS-01A — Runtime Foundation Phase A

SHOP-CMS-01A is validated and closed at milestone
`SHOPPING_RUNTIME_FOUNDATION_VALIDATED`. The Mac mini M4 owns the single
`shopping-runtime` lifecycle (`docker-compose-on-colima`, `NOT_DEPLOYED`);
WordPress and MariaDB are components, while WooCommerce is the hosted
`wordpress-plugin-commerce-engine` capability with
`activation_authorized=false`. AIControlCenter remains the sole Control Plane
and retains shopping business logic, governance, authorization, audit,
orchestration, and deployment control. Ubuntu remains stateless and owns no
shopping application or commerce state.

Phase A validated fail-closed read-only inspection, Mac-owned named volumes
`ai-shopping-wordpress` and `ai-shopping-database`, logical database export,
WordPress archive/checksum/metadata verification, loopback-only WordPress, no
MariaDB host port, separated untracked credentials, and bounded mutation
governance. Canonical #1 found only two stale service-count expectations
(`3151 passed, 2 failed, 5 deselected`); corrections passed targeted (2),
focused compatibility (47), and canonical #2 (`RC=0`). Exactly two canonical
invocations were used. Core direct outer-package import counts remain zero.

No Production, Docker, Colima, WordPress, WooCommerce, commerce database,
Caddy, or Ubuntu mutation occurred. No runtime, WordPress, MariaDB,
WooCommerce, storefront, Caddy storefront route, or Notion sync is claimed.
Next: `SHOP-CMS-01B — bounded Production runtime activation`, milestone
`SHOPPING_RUNTIME_ACTIVATED`; future storefront milestone
`SHOPPING_STOREFRONT_ONLINE_READ_ONLY`.

## SHOP-CMS-01B — Runtime Foundation activation phase correction

The desired shopping WordPress host port is `58082`, published only as
`127.0.0.1:${SHOPPING_WORDPRESS_PORT}:80`; MariaDB remains unpublished. The
runtime inspector derives reserved Control Plane ports from the canonical
service manifest. A healthy runtime that publishes WordPress on a reserved
Control Plane port fails readiness with `error_type=PortCollision`. The
ingress contract fixture derives the same `SHOPPING_WORDPRESS_PORT=58082`.

Compose inspection remains read-only and fail-closed. Its bounded parser
accepts a JSON array, one JSON object, NDJSON, or empty output; malformed,
scalar, or non-object content is rejected. A valid empty observation is
distinct from malformed inspection. Container health never proves
WooCommerce readiness; plugin/API and catalog readability require separate
read-only evidence.

One dedicated Colima-start authorization was consumed exactly once, and the
start succeeded. Subsequent reconciliation was read-only, not a new
Production mutation. Existing stored WordPress and MariaDB containers became
running/healthy under restart policy, with persistent volumes observed; this
was a side effect of the authorized Colima start, not an independently
authorized Compose up. The live WordPress publisher was observed on reserved
FastAPI port `58081` and is therefore `PortCollision`; the earlier REST 404
was FastAPI's response, not WordPress evidence. No cutover to `58082` has
occurred, shopping bootstrap secret files were absent, and WooCommerce
readiness remains unproven.

Canonical service and capability status remains `NOT_DEPLOYED`, and
`SHOPPING_RUNTIME_ACTIVATED=false`. Desired state is not activation authority:
the next operation is a separate human-authorized port cutover to `58082`,
followed by read-only reconciliation. WooCommerce bootstrap/readiness and
`SHOP-STOREFRONT-01` remain later work. AIControlCenter remains the sole
Control Plane; Host Caddy the sole public edge; Ubuntu remains stateless.
