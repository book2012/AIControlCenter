# Project History

## 2026-08-18 — Governed offline public-recipient intake boundary

SM-01B-02D-04A established recipient intake as a distinct governed mutation,
not a side effect of registration. External custody first supplies only an
already-public age recipient to the fixed Mac Control Plane inbox; a later
registration/validation action consumes a different fresh authorization,
mutation budget, execution request, and durable consumption record. This
separation prevents one authorization from silently covering two filesystem or
registration effects and preserves the one-human-authorization/one-bounded-
Production-mutation rule.

The private offline-recovery identity stays external because importing,
generating, storing, reading, or querying it on the Production Mac would expand
the Control Plane's custody and secret-exposure boundary unnecessarily. Python
receives only a typed, value-redacted public-recipient object, and durable
evidence contains no recipient value or private material.

The fixed inbox uses descriptor-relative, no-follow traversal and descriptor
metadata checks because pathname checks alone cannot prove that the validated
parent and leaf remain the objects mutated. Exclusive leaf creation identifies
the mutation boundary; fresh traversal plus parent and leaf `st_dev`/`st_ino`
comparison proves that the canonical path still names the actual created
object. Rebinding or any other post-creation ambiguity therefore becomes
`UNCERTAIN`, never `COMPLETED`, and triggers no automatic cleanup, retry,
rollback, compensation, or recovery.

This decision did not change the closed durable authorization-consumption
architecture. It performed no Production intake or filesystem mutation and did
not resolve historical MariaDB credential continuity. Implementation was
validated at `6e1aa0135b652b199f05a4911c0f45817a8529f4`; documentation closeout is complete, 04A is CLOSED, and 04B is next.

## 2026-08-13 — Canonical API recovery after immutable Source contamination

Release `9a7216a75323` reached canonical bootstrap exactly once, but canonical
process start exited with code `3`. Read-only validation reproduced
`SOURCE_ARTIFACT_WRITABLE:ops/macos/launchd/__pycache__`. Privileged Python
canonical refresh/bootstrap tooling had imported sibling modules before
bytecode suppression and created root-owned Python caches inside immutable
Production Source. The validator correctly failed closed. The contaminated
release was not repaired in place, and there was no automatic retry or
automatic rollback.

The repository remediation made both `canonical_api_daemon_refresh.py` and
`canonical_api_daemon_bootstrap.py` set `sys.dont_write_bytecode = True` before
project-local imports. Regression tests removed external bytecode-protection
environment variables and proved that neither executor creates `__pycache__`
nor `*.pyc`. Focused tests passed `49`; the canonical regression passed `2954
passed, 5 deselected, 439 warnings`. Checkpoint
`ef07532bd3d7ba91868d46375d48cac4821d6a56` was created and pushed before this
documentation closeout.

Runtime `ef07532bd3d7` and its matching immutable Source were each built
exactly once. Dependency installation, application import, full tests, and
independent Source validation passed. Runtime/Source identity matched the full
commit. Source content SHA-256 was
`2357749d768dfd8391a582669ae6b87b1f8e1c17cf477f5c505f47e051b15ce6`,
archive SHA-256 was
`b6cc292b95cc1327d35fcba0874bb7822f199ac15cf295226f7573bac3dcadbe`,
and Git tree was `2b157f1391cf34dd72c21cce6d5c82c212730bfd`. Writable object
count was zero, Python bytecode contamination remained absent before and after
service starts, and the ProductDraft main database digest remained unchanged
at `761d07099f051e2d1c934fce63fc66aee47bb052bf49138c220418c06ab604c4`.

The active pointer moved from `9a7216a75323` to `ef07532bd3d7` exactly once.
Shadow reconciliation ran exactly once; PID `37951` served from
`runtime/sources/ef07532bd3d7` with `GET /health = 200` and
`POST /health = 405`. Installed canonical runner and plist were byte-exact
with the new Source, with `root:wheel 0755` and `root:wheel 0644` metadata,
`RunAtLoad=true`, and `KeepAlive=false`. Canonical was registered but not
running, with runs `1` and previous exit `3`.

Exactly one separately human-authorized `launchctl kickstart` recovered the
canonical service. No second bootstrap, bootout, enable, or asset refresh was
performed. Canonical PID `38153` served from the new Source, returned the same
`200/405` health behavior, and launchd reported `running` with runs `2`. A
later duplicate recovery attempt reached only the operator wrapper: failed-state
preflight observed that canonical was already running and rejected the request
before authorization or mutation. Therefore no second canonical kickstart
occurred.

Public validation resolved `bokstory.duckdns.org` to `222.111.236.227`, saw
HTTP root redirect with `308`, and received `200` from HTTPS `/health` and
`/homepage/product-management`. Canonical API/Homepage recovery was complete.
Whole-runtime health was not: `GET /runtime/health` returned HTTP `200` with
`healthy=false`; API, Telegram, and scheduler status were `unavailable`; the
scheduler heartbeat was `STALE` and not fresh. The latest heartbeat reported
`ALIVE` at `2026-08-05T07:43:56.748515`. That degraded state remains explicit
follow-up operational debt.

Durable operator lessons from the recovery are:

1. One human authorization permits one bounded Production mutation invocation.
2. Successful mutation followed by wrapper or observation failure enters
   read-only reconciliation, never automatic retry.
3. Authorization prompts inside heredocs read from `/dev/tty`.
4. Expected-absence commands must not accidentally abort reconciliation under
   `set -e` or `pipefail`.
5. Shell redirection syntax in generated wrappers remains atomic.
6. JSON gates match the actual emitted versioned schema.
7. Immutable Production Source rejects generated bytecode contamination as
   well as writable objects.
8. Privileged Python executors disable bytecode before sibling imports.
9. Contaminated immutable releases are retired and replaced, never repaired in
   place.
10. Duplicate lifecycle requests fail closed before authorization or mutation
    when observed state no longer matches the expected precondition.

No ProductDraft generation, WooCommerce mutation, Ubuntu change, automatic
retry, or automatic rollback occurred.

## 2026-08-11 — SHOP-AI-01A ProductDraft generation foundation

Closed `SHOP-AI-01A_PRODUCT_DRAFT_GENERATION_FOUNDATION_READY` at verified
implementation HEAD `52db3600ae76c70926e27ce930be70fe34f98452`; canonical
regression was `2691 passed, 5 deselected, 437 warnings`. The milestone reused
the canonical Shopping domain, SHOP-02 ProductDraft and ProposedFields,
immutable revision candidates, and the canonical provider adapter. Contract
`1.0.0` prepares AI provenance-bearing candidates that remain `DRAFT`.

One injected provider is called with one attempt, a bounded timeout, and no
fallback. Source context is snapshotted and provider request IDs remain
traceable. Consuming the operation key before invocation provides at-most-one
provider invocation within the injected coordinator's durability scope and
suppresses concurrent duplicates. The coordinator is in-memory,
non-production, and does not establish global exactly-once semantics.

No durable persistence or operation ledger, transactional Unit of Work,
generation mutation surface, recommendation/ranking engine, WooCommerce write,
Production authority, retry, rollback, validation, approval, or deployment
intent was added. `SHOP-AI-01B_DURABLE_PRODUCT_DRAFT_GENERATION_TRANSACTION`
is next and begins with persistence/transaction architecture discovery.
`SHOP-REC-01A_RECOMMENDATION_ARCHITECTURE` remains separate. Ubuntu owns no
ProductDraft or AI application state.

## 2026-08-11 — SHOP-01A Shopping read-only foundation closeout

SHOP-01A closed at `SHOP-01A_SHOPPING_READ_ONLY_FOUNDATION_READY` after
SHOP-01A1 reconciled the GET-only runtime and SHOP-01A2 reconciled repository
utilization and architecture history. The verified SHOP-01A2 baseline HEAD is
`55270476e4b4e8d57c041084ff8eafda889c2660`; the canonical regression remains
`2670 passed, 5 deselected, 437 warnings` via
`ops/macos/validation/run-deployment-regression-gate.sh -q`.

The closeout preserves the existing SHOP-01/02/03 history and the intercepted
SHOP-03 adapter as non-Production `ACTIVE_LIBRARY` code. The Mac mini M4
remains the always-on Brain, AIControlCenter the single Control Plane and owner
of Shopping logic and Governance, Ubuntu a stateless infrastructure Worker,
WordPress the CMS/presentation boundary, and WooCommerce the Commerce Engine.
Shopping reads remain single-attempt and GET-only; Production mutation,
automatic retry, and automatic rollback remain disabled. No commit hash was
invented, no push occurred, and no external Notion synchronization occurred.
Next: `SHOP-AI-01A_PRODUCT_DRAFT_GENERATION_FOUNDATION`, reusing the existing
SHOP-02 `ProductDraft` work, followed by
`SHOP-AI-01B_DURABLE_PRODUCT_DRAFT_GENERATION_TRANSACTION`.

## 2026-08-11 — SHOP-01A2 retrospective reconciliation

SHOP-01A1 reconciled the GET-only runtime at HEAD
`f95ba9ae2133b55db06c362df321b16785f21423`; the canonical macOS validation
wrapper reported `2670 passed, 5 deselected, 437 warnings`. SHOP-01A2 then
classified repository utilization and reconciled the chronology of existing
SHOP-01, SHOP-02A/B/C, SHOP-03A, and SHOP-03B1 work. This milestone did not
restart or replace the Shopping domain and did not rewrite historical closeout
records.

The Mac mini remains the always-on Brain and AIControlCenter the single Control
Plane. WordPress remains CMS/presentation, WooCommerce the Commerce Engine, and
Ubuntu a stateless Worker with no Shopping business logic. Reads permit one
outbound GET attempt per invocation. The intercepted write adapter remains
library code, but Production transport, credentials, wiring, endpoints, and
mutation authority remain absent. Next: `SHOP-01A3_CLOSEOUT_AND_FINAL_SYNC`.

## 2026-08-10 — SEC-02A Governance Control Plane architecture ready

The A0-A10 SEC-02A architecture phase closed at
`SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY`, with the A1-A9 canonical
evidence chain `VALIDATED`. The milestone declares reusable Governance Control
Plane architecture readiness only. It does not enable a concrete Production
execution adapter, Production mutation, Shopping write automation, automatic
retry or rollback, or Ubuntu Governance authority.

The supplied canonical full repository regression was
`========= 2667 passed, 5 deselected, 437 warnings in 166.69s (0:02:46) =========`;
the prior focused Governance regression was `265 passed in 1.45s`. No tests
were rerun for this documentation closure. Git closeout will be performed by
the external controller. Notion actual external synchronization has not been
performed; documentation payload status is `READY_FOR_FINAL_SYNC`.

Next: `SHOP-01A_SHOPPING_PLATFORM_ARCHITECTURE_AND_READ_ONLY_FOUNDATION`, in
the sequence Architecture -> Product Domain -> WooCommerce READ-ONLY Adapter
-> Product Catalog API -> AI Draft Generation -> Recommendation -> Dashboard
-> Dry-run / Draft Workflow. Production commerce writes remain separately
governed and require explicit future authorization.

## 2026-08-10 — SEC-02A9 durable evidence and API projection validated

A9 added a pure immutable policy over caller-supplied storage facts and a
frozen, typed, value-free Governance read model. The deterministic projection
matches the unchanged A6 `GovernanceApiEnvelope`, preserves caller-supplied
time and safe references, and fails closed on invalid identity/count state.

Durable evidence is assigned to an operator-configured external Control Plane
data root. `/private/tmp` remains transient controller-report storage only;
Git-tracked evidence JSON remains canonical documentation/audit evidence and
not mutable runtime state. No user-specific external data-root path is
hard-coded.

Durable acceptance requires atomic write publication, restrictive permissions,
durable synchronization, manifest binding, and value-free evidence. No
filesystem persistence, concrete evidence adapter, SQLite, HTTP mutation route,
Production mutation API, Runtime/provider/Ubuntu access, authorization
mutation or consumption, execution, retry, rollback, or compensation was
added. External validation reported `265 passed in 1.45s` for the focused
Governance regression, validating the deterministic READ ONLY projection and
unchanged `GovernanceApiEnvelope` compatibility. This was not the full
repository regression. Milestone:
`SEC-02A9_DURABLE_EVIDENCE_AND_API_PROJECTION_VALIDATED`. Next:
`SEC-02A10 ARCHITECTURE CLOSURE REVIEW`. Notion remains
`DEFERRED_UNTIL_FINAL_PHASE`; architecture-ready is not claimed before A10.

## 2026-08-10 — SEC-02A8 orchestration policy validated

A8 added an immutable, deterministic application policy over existing A2-A5
domain facts. It returns only the next permitted disposition and imports or
invokes no Governance port or adapter. Failure evidence and exact binding,
lifecycle, current-precondition, consumption, budget, execution, and
postcondition blockers are evaluated before progress. Authorization
consumption and single invocation remain external coordinator boundaries.

Authorization consumption is a distinct gate, and current preconditions must
`MATCH` before invocation permission. Consumed authorization remains consumed
after later drift. One policy permission corresponds to one bounded
invocation. `FAILED`, `UNCERTAIN`, postcondition `FAIL`, and failure evidence
each produce `STOP`.

Every decision prohibits automatic retry and automatic rollback. Remaining
mutation count is accounting only and is not retry authority; no compensation
authority exists. Completed execution requires a matching postcondition, and
`PASS` permits closeout only.

External validation reported the focused Governance regression `231 passed in
1.42s`, reaching
`SEC-02A8_ORCHESTRATION_POLICY_AND_SAFETY_TESTS_VALIDATED`. This was not a full
repository regression. No Production,
Runtime, filesystem, network, subprocess, SQLite, Git-command, provider,
Ubuntu, environment, secret, clock, persistence, public mutation API, retry,
rollback, or compensation capability was added, and no Production, provider,
or Ubuntu mutation occurred. Next:
`SEC-02A9 DURABLE EVIDENCE AND API PROJECTION`. Notion remains
`DEFERRED_UNTIL_FINAL_PHASE`; no
`SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY` claim is made.

## 2026-08-10 — SEC-02A7 adapter ports and compatibility mappings validated

A7 added Governance-owned Protocol interfaces for typed precondition, Git, and
Runtime observations; audit and evidence persistence; exactly one bounded
external invocation; and read-only postcondition validation. Immutable,
declarative metadata classifies the existing deployment, audit, Runtime,
governance-operations, evidence-recovery, and Shopping boundaries without
importing or invoking operational code. Every concrete adapter remains absent.

Initial external validation reported `1 failed, 193 passed in 1.56s`. R1 fixed
the Protocol-only interface gate and classified the issue as
`PROTOCOL_RUNTIME_INIT_TEST_INSPECTION_DEFECT`. The diagnosis identified
test-inspection semantics—whether a Protocol class body explicitly declared
`__init__`—not implementation `__init__` semantics. The final focused
Governance regression reported `194 passed in 1.53s`, validating
`SEC-02A7_ADAPTER_PORTS_AND_COMPATIBILITY_MAPPINGS_VALIDATED`. This was not a
full repository regression. No Production,
Runtime, Ubuntu, provider, filesystem, network, subprocess, SQLite, secret, or
environment access occurred, and no orchestration, persistence implementation,
public mutation API, retry, or rollback was added. A7 contains abstract
Governance ports only and no concrete Production adapter. Adapters cannot
authorize, widen scope or mutation budget, or decide retry or rollback. Git
evidence remains read-only; Runtime identity remains observation-only;
Governance Operations remains operational audit/read-model only; Shopping
business rules remain Shopping-owned; and Ubuntu remains a stateless Worker
with zero Governance authority. Next:
`SEC-02A8 ORCHESTRATION POLICY AND SAFETY TESTS`. Notion remains
`DEFERRED_UNTIL_FINAL_PHASE`; no
`SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY` claim is made.

## 2026-08-10 — SEC-02A6 JSON Schema registry and contract tests validated

Implemented exactly 16 standalone Draft 2020-12 governance schemas with stable
URN identities and field shapes aligned to A2-A5 domain projections. A
deterministic local-package registry exposes the frozen v1 names, rejects
unknown names, rejects remote references, and returns isolated copies.

Added deterministic non-sensitive valid and invalid fixtures for every
contract and focused registry, schema, frozen-vocabulary, forbidden-field,
fixture, and model-projection tests. External focused governance regression
validated the registry and valid/invalid fixture contracts:
`173 passed in 1.39s`, reaching
`SEC-02A6_JSON_SCHEMA_REGISTRY_AND_CONTRACT_TESTS_VALIDATED`. This was not a
full repository regression.

The original R1 blocker was
`SEC-02A6-R1_CONTROLLER_REGISTRY_API_ASSUMPTION_DEFECT`: the controller
incorrectly assumed a public `registry.contract_names()` function although the
frozen contract required behavior, not that exact function name. It was not an
A6 contract implementation defect. This validation involved no Production,
provider, or Ubuntu mutation and no execution adapter. It added no Runtime
capability, authorization behavior, retry, rollback, public mutation API, or
Git mutation. Next: `SEC-02A7 ADAPTER PORTS AND COMPATIBILITY MAPPINGS`. Notion
remains `DEFERRED_UNTIL_FINAL_PHASE`; no
`SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY` claim is made.

## 2026-08-10 — SEC-02A5 receipt, failure, and evidence domain implemented

A5 added immutable models for atomic-consumption receipts, already-governed
execution requests, factual execution receipts, PASS/FAIL postcondition
reports, and fail-closed failure evidence. Caller-supplied counts preserve A4
invariants without status-driven rewriting. Consumption proves only the claim;
no receipt or report grants authorization, retry, rollback, or adapter action.

Value-free typed artifact references now compose deterministic manifests and
lifecycle-bound bundles. Duplicate identities and lifecycle drift fail closed;
artifact contents, raw payloads, secret material, paths, and generated hashes
are outside the model.

Three focused test modules were added but were not run by Codex. Therefore
`SEC-02A5_RECEIPTS_FAILURE_AND_EVIDENCE_MODELS_VALIDATED` remains a target
pending controller validation. This was pure domain evidence vocabulary only,
with no Production or Runtime access, execution adapter, orchestration,
persistence, audit storage, public mutation API, filesystem, subprocess,
network, SQLite, provider, Ubuntu, environment, secret, clock, ID, or digest
behavior. No SEC-02A architecture-ready milestone is claimed. Next: `SEC-02A6
JSON SCHEMA REGISTRY AND CONTRACT TESTS`. Notion remains
`DEFERRED_UNTIL_FINAL_PHASE`.

## 2026-08-10 — SEC-02A4 mutation budget domain implemented

A4 added immutable governance mutation budgets made from deterministically
ordered explicit capability line items. Each line item separately preserves its
allowed, actual invocation, completed, uncertain, remaining, and status
accounting. Duplicate or generic action types and invalid count relationships
fail closed instead of being repaired.

The pure transition from `AVAILABLE` to `CONSUMED` records irreversible
authorization consumption without implying an adapter call or changing a
counter. A separate pure operation accounts exactly one caller-reported
`COMPLETED`, `CONFIRMED_ZERO_EFFECT`, or `UNCERTAIN` boundary and exhausts only
the relevant line item until all line items are exhausted. Remaining count is
accounting only and creates no retry authority. An explicit caller-reasoned
safety incident can make a budget terminal `VIOLATED` while preserving counts;
it performs no compensation.

Three focused test modules were added but were not run by Codex. Therefore
`SEC-02A4_MUTATION_BUDGET_AND_INVOCATION_ACCOUNTING_VALIDATED` remains a target
pending external validation. This was pure domain work only, with no Production
or Runtime access, adapter, execution orchestration, persistence, evidence
storage, public mutation API, retry, rollback, filesystem, subprocess, network,
SQLite, provider, Ubuntu, environment, secret, clock, ID, or digest behavior.
No SEC-02A architecture-ready milestone is claimed. Next: `SEC-02A5 RECEIPTS
FAILURE AND EVIDENCE MODELS`. Notion remains `DEFERRED_UNTIL_FINAL_PHASE`.

## 2026-08-10 — SEC-02A3 precondition and stale domain implemented

A3 added an immutable `GovernancePreconditionSnapshot` and immutable named
bindings without collecting state or generating identities, timestamps, or
digests. Multi-valued categories normalize deterministically and reject
duplicate names. JSON-safe projection remains explicit and deterministic.

Pure comparison ignores recollection identity, time, and collector metadata but
binds lifecycle, request, target, Git, Runtime, security, manifests, operational
state, policy version, and canonical snapshot digest. It reports ordered
category-specific reasons. Before comparison, the issued authorization receipt
must match the expected lifecycle, request, and snapshot digest. Drift alone
uses the preserved A2 transition API to produce terminal `STALE`; match leaves
the original authority object and receipt unchanged. Caller-supplied time after
expiry similarly produces `STALE` with `AUTHORIZATION_EXPIRED`, while the exact
expiry boundary remains valid.

Focused tests were added but were not run by Codex. Thus
`SEC-02A3_PRECONDITION_SNAPSHOT_AND_STALE_SEMANTICS_VALIDATED` remains a target
pending external focused-test success. This is pure domain implementation only:
no Production or Runtime access, collector, adapter, persistence, accounting,
network, filesystem, subprocess, provider, Ubuntu, retry, rollback, public
mutation API, internal clock, random identity, or digest generation was added.
No SEC-02A architecture-ready milestone is claimed. Next:
`SEC-02A4 MUTATION BUDGET AND INVOCATION ACCOUNTING`. Notion remains
`DEFERRED_UNTIL_FINAL_PHASE`.

## 2026-08-10 — SEC-02A2 authorization domain models implemented

A2 implemented the frozen authorization lifecycle as pure immutable Python
domain models. It distinguishes requests from authority, approvals from
rejections, and authority-bearing receipts from rejected terminal state. The
single transition API returns new aggregate/state-record objects, preserves
caller-supplied UTC timestamps, and fails closed on illegal transitions,
terminal reuse, identity drift, scope widening, budget changes, and snapshot
digest changes.

Focused deterministic tests were added but were not run by Codex. Consequently,
`SEC-02A2_AUTHORIZATION_DOMAIN_MODELS_VALIDATED` is recorded only as the A2
target pending external test execution. No architecture-ready milestone is
claimed. No Production, provider, Runtime, Ubuntu, network, filesystem adapter,
persistence, execution, retry, rollback, budget-accounting, or precondition
comparison capability was added. Next:
`SEC-02A3 PRECONDITION SNAPSHOT AND STALE SEMANTICS`.

## 2026-08-10 — SEC-02A1 governance domain and JSON contract freeze

SEC-02 began by inventorying rather than replacing the repository's mature DPL
primitives. Deployment authorization, preflight, atomic permit claim, replay
protection, append-only audit SQLite, Git evidence, runtime identity, receipts,
and evidence validation already encode strong deployment-specific safety rules.
Replacing them would duplicate proven controls and blur ownership. SEC-02
therefore freezes a reusable governance domain and application port boundary
that wraps those capabilities while `core/deployment/*` retains deployment
business rules, `core/governance/operations/*` retains operational observation
and audit scheduling/read models, and `core/shopping/*` retains commerce
eligibility and write semantics.

A1 also records a critical distinction: authorization consumption and mutation
invocation accounting are not the same event. Atomic claim irreversibly changes
authorization to `CONSUMED`, even if no adapter boundary is subsequently
crossed. `actual_invocation_count` changes only when the bounded adapter call
boundary is crossed. Consequently, an unspent numeric remainder cannot restore
authority or permit retry. Failures after claim stop without automatic retry or
rollback and require manual inspection plus an entirely new authorization
lifecycle for any future attempt.

The freeze defines the exact five-state authorization lifecycle, four mutation
budget statuses, durable Mac Control Plane evidence rules, bounded adapters, and
16 v1 governance contract names/major field families. It adds no schemas or
Production mutation capability. Ubuntu remains a stateless bounded-JSON
infrastructure Worker and `/private/tmp` remains non-authoritative for durable
evidence.

`SEC_02A1_FINAL_STATUS=GOVERNANCE_DOMAIN_AND_JSON_CONTRACT_FROZEN`. Next:
`SEC-02A2 AUTHORIZATION DOMAIN MODELS`.

## 2026-08-10 — AI-PROVIDER-01C-A

The existing canonical `BrainAgent.ask` Control Plane workflow moved from the
legacy `ProviderManager.chat -> AIProvider.chat` call path to explicit
`ProviderRouter -> ProviderAdapter` invocation. Request/config provider
selection remains deterministic, unknown providers fail closed, and normalized
JSON results, errors and audit-safe metadata are the application boundary.
Injected legacy managers remain a compatibility seam only; no second agent or
workflow stack was created.

No authenticated provider request or network call occurred. Production Runtime
remained `7b171f135dc7`, with no service or operational-state mutation. 01C-B
will create a new Candidate Runtime and 01C-C requires explicit human
authorization for Production promotion. Notion is
`DEFERRED_UNTIL_FINAL_PHASE`.

## 2026-08-10 — SEC-01 production provider-secret lifecycle completed

SEC-01 closed at `PRODUCTION_SECRET_LIFECYCLE_VALIDATED` with Runtime
`102b8f1fa862` bound to matching immutable source. Protected
File-Per-Provider Secrets with Deterministic Wrapper Injection gives each
provider an isolated, fail-closed boundary while the wrapper, never business
logic, reads and injects protected files. This prevents secret access from
spreading into application policy, avoids `launchctl setenv` persistence and
plaintext plist material, and preserves explicit selection without silent
cross-provider fallback.

Immutable Runtime/source binding prevents Production from drifting onto mutable
repository source. Explicit human authorization exists because a desired state,
staged candidate, dependency, or recovery condition is not implicit authority
to mutate Production. Controlled mutation failure does not trigger automatic
rollback or retry.

Persistent daemon delivery and restart recovery were validated. Reboot recovery
closed as `VALIDATED_WITH_EVIDENCE_RECOVERY`. Missing-secret behavior failed
closed using the installed helper's supported `--secret-root` seam. Storage
rotation used exactly one atomic replacement and daemon rotation one authorized
E3 restart. Provider administration and candidate cleanup were validated;
previous credential revocation/deletion remains operator-attested. Provider
admin revocation was not machine verified, authenticated provider validation
was not performed, and credential identity was not proven locally. No secret
value or credential identifier belongs in documentation. Production was
healthy after E5 and the candidate `.next` file was removed.

The final quality gate required an audit correction. SEC-01 FINAL R1 invoked
raw pytest directly and reported 2 failed, 2338 passed, 5 deselected, and 62
errors. That invocation bypassed the canonical deployment regression harness,
so its required isolated test-root environment variables were absent. The
attempt remains recorded as `INVALID_RAW_PYTEST_GATE_INVOCATION`; it did not
demonstrate an application regression and documentation did not cause it. FINAL
R2 was `DIAGNOSED_READ_ONLY` and made no repository or Production mutation.

FINAL R3 used `ops/macos/validation/run-deployment-regression-gate.sh`, whose
contract provisions `AICONTROLCENTER_GIT_EVIDENCE_TEST_ROOT`,
`AICONTROLCENTER_OPERATIONAL_EXECUTION_TEST_ROOT`, and
`AICONTROLCENTER_OPERATIONAL_LIVE_TEST_ROOT` before forwarding selectors with
`python -m pytest "$@"`. All 3 representative selections passed, totaling 17
tests, with
`tests/deployment/test_m3_a4b2b2b_r1_existing_safe_parent.py` as the primary
module. Tests did not modify the repository and Production was not mutated.

SEC-01 FINAL R4 is the authoritative final regression gate. The canonical
harness—not raw pytest—reported 2402 passed, 5 deselected, and 437 warnings;
warnings are not failures. No application regression was demonstrated, tests
did not modify the repository, Production PID was unchanged, canonical secret
metadata was preserved, the candidate was absent, and Production mutation was
zero.

Permanent governance exceptions explain the recovery controls:

- `SEC-01D-B-REPEATED-RESTART-AUTHORIZATION-SCOPE-EXCEPTION`: D-B ran two
  restart workflows under authorization for one. It was not retroactively
  authorized, and Production health did not erase the exception.
- `SEC-01D-C3-BOOT-PARSER-DEFECT`: greedy parsing captured `usec` rather than
  `sec`; the original reboot authorization became `STALE_UNCONSUMED`, and C3-R1
  corrected the parser before the authorized reboot.
- `SEC-01D-C5-EVIDENCE-RETENTION-DEFECT`: C3/C4 evidence in `/private/tmp` was
  lost and not restored. C5-R2 used transcript-bound recovery. Exact reboot
  count was not machine-verifiable; the operator attested one reboot and boot
  epoch proved the reboot boundary.

The durable evidence root exists because temporary storage cannot carry
authoritative governance evidence across reboot:
`/Users/kyouhan/Library/Application Support/AIControlCenter/governance/evidence/SEC-01`.
The Mac mini M4 remains the always-on Brain and AIControlCenter the sole Control
Plane. Ubuntu remains a stateless JSON-API infrastructure Worker with no AI
workload, business logic, application state, governance, authorization, or
secret policy. SEC-01 completion does not complete the wider project. Next:
`SEC-02_CONTROL_PLANE_GOVERNANCE_AUTOMATION`.

## 2026-08-10 — AI-PROVIDER-01A

AIControlCenter established its first production-quality vendor-neutral
provider baseline in the existing `core/providers` subsystem. The platform now
owns provider governance, explicit fail-closed routing, normalized contracts
and audit-safe errors while replaceable adapters isolate business logic from
vendor SDK behavior. A deterministic fake adapter validates the boundary. The
OpenAI adapter checks the external `OPENAI_API_KEY` contract before an
invocation hook and includes no default network implementation.

No credential was installed or read and no authenticated provider call was
made. Production Runtime `7b171f135dc7`, its authorized source commit and
PI-009 authorization remained intact. AI-PROVIDER-01B was not started. Notion
synchronization is `PENDING`.

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
## 2026-08-06 — ACTIVATION-01B-C1 Complete

The versioned contract foundation for the read-only Activation
Inspector was completed.

Three Draft 2020-12 contracts were registered with canonical URN
identities. Synthetic fixtures validate policy-to-manifest,
report-to-policy, report-to-manifest and semantic report digest
bindings.

The focused gate passed `41` tests. The safe deployment
regression passed `1017` tests with `9` warnings.

Operational harness suites were deferred because isolated
test-root environment variables were unavailable. This is
tracked as test-infrastructure backlog, not as a C1 regression.

No Runtime, HTTP, service, launchd, Caddy, Ubuntu or Production
operation occurred.

Architecture base commit:

`dc482780fdd36ba50d4947e8193380d7426d8367`

Production remains `NOT_AUTHORIZED`.
<!-- AICONTROLCENTER:ACTIVATION_01B_C1_CLOSEOUT:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_ARCHITECTURE:START -->
## 2026-08-05 — ACTIVATION-01B Architecture Freeze

ACTIVATION-01B froze the architecture of a read-only Activation
Inspector after repository inventory and targeted review of the
existing deployment contracts.

The design reuses canonical JSON, SHA-256, JSON Schema Draft
2020-12, bounded Git evidence and macOS read-only adapter
patterns.

The Runtime Python probe is restricted to the exact isolated
invocation `<exact-runtime-python> -I -S --version`.

The only POST probe is a zero-body, one-attempt denial check
against `127.0.0.1:18100/health`, expecting HTTP `405`.

No implementation, host inspection, Runtime mutation, service
restart, rollback, Ubuntu operation, public opening or Production
authorization occurred.

Architecture predecessor commit:

`43975f6e26986fd91c9a715786e7c68deb63f612`
<!-- AICONTROLCENTER:ACTIVATION_01B_ARCHITECTURE:END -->

<!-- AICONTROLCENTER:ACTIVATION_01A:START -->
## 2026-08-05 — ACTIVATION-01A Architecture Decision

ACTIVATION-01A documented the atomic Runtime activation boundary without
performing an operational activation.

The decision binds candidate Runtime `acd80ab9f6ae`, active Runtime
`b9ad351a7241`, canonical serving target `core.api.shadow:app`, and
LaunchDaemon `system/com.aicontrolcenter.api.shadow`.

Runtime selection must use the existing atomic `runtime/current`
symlink-replacement mechanism. Service restart remains a separate gate
and may target only the exact loaded LaunchDaemon.

Failed activation validation does not authorize automatic rollback.
The previous Runtime target is rollback evidence only. Recovery requires
new, separately authorized human approval.

The candidate application source remains repository-bound through
effective `PYTHONPATH`, so it is not yet a completely independent
immutable application artifact.

No Runtime pointer, service, launchd, Caddy, Ubuntu or public-access
state changed. Production remained `NOT_AUTHORIZED`.

The architecture-and-runbook gate closed after the contract documentation commit `d14058553baa1dfc45e027a59ff580013584913b` was pushed and local/remote synchronization passed. This closure did not activate the candidate Runtime, restart a service, authorize rollback, open public access or grant Production authorization.
<!-- AICONTROLCENTER:ACTIVATION_01A:END -->

## 2026-08-05 — RUNTIME-BUILD-04A build, evidence recovery, and smoke

At source/documentation commit
`acd80ab9f6aeb848900e1a19e3fa3afd69face8a`, the build-only workflow created
side-by-side release `acd80ab9f6ae` while active Runtime `b9ad351a7241` and
`runtime/current` remained unchanged. Dependency installation and application
import passed. The Full Suite passed, source marker and metadata validation
passed, FastAPI was `0.139.0`, Uvicorn was `0.51.0`, and `jsonschema` was
available. The release was validated but not activated.

The builder produced a valid structured JSON report on stdout. The host wrapper
did not find a canonical build-report JSON file; the report was recovered from
the builder log and validated successfully. This is host wrapper/report
persistence tooling debt, not a product or release failure. An optional host
`rg` command was also unavailable; because it was optional, that was not a
release defect.

Direct localhost smoke started canonical `core.api.shadow:app`. Its
`ReadOnlyASGI` Shadow application composes internal FastAPI application
`core.api.app:app`. GET requests to `/health`, `/runtime/health`,
`/homepage/status`, `/homepage`, `/homepage/product-management`, and
`/datacenter/status` each returned 200; `POST /health` returned 405. Cleanup
terminated the exact smoke PID and confirmed listener cleanup.

The release owns Python and dependencies, but loads application source from the
mutable repository through `PYTHONPATH`; `source_bundled_inside_release` is
false and `repository_source_binding` is true. It is therefore not a fully
source-immutable application release. No service, launchd, Caddy, Ubuntu,
public, or production change occurred. Runtime activation, rollback execution,
service restart, public staging, production, and production writes remained
`NOT_AUTHORIZED`.

## 2026-08-05 — RUNTIME-CONTRACT-04A

Commit `637f5ee62ee7a5ac24c06afe9074811077cf0082`,
`fix(runtime): derive serving target from canonical launchers`, corrected
Runtime Contract discovery so the two canonical launchd runners, rather than
the set of discovered FastAPI objects, own serving-target selection. Both
runners must declare one complete target and agree on
`core.api.shadow:app`. The internal `core.api.app:app` target describes the
FastAPI composition behind the Shadow application and remains
diagnostic/composition-only; it is not eligible as a direct production serving
target. Missing, conflicting, multiple, malformed, and abbreviated launcher
targets all fail closed.

The same implementation retained only valid path-shaped health endpoints,
deduplicated them, and made their output deterministic. Targeted verification
passed 7 tests. Harness-only failures occurred before the successful isolated
Full Suite; they did not establish product or production failures. The final
isolated Full Suite passed 2281 tests, with 5 deselected and 437 warnings.

Runtime current remained `b9ad351a7241`. The previously built immutable
release `382ba887a045` was not activated, and no immutable release was built
from the RUNTIME-CONTRACT-04A commit. No Runtime activation, service restart,
launchd mutation, Caddy mutation, public opening, Ubuntu change, production
write, or production authorization occurred. Production remained
`NOT_AUTHORIZED`. The controlled continuation is documentation commit,
non-force push and remote verification, fresh Runtime Contract generation, new
immutable build-only, direct localhost `core.api.shadow:app` smoke, GET 200,
mutation 405, exact smoke PID shutdown verification, and a separate
activation/rollback gate.

## 2026-08-04 — RUNTIME-BUILD-02A and RUNTIME-BUILD-02B

The canonical macOS Runtime builder audit found a monolithic flow whose
successful execution unconditionally switched `runtime/current`. That coupled
dependency installation, release construction, validation, and activation,
preventing a build-only proof that preserved the active Runtime.

RUNTIME-BUILD-02A, commit
`5517fdb25a68c65f1bc8db03110900aa44ff173f`, replaced that flow with explicit
fail-closed BUILD/VALIDATE and ACTIVATE modes. Build owns a staging release,
installs dependencies only there, generates and validates metadata and the
exact source marker, and atomically finalizes an immutable release without
changing `runtime/current` or patching existing releases. Activation separately
revalidates a finalized release and Runtime Python before the atomic current
switch; it installs nothing and performs no service or `launchctl` action.
Targeted verification passed 18 tests. Main and standalone Full Suites each
passed 2270 with 5 deselected, reporting 437 and 435 warnings respectively.

The refactor introduced a product regression: the canonical builder's Git mode
changed from `100755` to `100644`. During correction, an initial host gate read
`git ls-files` index mode before the executable change had been staged and
reported a blocker. That was a host verification sequencing error, not another
product defect. Correct verification checked the executable worktree, then the
staged index, committed tree, and standalone clone.

RUNTIME-BUILD-02B, commit
`f8f2890178c78862cff53362fd167982fa672c99`, restored Git mode `100755` without
changing builder bytes and added a deterministic executable-bit regression
test. Main and standalone targeted runs each passed 19 tests. Main and
standalone Full Suites each passed 2271 with 5 deselected, reporting 437 and
435 warnings respectively; all four mode surfaces verified `100755`. No real
Runtime build, activation, `runtime/current` change, existing-release change,
service restart, `launchctl` or Caddy operation, push, or production
authorization occurred. Production remained `NOT_AUTHORIZED`.

## 2026-08-04 — TEST-INFRA-02 through Runtime source-marker verification

`TEST-INFRA-01` ended blocked because its harness depended on retained host
evidence and fixed historical identities. That was a test-infrastructure
failure, not a product defect. `TEST-INFRA-02` replaced that dependency with an
immutable trusted evidence binding and deterministic exact 14-artifact
non-production generator. Commit
`95f2f9d7b302428889d28e377fece3deb33eaf8e` passed 4 generator-focused tests,
3 factory-focused tests, 74 clean-room targeted tests, and a clean-room Full
Suite of 2244 passed, 5 deselected, with 437 warnings.

Verification from a detached worktree then exposed a harness limitation: Git
identity observation did not resolve the repository state presented there.
Diagnosis isolated an actual product defect in exact ref discovery: the
file-backed observer lacked correct `packed-refs` fallback. `FIX-GIT-01`, commit
`2bf553a733c3cb4c1d1b147f598fc7b696bd0318`, corrected loose-ref precedence,
exact packed-ref lookup, detached full-SHA handling, and bounded symbolic-ref
resolution without subprocesses or metadata writes. Both focused phases passed
27 tests; the main pre-commit Full Suite was 2257 passed, 5 deselected, with
437 warnings, while standalone commit verification was 2251 passed,
5 deselected, with 435 warnings. Thus the detached-worktree constraint was a
harness limitation, while the packed-ref behavior was a product defect.

Commit `52f896f085186dc7fef65106942980d2cdaaf8ef` then added the atomic immutable
Runtime source commit marker and fail-closed activation requirement. Runtime
focused verification passed 15 tests; the clean main and standalone Full
Suites each passed 2257 with 5 deselected, reporting 437 and 435 warnings
respectively. No existing release was patched, and no Runtime build,
`runtime/current` switch, service, launchd, Caddy, push, public opening, or
production authorization occurred. Production remained `NOT_AUTHORIZED`.

## 2026-08-04 — OPS-01B-R5-R3A

Closed the source-identity metadata gap without touching production. Runtime
metadata generation now validates an exact lowercase full Git SHA and publishes
`metadata.json` with `.aicontrolcenter-source-commit` as one fail-closed
operation before symlink activation. The Shadow daemon remains the consumer and
rejects missing or invalid markers. Existing immutable releases remain
untouched; a new release must be built from committed Git source under a
separate gate.

## M4-A3 test-only authorization simulation

M4-A3 began from synchronized commit
`05a6cd5d61bc16b973b2ea634aa435b020ef0705` after M4-A1, M4-A1R1, and M4-A2
closed. It added immutable contracts, injected clock/seed IDs and digests, a
seven-step evidence chain, test-only artifact factory, in-memory one-use claim
guard, fail-closed validation, confined reporting, and live-boundary rejection.
All five capabilities were simulated independently. No real authorization,
operational permit, claim, writer, monitoring, dispatch, notification, Ubuntu
action, command, restart, API write, or activation occurred. Production remains
`NOT_AUTHORIZED`; `.env` was not required or read. Decision:
`READY_FOR_READ_ONLY_OPERATIONAL_OBSERVATION`; 427 warnings remain backlog.

M3-A4B2B2B-R4 repaired two defects found after strict artifact normalization
in an authorized attempt that stopped `BLOCKED_PRE_AUTHORIZATION`: the required
Ubuntu non-participation evidence was rejected generically, and permit issuance
returned an untyped mapping. A narrow exact-false preflight contract and frozen
typed permit boundary now pass test-confined orchestration. Actual managed
targets remain absent and operational counters remain zero. Fresh approval is
required for R4; production is `NOT_AUTHORIZED`.

The first R3 recovery remained blocked because concrete clean/synchronized Git
evidence was absent. Recovery-2 added the sole narrow deployment subprocess
exception for fixed read-only Git observations and independently exercised the
existing inspectors, PRE_ACTIVATION monitor, and preserved failure evidence.
Actual bootstrap remained `NOT EXECUTED`; production stayed `NOT_AUTHORIZED`.

The previous M3-A4B2B2B-R3 attempt ended `BLOCKED_PRE_AUTHORIZATION`. Recovery
completed the reviewed default composition and mandatory pytest-only
end-to-end scenario without removing a gate. The validation runner stayed
validation-only, the live runner now uses the dedicated composition root,
actual managed targets stayed absent, and the actual operation stayed
`NOT EXECUTED`. Fresh approval must bind the recovery commit; production
activation remains `NOT_AUTHORIZED`.

## M3-A4B2B1A — closed after validation

The review-only operational permit issuance control package is available.
Identities and acknowledgements remain not provided and every operational
action remains at zero. Production activation remains NOT_AUTHORIZED.

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
# M3-A4B2B1B

Closed the human approval and permit issuance decision boundary after
validation. Synthetic dual-identity approval and synthetic in-memory permit
issuance were validated. The real review remains DENIED because the independent
approver, independent approval and independent restriction acknowledgement are
missing. No live permit, claim, bootstrap execution or production activation
occurred.
# M3-A4B2B2A

M3-A4B2B1C issued one operational permit. It remained unclaimed and was not
read, changed or deleted by this increment. It expires or will expire unused
and becomes invalid after the M3-A4B2B2A commit. M3-A4B2B2A closed after
test-only validation; controlled operational execution did not occur.
# M3-A4B2B2B-R1

The initial attempt stopped before permit issuance. Read-only recovery found
`ROOT_EXISTS_SAFE_PARENT_CANDIDATE`. Compatibility now preserves the existing
shared parent and unrelated siblings while retaining strict managed-target
absence. No operational execution occurred; fresh approval is required.
# M3-A4B2B2B-R2

The prior attempt stopped `BLOCKED_PRE_PERMIT`; both blockers were retained as
default-deny protections and resolved through an explicit reviewed activation
authorization boundary. Actual operational state remains unchanged.
# M3-A4B2B2B-R5

The latest operational attempt reached authorization and typed permit issuance
but stopped before claim because all 18 full-evidence digests crossed an exact
two-warning boundary. R5 separates and binds those contracts. The forensic
root is preserved and the actual bootstrap remains not executed.

# M3-A4B3

The separately authorized controlled non-production bootstrap succeeded once
at `f7a81b73b86c170300bb6b80f437dbb753362f7e`. Authorization
`m3-a4b2b2b-r2-60cc9ee1f8cf6c9a55a97cea3224786d`, permit
`m3-a4b2b2b-r4-permit-a72d2e43cc42cf05150884e95919d4b7`, and claim
`m3-a4b2b2a-claim-ef74c0c861feb6868e45999396e6f6db` are cross-bound.
Audit and replay are `HEALTHY` with zero events; two backups and isolated
restores validate. The shared parent and siblings were preserved. The permit is
consumed; runtime activation and production authorization did not occur.

# M3-A4C controlled activation validation

M3 closed from bootstrap `f7a81b73b86c170300bb6b80f437dbb753362f7e`
and recovery validation `0f23abdf362965c09db5f4f35483cbff47853643`.
Audit and replay remained `HEALTHY` with zero events, isolated restores passed,
and operational state remained unchanged. All activation, Ubuntu, and
production capabilities remain false; 427 warnings remain separate backlog.

# M4-A1 controlled activation architecture

M4 began at M3 closeout commit
`89d10da82545e6cfd173085719076bb71e14c120` with architecture-only work.
AIControlCenter now owns a typed closed registry, immutable deterministic state
machine, default-deny policy, canonical planner, and validation facade for five
independently governed capabilities. No authorization, permit, claim, writer,
monitoring runtime, dispatch, Ubuntu action, command, API write route, or
production activation occurred. The architecture decision is
`READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS`; M4-A2 remains future work. The
427 warnings remain a separate backlog track.

# M4-A2 capability authorization contracts

M4-A1 and M4-A1R1 closed before M4-A2 began at
`cbeb20d41808ea615b08196b164d6b5578486ed8`. M4-A2 introduced immutable,
canonical, independently approved contracts for exactly one registry capability
at a time. Exact Git and readiness bindings, independent identities, complete
restrictions, capability dependencies, UTC-aware bounded windows, and SHA-256
tamper binding now fail closed.

The resulting grant is only a deterministic test plan. No real authorization,
permit, claim, writer, monitoring runtime, dispatch, Ubuntu action, runtime
command, API write route, or production activation occurred. Production remains
`NOT_AUTHORIZED`; `.env` and endpoint secrets were not required. Decision:
`READY_FOR_TEST_ONLY_AUTHORIZATION_SIMULATION`. The 427 warnings remain
separate backlog.
## AUTO-01 autonomous delivery controller architecture

AUTO-01 began from clean synchronized commit
`873ad5cc8fcbf2cb48bd3205ce1ee6451c5338ec` after M4-A3 closed. It established
AIControlCenter as the sole autonomous-delivery Control Plane and Codex as a
bounded replaceable executor. The increment is deterministic planning only:
there is no persistent runner, service, subprocess, authorization, permit,
claim or activation. The decision is
`READY_FOR_PERSISTENT_RUNNER_ARCHITECTURE`; AUTO-02 is next. Production remains
`NOT_AUTHORIZED`; the existing 427 warnings remain separate backlog.

<!-- SHOPPING-FIRST-REPRIORITIZATION:BEGIN -->
## 2026-07-31 — Infrastructure Depth Review

The project identified that deployment governance work had moved too
far ahead of the original Shopping Platform objective.

The completed deployment, authorization, evidence and AUTO-01
architecture foundations were retained. Further autonomous runner and
controlled-activation expansion was deferred.

The project returned to the product sequence:

Shopping Platform → AI Integration Platform → Personal AI Assistant.
<!-- SHOPPING-FIRST-REPRIORITIZATION:END -->

<!-- SHOP-00-CLOSEOUT:BEGIN -->
## 2026-07-31 — Shopping Platform Product Track Restored

The repository inventory found that the Shopping foundation,
WooCommerce read integration, normalized JSON contracts, governance,
health monitoring, read API and storefront were already implemented.

The project prohibited duplicate adapter work and selected a
management-facing product view as the first new vertical capability.

Validated baseline:

- SRI commit: ba6fdb6a69ee9398b44fdd0810102b078c38c7f8
- SHOP-00 baseline: 93a8125d97d7c32347fa757c7a8af7e0cb47eeb5
- Shopping targeted regression: 292 passed
- mutation routes detected: 0
<!-- SHOP-00-CLOSEOUT:END -->

<!-- SHOP-01B-MANAGEMENT-READ-MODEL:BEGIN -->
## 2026-07-31 — SHOP-01B Management Projection

The first incomplete Shopping product capability was implemented as a
pure application read model.

The module consumes the existing Shopping service and produces
operator-facing JSON without introducing a new product store,
WooCommerce dependency, UI framework or write capability.

Next integration boundary:

`ShoppingManagementReadModel`
→ optional `DashboardAPI` dependency
→ `/dashboard.shopping_management`
<!-- SHOP-01B-MANAGEMENT-READ-MODEL:END -->

<!-- SHOP-01C-DASHBOARD-INTEGRATION:BEGIN -->
## 2026-07-31 — Shopping Management Dashboard Vertical Slice

The Shopping management read model was integrated into the existing
AIControlCenter Dashboard JSON surface.

The integration did not add a frontend framework, product database,
WooCommerce adapter dependency or write operation.

Shopping failures are represented as a safe `UNAVAILABLE` projection
rather than causing the Control Plane Dashboard to fail.
<!-- SHOP-01C-DASHBOARD-INTEGRATION:END -->

<!-- SHOP-01D-CLOSEOUT:BEGIN -->
## 2026-07-31 — SHOP-01 Product Management Milestone

AIControlCenter completed its first management-facing Shopping product
vertical slice.

Operators can consume normalized product, inventory, health,
readiness and integration state through the existing Dashboard JSON
surface.

The milestone reused the existing WooCommerce read foundation and did
not introduce another adapter, product database, frontend framework or
write path.

The next phase is Product Draft Workflow architecture. Draft state
will belong to AIControlCenter, while WooCommerce remains the
authoritative Commerce Engine.
<!-- SHOP-01D-CLOSEOUT:END -->

<!-- SHOP-01E2-COMPATIBILITY-ADAPTER:BEGIN -->
## 2026-08-01 — Shopping Management Contract Recovery

Operational diagnostics found that the default Mock adapter returned
the original Shopping `Product` shape, while the new management read
model consumed the canonical snapshot-oriented product shape.

The project resolved the mismatch with an explicit application
anti-corruption adapter rather than weakening the canonical contract
or adding translation logic to the Dashboard.
<!-- SHOP-01E2-COMPATIBILITY-ADAPTER:END -->

<!-- SHOP-01E3C-SECURE-RUNTIME:BEGIN -->
## 2026-08-01 — WooCommerce Read Foundation Operationally Validated

AIControlCenter authenticated to the canonical WooCommerce target with
a read-only key and successfully executed authenticated and public GET
requests.

The target matched the configured Shopping site. All product states
were empty, while one product category existed.

The platform introduced a secure reusable credential loader instead
of storing secrets in LaunchAgent environment variables. Product
workflow development can now proceed independently of catalog
population.
<!-- SHOP-01E3C-SECURE-RUNTIME:END -->

## 2026-08-01 — SHOP-02A

Closed the SHOP-01E read foundation and completed the ProductDraft architecture without runtime or external writes. SHOP-01E3D persistent activation remains deferred. The design binds human approval to an immutable revision and separates deployment readiness from execution. WooCommerce still reports zero products and one category; draft development is independent. SHOP-02B is next.

## 2026-08-02 — SHOP-02B

Completed the ProductDraft 1.0.0 immutable domain, pure lifecycle evaluator, exact-revision concurrency, canonical-JSON SHA-256 idempotency, repository port, and isolated in-memory adapter. No API mutation route, persistent storage, WooCommerce write, or activation was added. Production writes remain `NOT_AUTHORIZED`; SHOP-02C validation and human approval application service is next.

## 2026-08-02 — SHOP-02C

Completed deterministic ProductDraft validation and revision-bound human review application services. Authorization is deny-by-default, accepted APPROVE/REJECT/REVOKE decisions are HUMAN-only and exact-revision-bound, and audit/idempotency adapters remain in-memory and non-production. ProductDraft contracts remain 1.0.0. No API mutation routes, WooCommerce writes, persistent storage, or activation were added. Production writes remain `NOT_AUTHORIZED`; SHOP-02D read API and Dashboard projection is next.
# SHOP-02D ProductDraft read delivery

Completed the AIControlCenter-owned ProductDraft read/query layer, three GET-only Shopping resources, and failure-isolated `product_draft_review` Dashboard JSON. The production default is explicitly unavailable and does not pretend an in-memory snapshot is durable; an injected empty source returns an available empty result. ProductDraft contracts remain 1.0.0. No mutation API, WooCommerce write, persistent storage, or production activation was introduced. SHOP-03 controlled WooCommerce write architecture follows.

## 2026-08-03 — SHOP-03A

Completed the controlled Commerce write architecture for exact approved immutable ProductDraft revisions. Eligibility, freshness, authorization, controlled-plan hashing, successful-plan idempotency, fake/dry-run port execution, and JSON-safe preview are deterministic and caller-clocked. ProductDraft contracts remain 1.0.0. There is no API mutation route, persistent queue, real WooCommerce adapter, live write, or production authorization; SHOP-03B is separately gated.
# 2026-08-03 — SHOP-03B1

The user-attested SHOP-03B program authorization permitted architecture, implementation, and intercepted validation. AIControlCenter completed the production-grade adapter contract and credential boundary without external requests or live Commerce writes. No exact product/revision execution authorization was bound, no concrete network transport or API mutation route was added, and production activation remained `NOT_AUTHORIZED`.
## UI-01 internal Homepage complete

AIControlCenter gained its first real browser Homepage at `GET /homepage` for
internal, read-only Shopping operations. Package-local HTML, CSS, and JavaScript
consume only same-origin `GET /dashboard`, with bounded timeout and safe retry.
No frontend framework, public Caddy exposure, authentication change, mutation
API, live Commerce write, or ProductDraft/deployment contract change occurred.
Public opening remains pending OPS-01; UI-02 Product Management Console is next.

## UI-02 internal Product Management Console complete

Added the internal, responsive ProductDraft console at
`GET /homepage/product-management`. Its bounded presentation reads only the
existing same-origin collection, current-revision, and exact-revision GET APIs.
No ProductDraft/dashboard implementation or contract changed; no external
request, Commerce write, public exposure, Ubuntu change, or production
activation occurred. Next: `OPS-01_STAGING_CADDY_AUTH_MONITORING`.

## PI-009A1 Deployment Test Gate Repair

The first PI-009 deployment regression reported 1032 passing tests,
18 failures and 17 errors.

The failures were traced to dependency architecture classification,
package-relative import analysis, macOS temporary-path canonicalization,
and controlled-bootstrap `/private/tmp` test confinement.

After repair, the complete deployment suite passed:

`1133 passed, 9 warnings`

Repair commit:

`fe0e89af58c28d8b72b47c4c4e2f8fa86cc5739c`

No Runtime, service, Caddy, Ubuntu or Production mutation was performed.

PI-009A1 closed with `RUNTIME_SOURCE_ISOLATION` as the remaining technical
Production blocker.

## PI-009A2 Architecture Decision

Runtime source isolation investigation confirmed:

- no `pyproject.toml`
- no `setup.py`
- no `setup.cfg`
- Candidate Runtime cannot import `core.api.shadow` from a neutral directory
- Candidate Runtime contains no installed AIControlCenter distribution
- the current wrapper imports application source from the mutable Git working
  tree
- the approved Candidate commit can be exported with `git archive`

The architecture therefore selected a paired immutable Runtime model instead of
introducing a new packaging system during the Production gate.

No Runtime or service mutation occurred during the architecture decision.

## PI-009A2 State Isolation Discovery

Immutable-source execution exposed a second implicit repository dependency:
application state.

`SQLiteConversationStore` defaulted to `data/conversations.db` and scheduler
heartbeat state defaulted to `data/scheduler.db`.

Because the immutable source artifact is intentionally non-writable, application
initialization correctly failed instead of writing state into the release.

The repair introduced a canonical external application data-root contract while
preserving a development fallback when the environment variable is absent.

A synthetic read-only source test using Candidate Python confirmed that
application source can remain immutable while SQLite state is created outside
the source artifact.

The former Candidate source commit cannot be modified in place. A new Runtime
Candidate is required.

## PI-009A2 A2.1 Completion

After state isolation was repaired, the canonical Runtime bootstrap was
inspected for source identity behavior.

Build mode resolves `git rev-parse HEAD`, requires the Runtime Contract commit to
equal HEAD, requires a clean repository and has no historical-commit build
option.

The architecture therefore adopts the A2.1 completion commit as the source
identity of the next Runtime Candidate rather than extending or bypassing the
canonical bootstrap.

A2.1 implemented immutable source artifact tooling and an immutable-source
wrapper template while preserving external writable state through
`AICONTROLCENTER_DATA_ROOT`.

No operational Runtime mutation occurred.

## PI-009A2 A2.2A Runtime Candidate Build

Runtime Candidate `7b171f135dc7` was built once through the canonical
production Runtime bootstrap from source commit `7b171f135dc7882546bf7f733208778f1aef4943`.

The canonical report recorded a passed Runtime gate, dependency installation,
application import and test suite with no activation.

A separate report-first review validated Runtime identity, `pip check`,
immutable source execution, external application state, unchanged service PID,
unchanged listener PID and HTTP 200/200/405 behavior.

A read-only observation command initially shadowed the shell PATH and therefore
could not invoke curl or git. The observation was repeated using absolute
command paths. This did not trigger a Runtime build retry or service mutation.

The authorized canonical build count remained exactly one.

Milestone:

`NEW_IMMUTABLE_RUNTIME_CANDIDATE_VALIDATED`

## PI-009A2 A2.2B Operational Immutable Source

An operational immutable source artifact was created exactly once for Runtime
`7b171f135dc7` from source commit `7b171f135dc7882546bf7f733208778f1aef4943`.

Builder, validator, manifest, Runtime marker and Runtime metadata all agreed on
the same source identity.

The resulting source artifact was read-only, contained no Git metadata and
successfully loaded `core.api.shadow` using Candidate Runtime Python while
application state was redirected to an external writable data root.

The active Runtime, live wrapper, LaunchDaemon PID and listener PID remained
unchanged.

Two evidence-shell issues occurred after the successful builder operation:
an invalid `/bin/exit` path and use of zsh's reserved `status` variable.
Neither triggered a source build retry or operational service mutation.

The source builder invocation count remained exactly one.

## PI-009A2 A2.3

The shadow service was quiesced before SQLite state migration, eliminating the
live-writer race. Runtime `7b171f135dc7` and its immutable source artifact were
then activated as a matched deployment pair.

Persistent application state moved from repository-local SQLite files to the
AIControlCenter macOS application data root.

The service was restored once and validated using immutable source cwd,
operational database paths, listener identity and HTTP checks.

No automatic rollback or repeated cutover attempt occurred.

## PI-009 Production Authorization

PI-009 reached final human Production authorization for Runtime
`7b171f135dc7` and source commit `7b171f135dc7882546bf7f733208778f1aef4943`.

The final deployment regression passed 2337 tests with 5 deselected.

The initial final review reported LAUNCHD_NOT_RUNNING because its parser
overwrote the top-level launchd state `running` with a nested coalition state
`active`. The corrected V2 review removed the false blocker without any
operational mutation or regression rerun.

The Production authorization itself was governance-only. Runtime, state,
wrapper and LaunchDaemon were not mutated.

## 2026-08-10 — AI-PROVIDER-01C-B Candidate Artifacts

Human authorization was consumed to build Candidate Runtime `102b8f1fa862`
and its matching immutable source exactly once from commit
`102b8f1fa8628d00d25575cb94538826a1a04e10`. Canonical Runtime, source
identity, immutability, and network-free FakeProvider workflow gates passed.

Production remained on `7b171f135dc7`. No activation, launchd operation,
Production database mutation, credential read, or provider network call
occurred. AI-PROVIDER-01C-C remains a separate human authorization gate, and
Notion synchronization is deferred until the final phase.

## AI-PROVIDER-01 Production Completion

Production Runtime `102b8f1fa862` was promoted using the frozen immutable
Candidate.

The initial LaunchDaemon handoff required a separately authorized retry after
macOS administrator authorization rejected the first attempt.

The first authenticated BrainAgent smoke later failed. Read-only diagnosis
classified the failure as a temporary harness-only defect and confirmed that no
repository application repair, Candidate rebuild, repromotion or service
restart was required.

A separate human authorization permitted one corrected authenticated smoke.
The corrected validation used the actual immutable Production BrainAgent and
provider contracts and completed successfully.

The first failed smoke's upstream request occurrence remains unknown and is not
rewritten as zero in governance evidence.
# SEC-01B — Deterministic Provider Secret Delivery

Implemented the repository-only form of Protected File-Per-Provider Secrets with Deterministic Wrapper Injection. Added generic provider mapping, strict file metadata/value-shape validation, sanitized JSON diagnostics, wrapper-mediated environment injection, and business-logic separation. Live Production wrapper, service, state, and Runtime `102b8f1fa862` were not changed.

## 2026-08-10 — SEC-01C-R1 immutable-source regression repair

SEC-01C consumed two live installs and one restart. Its frozen wrapper retained secret delivery but selected mutable repository cwd and `PYTHONPATH`. HTTP recovery did not establish immutable Production convergence; no automatic rollback occurred, and the current installation remains blocked. R1 repaired and focus-tested repository artifacts only, restoring dynamic Runtime/source pairing, identity/content validation, external state, isolated imports, immutable cwd, and Runtime Python safe-path execution without changing the provider helper or business logic. The supplied Runtime `102b8f1fa862` preflight reports `jsonschema` importable. No install or restart occurred; new exact human authorization is required. Notion remains `DEFERRED_UNTIL_FINAL_PHASE`.

## 2026-08-10 — SEC-01C Production secret delivery completed

The separately authorized R1 handoff converged Production to immutable source.
R2 then found that `AICONTROLCENTER_WORKERS_CONFIG` still named mutable
version-controlled config and classified it as `VERSIONED_APPLICATION_CONFIG`.
R3 froze the matching immutable-source config binding without performing its
intended live mutation. R3Q detected precondition drift before mutation: the
logical value was already present but unquoted, and the service was not
converged; its controller consumed zero edit and restart attempts.

Separately authorized R3Q2 changed only that representation to shell-safe
single-quoted form, preserving the logical value, every other worker.env byte,
and `root:staff` mode `0640`, then performed exactly one restart. Evidence
validated a running daemon with matching service/listener PID, immutable cwd and
workers config (SHA-256
`f3167547ee37173ad2cc4069d473b5d44adb9583c9d6d0a761857ba03f61bc1a`), no
mutable repository source/config dependency, external state, HTTP `200/200/405`,
and `OPENAI_API_KEY` presence without printing, persisting, or hashing its value.
Provider calls were zero; no Runtime, source artifact, helper, wrapper, plist,
database, or secret change occurred beyond the authorized representation edit
and restart.

SEC-01C is `COMPLETE`; milestone
`PRODUCTION_DAEMON_SECRET_DELIVERY_VALIDATED`. SEC-01 remains open. Next is
SEC-01D Secret Lifecycle & Recovery Validation. Notion remains
`DEFERRED_UNTIL_FINAL_PHASE`.

<!-- AIHD_RUNTIME_HEALTH_PRODUCTION_2026_08_13 -->
## 2026-08-13 — Runtime Health Model Production Deployment

Runtime Health previously projected Linux/systemd service units even though the
Production Control Plane runs on macOS launchd. This produced false
`unavailable` states for the API, Telegram and Scheduler.

The Runtime Health model was reconciled to the authoritative Mac service
topology. The canonical API is now represented as the required launchd service
`com.aicontrolcenter.api`; Telegram is optional and currently not deployed; the
dedicated Application Scheduler is required but not yet deployed. The existing
persisted scheduler heartbeat is stale, so the aggregate correctly remains
`healthy=false` while topology status is `VALID`.

Release `ed2424e39bb1`
(`ed2424e39bb12e363ae7a1967c677e661ae7ec0e`) passed focused tests and the
canonical repository regression before release staging.

The Runtime and matching immutable Source were built separately without
Production activation. The candidate was then validated on an ephemeral pinned
Shadow lane at `127.0.0.1:18101`, proving that candidate validation does not
need to move the Production pointer. Health, Runtime Health and Homepage
validation passed while the canonical API, existing Shadow and public ingress
remained operational. The candidate was later stopped with one separately
authorized SIGTERM.

Production `runtime/current` converged from `ef07532bd3d7` to
`ed2424e39bb1`. The canonical API subsequently converged to the matching
immutable Source and served the Production API on `127.0.0.1:58081`.
Canonical health, Homepage status, public health, public Homepage and public
Product Management validation all returned HTTP 200. Production
`/runtime/health` matched the new service-topology contract.

The immutable Source remained bytecode-clean and the ProductDraft main SQLite
database content remained unchanged. No automatic retry or external rollback
was used.

The existing Shadow service on `127.0.0.1:18100` remained healthy on the prior
release during closeout. It is not a public upstream and its alignment is
deferred to a separate maintenance Sprint.

The Shadow audit also identified two deployment-tooling debts: effective
Runtime selection is still derived from `runtime/current` before the
runtime-link override is processed, and the legacy Shadow executor contains
automatic external rollback logic incompatible with the current bounded
Production governance model.

Next Runtime Health milestone: deploy the dedicated Mac Application Scheduler
and establish a fresh heartbeat.
