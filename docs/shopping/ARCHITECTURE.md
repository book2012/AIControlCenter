# AI Shopping Platform Architecture

<!-- SHOP_AI_001C-C5-C3A_CLOSEOUT -->
## Current authoritative SHOP_AI_001C-C5-C3A architecture

`SHOP_AI_001C-C5-C3A` trusted authenticated-read authorization foundation is
**COMPLETE for the offline authorization scope only**.

Canonical evidence:

- implementation commit: `e30ca8dd4b289ba57aa0e3106d5d50eb0b72ff6e`
- parent: `7e61ee54fccbd871c0162bc726063982fad233a7`
- reviewed implementation patch SHA256:
  `5586b5c52de1a0f200753b3280676c8511a57a6df0b9e29142ecab605581b335`
- focused authorization tests: **31 passed**
- SHOP_AI file-isolated regression: **49/49 files, 898 passed, 1 deselected**
- deterministic static/security review: **PASS**

C5-C3A establishes an AIControlCenter-owned, Twilio-specific trusted
authenticated-read authorization authority.

The trust model is authority-registry based. A capability-shaped object is not
trusted merely because a caller possesses it. The issuing AIControlCenter
authority must have the authoritative issuance record.

Authorization is bound exactly to provider, read operation, request identity,
correlation identity, Verify Service SID, and Verification SID where required.

Capabilities are opaque, short-lived, limited to a maximum lifetime of
60 seconds, and one-shot. A first trusted authorization attempt consumes the
capability. Forged, expired, reused, cross-authority, or binding-mismatched
capabilities fail closed.

The generic C5-B `ProviderNetworkAuthorizationGate` remains
`OFFLINE_DENY_ONLY` and has not gained an allow path.

C5-C3A performed no provider network call, credential resolution, Keychain
access, Twilio SDK activation, SMS send, deployment, production activation,
schema migration, or Ubuntu mutation.

This milestone does not grant live authenticated provider authorization and
is not a production-readiness claim.

Next milestone:

`SHOP_AI_001C-C5-C3B` — offline SecretReference / Mac Secret Resolver /
EphemeralSecretLease and Twilio authenticated-read transport composition
contract.

C5-C3C remains separately approval-gated for any real Keychain resolution or
authenticated Twilio GET network call.


<!-- SHOP_AI_001C-C5-C2_CLOSEOUT -->
## Current authoritative SHOP_AI_001C-C5-C2 architecture

`SHOP_AI_001C-C5-C2` provider-specific Twilio Verify v2 read-only foundation is
**COMPLETE for the offline C5-C2 scope only**.

Canonical implementation evidence:

- code commit: `7928456fa25ab70f6fa87badd2cc035743d9dd37`
- parent documentation baseline: `6b355a9d3bfc726242c71545102f635ce2f98675`
- reviewed implementation patch SHA256:
  `4284206189afb8a611af2404e145bfb5692e584e2954688b184e5771a6f6f344`
- focused C5-C validation: **4/4 files, 43 passed**
- full SHOP_AI file-isolated gate: **45/45 files, 867 passed, 1 deselected**
- final deterministic architecture/security review: **PASS**

Architecture remains fail-closed. AIControlCenter on the Mac mini is the sole
Control Plane. The C5-B generic authorization boundary remains
`OFFLINE_DENY_ONLY`.

C5-C2 selects `twilio.verify.v2` only for a provider-specific offline read
contract. The implementation exposes bounded GET-only request specifications
for one Verify Service and one Verification resource and normalizes provider
responses into bounded evidence. Provider status is evidence and is not
automatically converted into C4 terminal truth.

No provider network transport was constructed or called. No credentials were
resolved, no Keychain access occurred, no SMS was sent, no Twilio SDK was
activated, no schema or production migration was executed, no production
route or deployment was activated, and Ubuntu was untouched.

`VerificationReconciliationService` remains the sole durable C4 reconciliation
writer. `UNKNOWN_OUTCOME` remains blocked from terminal C4 admission.

C5 as a whole is not complete and this is not a production-readiness claim.
The next milestone is `SHOP_AI_001C-C5-C3` for explicitly approval-gated,
provider-specific authenticated read activation. Real credentials, Keychain
resolution, and authenticated provider network calls require separate explicit
authorization.


## Historical SHOP_AI_001C-C5-B closeout — COMPLETE for C5-B offline foundation scope only

`SHOP_AI_001C-C5-B` Provider-Neutral Offline Provider Integration Foundation is
**COMPLETE for C5-B offline foundation scope only** at canonical code commit
`c4bcd6a8cbe0c2d36afe282f4e561559dbbb2885`, with parent C4 documentation
commit `37fb765142de909ce62bd42f3ad428dec3b3481d`. The reviewed
implementation patch SHA256 is
`ddc26b31978eb226df3f326540657b80bc74102a34365d50c63a402a29fd8d2f`.

### C5-B validation evidence

- C5 focused: **8/8 files, 39 passed, 0 deselected**.
- Full SHOP_AI file-isolated gate: **41/41 files, 824 passed, 1 deselected**.
- Final adversarial architecture/security review: **PASS**.

### C5-B Control Plane and authorization model

- AIControlCenter on the Mac mini remains the sole Control Plane. Ubuntu is
  untouched and remains only an optional stateless infrastructure worker.
- C5-B is provider-neutral and `OFFLINE_DENY_ONLY`. Generic provider
  authorization cannot permit an authenticated provider request.
- No generic capability issuer exists. No generic caller-injected trusted
  capability authority exists. A capability object supplied by a caller is
  not trusted.
- Configuration, activation state, provider and operation allowlists,
  environment, and a capability object are each insufficient to authorize
  provider I/O. The generic authorization decision remains deny-only.
- Trusted capability issuance and verification are explicitly deferred to a
  future AIControlCenter Control Plane/provider-specific C5-C boundary.

### Inert runtime and offline safety boundary

- `DISABLED` and `CONTRACT_ONLY` runtime compositions remain inert.
- Provider-specific transport is not constructed, credentials are not
  resolved, and `SecretReference` remains value-free metadata only.
- No Keychain access occurred. No provider was selected. No provider SDK or
  network request occurred. No SMS was sent.
- No automatic retry or provider fallback exists. No route/dashboard
  activation, schema or production migration, deployment, or production
  activation occurred. C5-B has no SQLite persistence authority.

### C4 admission boundary

- `UNKNOWN_OUTCOME` may exist only as bounded unresolved provider evidence.
  C5-B blocks it from C4 reconciliation admission.
- Normalized provider verification identifier accepts only the exact bounded
  `ProviderVerificationIdentifier` contract or `None`; subclasses, raw
  values, and other identifier objects are rejected.
- Provider identifier presence and value binding are exact and fail-closed:
  evidence and the C4 command must both carry the same exact identifier, or
  both carry `None`.
- `VerificationReconciliationService` remains the sole durable reconciliation
  writer. The C5-B evidence adapter has no SQLite or persistence authority and
  forwards only bounded normalized evidence to the existing C4 port.

### Explicit C5-B non-activation statement

C5-B authorizes no credentials, Keychain access, provider network calls, SMS,
production provider selection, deployment, migration, or production
activation. The overall Shopping platform is not production-ready. The next
milestone is `SHOP_AI_001C-C5-C — Provider-Specific Authenticated Read-Only
Integration`, which must select or formally defer the provider and introduce a
provider-specific authenticated-read adapter/transport boundary under separate
approval gates.

## Historical SHOP_AI_001C-C4 closeout — COMPLETE

`SHOP_AI_001C-C4` Durable UNKNOWN_OUTCOME Quarantine / Reconciliation was
**COMPLETE** at code, test, and architecture level. The initial local code
commit was `50bd8d9203dfa977f257d8fa48186460c894244c`. A post-commit
read-only review discovered blockers in the initial implementation; that
commit was not pushed before corrective validation. Corrective safety commit
`ea8878c0606c2a63c9cf858fff0f7218d12066bd` closes those blockers without
rewriting Git history.

### Validation evidence

- Final read-only architecture review: **PASS**.
- Focused corrective gate: **6/6 test files, 112 passed**.
- Full SHOP_AI file-isolated gate: **33/33 files passed, 785 passed,
  1 deselected**.
- Pytest cleanup/deprecation warnings were non-failing.

### Durable state machine

The durable model is the lifecycle projection plus
`shopping_verification_unknown_outcomes` plus append-only
`shopping_verification_reconciliation_events`.

- A provider ambiguity is recorded durably as an unknown outcome without
  converting the domain lifecycle into an `UNKNOWN` status.
- `START_UNKNOWN` can reach terminal reconciliation only after validated
  bounded provider evidence establishes the terminal truth. An operator's
  selected terminal truth alone is forbidden.
- `VERIFY_UNKNOWN` remains durable and fail-closed until explicit
  reconciliation; it is not silently converted, retried, or treated as
  success.
- Reconciliation requires explicit AIControlCenter Control Plane capability
  authority. CAS/version checks prevent stale writes, and the reconciliation
  event history is append-only.
- C1 durable replay and `_replay_result` remain preserved. Provider rejection
  publication rechecks local expiry before it is published.

### Quarantine and persistence contract

v3 persistence structurally validates the required C4 tables and triggers,
including the lifecycle projection, `shopping_verification_unknown_outcomes`,
and `shopping_verification_reconciliation_events`. The forbidden
`shopping_verification_quarantines` table is rejected. Domain
`VerificationStatus.UNKNOWN` is forbidden. Provider-transport
`ProviderTransportVerificationStatus.UNKNOWN` is transport-only and may
exist only as transport ambiguity input; it is not a durable domain state.

### Authority and fail-closed boundary

AIControlCenter on the Mac mini remains the sole verification and
reconciliation authority. No operator-selected terminal result can bypass
validated bounded provider evidence, explicit capability authority, CAS, or
append-only history. Unknown outcomes remain durable and fail-closed until the
authorized reconciliation path completes.

No provider SDK activation, live provider call, credentials, Keychain,
production migration, deployment, route activation, or Ubuntu mutation
occurred. C4 introduces no production activation. C5 provider credentials,
authenticated calls, and Keychain remain separately approval-gated, and the
overall Shopping platform is not production-ready.

### Next milestone

`SHOP_AI_001C-C5 — Provider-Specific Authenticated Non-Production Integration`

## Historical SHOP_AI_001C-C3 closeout — COMPLETE for foundation scope only

`SHOP_AI_001C-C3` Destination Resolution + Mac Secret Resolver Foundation is
**COMPLETE for foundation scope only** at canonical code commit
`72310b63710d6fc13eb14e85ad133318454bb430`, parent
`0de8b7ef0522b53f2089c1c302075f5d6264400c`, with an exact code scope of
**15 paths**. The reviewed implementation patch SHA256 is
`e6a07f0e2f60c7e13a33a15edfa06eb33b2bcc286bb4bebf2fc1cd4055452f45`.

### Validation and harness boundary

- C3 focused regression: **22 passed**.
- Canonical SHOP_AI validation was file-isolated: **29/29 test files passed**.
- Aggregate evidence across those isolated processes: **747 passed, 1
  deselected, 16 warnings**.
- The existing API runtime baseline defect
  `tests/test_shop_ai_01b3_api_runtime.py::test_app_creation_does_not_create_product_draft_database`
  remains explicitly excluded and was not fixed by C3.
- A monolithic multi-file SHOP_AI pytest invocation is not the canonical gate:
  API-oriented test collection/import can leave `core.api.app` in
  `sys.modules`, violating the isolation precondition of persistence/security
  tests. File-per-process validation removes this harness contamination. The
  monolithic harness collision is not an application regression.

### C3 architecture and preserved authority

- `CanonicalPhone` diagnostics redact raw phone representation.
- `DestinationHandle` is opaque, immutable, transient, request-scoped, and
  one-shot. Scope validation binds trusted provider, purpose, challenge,
  replay, customer, browser, and binding dimensions.
- `Mac ProviderDestinationResolver` is process-local and in-memory only.
- Raw destination is not persisted in SQLite, receipts, audit, JSON, or
  provider-neutral application results.
- `ChallengeStartRequest` and `ProviderTransportStartRequest` carry only an
  opaque destination capability.
- Existing C1 verification persistence, result, and session authority remains
  intact.
- Generic `ProviderPhoneVerificationAdapter` forwards the capability but does
  not resolve the destination.
- `SecretReference` remains value-free metadata.
- `SecretResolverPort` returns a redacted one-shot `EphemeralSecretLease`.
  `Mac ProviderSecretResolver` uses only an explicitly injected reader
  foundation.
- Default runtime performs zero Keychain reads, zero credential reads, zero
  provider-network calls, and no provider-specific SDK construction. Default
  runtime remains inert/disabled.
- Mac mini remains the sole Control Plane. Ubuntu receives no raw phone,
  provider credentials, verification authority, application state, or business
  logic.

### Explicit C3 exclusions

No commercial SMS provider selection, provider SDK, authenticated provider
call, Keychain access, environment credential materialization, production
credential, route/API activation, schema/migration change, deployment,
production activation, Ubuntu mutation, Telegram implementation, or durable
`UNKNOWN_OUTCOME` lifecycle/schema change.

### Known unresolved architecture and next milestone

`UNKNOWN_OUTCOME` is still not durably quarantined/reconciled. Do not reopen C1
persistence inside this C3 closeout. This must be resolved before authenticated
provider integration.

README review requires no change because C3 introduces no customer-facing
route, real provider capability, production activation, deployment procedure,
or operator workflow; `README.md` remains unchanged.

The next engineering milestone is exactly:
`SHOP_AI_001C-C4 — Durable UNKNOWN_OUTCOME Quarantine / Reconciliation`.

After C4, provider-specific authenticated non-production integration remains a
separately gated milestone.

## Historical SHOP_AI_001C-C2 closeout — COMPLETE

`SHOP_AI_001C-C2` Provider Adapter Foundation is **COMPLETE** at canonical
code commit `4c9f8851f39b944f0d875694c44f998ae5ad1000`, parent
`fd64c2395778c69ecad0a3e1f662e1fe88444d97`, with a validated code scope of
**12 paths**.

### Validation and baseline technical debt

- C2/C1 regression: **74 passed, pytest exit 0**.
- Broader SHOP_AI regression: **506 passed, 1 warning, pytest exit 0**.
- API runtime excluding one proven pre-existing baseline defect: **6 passed,
  1 deselected, 11 warnings, pytest exit 0**.
- Excluded test:
  `tests/test_shop_ai_01b3_api_runtime.py::test_app_creation_does_not_create_product_draft_database`.
  The untouched parent commit fails the same test with
  `sqlite3.OperationalError` because the configured `inquiries.db` parent
  directory is absent. This is pre-existing technical debt only, not a C2
  blocker; C2 did not fix it.

### Preserved application and authority contracts

- Existing `PhoneVerificationPort` remains unchanged.
- C1 persistence, verification service, session service, normalization, and
  customer authentication remain unchanged.
- `ProviderPhoneVerificationAdapter` is provider-neutral.
- `ProviderTransportPort` provides typed closed START/VERIFY contracts.
- The inert transport is unavailable, zero-network, and has no automatic
  retry. Its stable bounded failure taxonomy is:
  `PROVIDER_UNAVAILABLE`, `TIMEOUT`, `MALFORMED_RESPONSE`, `REJECTED`,
  `AMBIGUOUS_PROVIDER_IDENTIFIER`, and `UNKNOWN_OUTCOME`.
- Timeout policy defaults to 10 seconds and is capped at 30 seconds.
- `SecretReference` contains value-free backend/key-name metadata only. C2
  does not resolve or materialize secret values.
- `ProviderTransportVerifyRequest` is the C2 OTP serialization/privacy
  boundary. The existing `ChallengeVerificationRequest` application contract
  was not altered.
- Provider timestamps are evidence only. AIControlCenter remains authorization,
  time, and policy authority. Trusted application requests own customer,
  challenge, replay, and phone-binding authority; provider payload does not.

### Activation and deployment boundary

- Default runtime provider verification remains disabled.
- C2 adds no new routes or API activation, schema or migration, provider SDK,
  real network/provider call, credentials, production provider selection, or
  production activation.
- Ubuntu gains no authority, state, or business logic.
- README review requires no change because C2 adds no customer-facing route,
  real provider capability, production activation, or operational procedure;
  `README.md` remains unchanged.

### Explicitly deferred to C3 or later

1. Destination-phone resolution trust boundary required for real SMS delivery.
2. Mac secret resolver and real provider-specific transport.
3. Authenticated non-production provider integration.
4. Durable `UNKNOWN_OUTCOME` quarantine/recovery policy, because changing it
   would reopen C1 persistence/lifecycle authority.
5. Production credentials.
6. Production migration.
7. Customer-facing E2E and runtime activation.

The next milestone is exactly:
`SHOP_AI_001C-C3 — Destination Resolution + Mac Secret Resolver Architecture`.

The preserved downstream sequence is:
`SHOP_ORDER_001 → SHOP_AI_002 → SHOP_AI_003 → TG_SALES_001 → SHOP_E2E_001`.

## Historical SHOP_AI_001C-C0/C1 closeout

`SHOP_AI_001C-C0` Durable Challenge / Attempt Persistence Design and
`SHOP_AI_001C-C1` Durable verification persistence are **COMPLETE**. The exact
code commit is
`57c6c4e96ff13ea3ce727dd1910c276c08e62eee`, with an exact code scope of 7
files. The targeted regression was **148 passed, 1 warning, pytest exit 0**;
the SHOP_AI regression was **473 passed, 1 warning, pytest exit 0**.

### Authority and invocation boundary

- Mac AIControlCenter is the sole verification authority.
- Ubuntu has zero verification, business-logic, or application-state
  authority.
- Durable `START_CLAIMED` occurs before provider-start invocation.
- Provider invocation occurs outside the SQLite transaction.
- Concurrent exact starts permit one provider invocation.
- An uncertain provider-start outcome fails closed and cannot auto-reinvoke.
- Immutable provider-start evidence is stored separately from lifecycle state.
- SQLite is the sole durable replay authority; there is no process-local
  authorization or replay authority.

### Durable data and security semantics

- OTP is provider transport input only. OTP, OTP digest, and OTP HMAC are not
  durable replay state or identity.
- Raw phone, OTP, raw provider payload, and credentials are excluded from
  durable verification state, audit, and trusted receipt.
- Opaque phone binding is durable.
- `provider_source + provider_verification_id` uniqueness is durable.
- TX1 atomically covers attempt, challenge, trusted-receipt provenance, and
  audit, and validates the returned trusted object before commit.
- TX2 atomically validates durable provenance, consumes the receipt, creates
  the session, records B3 consumption/audit, and validates the projection
  before commit.
- The injected AIControlCenter UTC clock remains authorization time authority;
  provider timestamps are evidence only.
- B3-A receipt/session security semantics remain preserved.

### Schema and activation boundary

- The fresh/current customer persistence foundation is schema v2.
- Historical v1 is not silently upgraded or reinterpreted.
- Existing v1 requires a separately authorized explicit migration.
- C1 did not execute production migration or backfill.
- Production phone provider: **NOT IMPLEMENTED**.
- Provider credentials: **NOT MATERIALIZED**.
- Production DB migration: **NOT STARTED**.
- Production provider runtime activation: **NOT AUTHORIZED**.
- No production/provider/network access occurred and no deployment occurred.

README review found no content change required because production provider
capability is not ready; `README.md` remains unchanged.

The next engineering milestone is exactly:
`SHOP_AI_001C-C2 — Provider Adapter Foundation`.

C2 consists of a provider-neutral adapter, inert/fake transport first,
timeout/malformed-response mapping, a Mac-only secret-reference boundary, and
disabled-by-default composition.

The preserved roadmap sequence is:
`SHOP_AI_001C → SHOP_ORDER_001 → SHOP_AI_002 / SHOP_AI_003 → TG_SALES_001 → Telegram Customer Order E2E`.

## SHOP-AI-01A ProductDraft generation foundation

`SHOP-AI-01A_PRODUCT_DRAFT_GENERATION_FOUNDATION_READY` preserves
`core/shopping/` as the canonical domain and reuses the SHOP-02 ProductDraft
aggregate, existing `ProposedFields`, and immutable revision construction.
Structured generation contract `1.0.0` accepts only the existing proposed
fields. Generated values receive AI `SuggestionProvenance`; each candidate
remains `LifecycleState.DRAFT`. Generation does not validate, approve, create
deployment intent, persist, or expose a mutation surface.

The Shopping adapter reuses canonical `core.providers.ProviderAdapter`. It has
one injected provider, `RetryPolicy(max_attempts=1)`, a timeout bounded to 60
seconds, and no provider fallback. The command snapshots source context as
canonical JSON; provider request identity remains in result and audit
projection. The operation key is claimed before provider invocation, yielding
**AT-MOST-ONE provider invocation per consumed operation key within the
injected coordinator's durability scope** and concurrent duplicate
suppression. It is not a global exactly-once guarantee. The current
`InMemoryProductDraftGenerationOperationCoordinator` is explicitly
non-production.

Durable ProductDraft persistence, durable operation ledger, transactional
revision/audit/operation Unit of Work, generation API, Dashboard generation
mutation, recommendation/ranking, WooCommerce write integration, Production
mutation authority, automatic retry, and automatic rollback are not
implemented. Next:
`SHOP-AI-01B_DURABLE_PRODUCT_DRAFT_GENERATION_TRANSACTION`, starting with
architecture/discovery of existing persistence and transaction conventions.
No ProductDraft or AI application state may reside on Ubuntu. Canonical detail:
[`SHOP-AI-01A-PRODUCT-DRAFT-GENERATION-FOUNDATION.md`](../architecture/SHOP-AI-01A-PRODUCT-DRAFT-GENERATION-FOUNDATION.md).

## SHOP-01A2 reconciled baseline

SHOP-01A is a retrospective reconciliation of existing SHOP-01/02/03 work.
`core/shopping/` remains the canonical domain. SHOP-01A1 HEAD is
`f95ba9ae2133b55db06c362df321b16785f21423`; the canonical regression command
`ops/macos/validation/run-deployment-regression-gate.sh -q` reported `2670
passed, 5 deselected, 437 warnings`.

The runtime is GET-only and composed through
`build_default_shopping_service()` for both `/shopping` and the Shopping
dashboard. One read invocation permits one outbound HTTP GET attempt; automatic
retry is disabled. Production mutation authority is disabled. The intercepted
SHOP-03 adapter remains active library code, but no Production write transport,
Production credential provider, runtime/API wiring, or mutation endpoint
exists. The canonical utilization matrix and history reconciliation are in
[`SHOP-01A2-REPOSITORY-UTILIZATION-AND-ARCHITECTURE-RECONCILIATION.md`](../architecture/SHOP-01A2-REPOSITORY-UTILIZATION-AND-ARCHITECTURE-RECONCILIATION.md).

## Purpose

AI Shopping Platform is a service domain inside AIControlCenter.

It is not a traditional WordPress shopping site implementation.

## Responsibility Model

### WordPress

- Shopping homepage
- Product presentation
- Category presentation
- Blog
- Landing pages
- CMS

### WooCommerce

- Products
- Orders
- Customers
- Inventory
- Coupons
- Payment and commerce state

### AIControlCenter

- Shopping business logic
- Shopping API
- AI workflows
- Approval policies
- Recommendations
- Pricing analysis
- Automation policies
- Audit status
- Operational validation

### AI Agent

- Product draft generation
- SEO draft generation
- Product description generation
- Category recommendation
- Review summary generation
- Approved update execution

### n8n

- External workflow execution
- Email
- Notifications
- Webhooks
- Scheduled integrations

## Runtime Model

Current runtime: Virtual development environment

Production target: Mac mini M4

The same application code must be used in development and production.

Environment differences must be configuration-only.

## Worker Boundary

Ubuntu remains an infrastructure worker.

Shopping business logic, AI logic and application state must not be
implemented on Ubuntu.

## Safe Update Workflow

AI draft
to policy validation
to human approval
to controlled WooCommerce REST update
to WordPress presentation
to audit event

## Initial Safety Mode

- Read-only
- Approval required
- AI execution disabled
- Automation disabled

<!-- SHOPPING_M4_START -->

## M4 Architecture

AIControlCenter
    |
    +-- ShoppingSettings
    |
    +-- ShoppingService
    |
    +-- Adapter Factory
            |
            +-- MockCommerceCatalogAdapter
            |
            +-- WooCommerceRESTAdapter
                    |
                    +-- WordPress and WooCommerce

### URL Separation

- Canonical signing URL: external WordPress URL
- Internal connection URL: localhost WordPress port
- External development UI: http://bokstory.iptime.org:58088
- Internal REST connection: http://127.0.0.1:8088

### Security

- WooCommerce API Key is read-only.
- Secret files are excluded from Git.
- systemd runtime Secret permissions are 600 root:root.
- Production requires a user-owned domain and HTTPS.
- iptime.org CAA policy prevents certificate issuance for the current DDNS hostname.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## M5 Storefront Architecture

WooCommerce
    |
    v
WooCommerceRESTAdapter
    |
    v
ShoppingService
    |
    +-- Featured Products
    +-- Search
    +-- Categories
    +-- Image URL normalization
    |
    v
AIControlCenter REST API
    |
    v
AI Shopping Storefront Plugin
    |
    +-- API Client
    +-- Cache
    +-- Shortcodes
    +-- Renderer
    +-- CSS
    |
    v
WordPress Presentation Layer

### WordPress Responsibilities

- User input rendering
- Input sanitization
- API request forwarding
- Short-lived response cache
- HTML and CSS rendering
- Error fallback messages

### Forbidden WordPress Responsibilities

- Product recommendation decisions
- Price calculation
- Inventory policies
- AI provider calls
- Order automation
- Approval workflows
<!-- SHOPPING_M5_END -->

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


Management read path:

Dashboard
→ AIControlCenter Dashboard API
→ Shopping management read model
→ existing Shopping snapshot queries
→ existing WooCommerce read adapter

The management read model may aggregate and present existing Shopping
contracts but may not become a second source of product truth.
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

## SHOP-02A Aggregate

ProductDraft is an AIControlCenter-owned proposal made of immutable revisions derived from WooCommerce snapshots. Validation is deterministic, approval is human-only and revision-bound, and deployment intent is non-executable. `DEPLOYED` is intentionally absent. WooCommerce remains source of truth and Ubuntu owns no state or logic.

## SHOP_AI_001C-C5-C3B — Offline Secret Delivery

C5-C3B adds the provider-specific secret-delivery seam without activating provider I/O.

Architecture:

`AIControlCenter trusted authorization -> Twilio credential references -> SecretResolverPort -> EphemeralSecretLease -> future Twilio authenticated-read transport`

Rules:
- AIControlCenter remains the sole Control Plane.
- C5-B `ProviderNetworkAuthorizationGate` remains `OFFLINE_DENY_ONLY`.
- C5-C3A trusted capability authorization remains authoritative.
- Generic business services never resolve provider secrets.
- Provider secret values may only reach a provider-specific transport through an ephemeral lease.
- C5-C3B itself performs no `resolve()` or lease `consume()`.
- No network, Keychain access, SMS, write operation, deployment, schema migration, or Ubuntu mutation is permitted.
- Canonical SHOP_AI regression execution is file-isolated; monolithic single-process pytest is not a production gate because existing test modules have shared-process isolation interference.

Live authenticated provider reads belong exclusively to separately approval-gated C5-C3C.

<!-- SHOP_AI_001C-C5-C3C0_CLOSEOUT -->
### C5-C3C0 offline authenticated-read runtime boundary

C5-C3C0 preserves the Mac AIControlCenter as the sole control-plane authority.

The authenticated-read sequence is authorization-first:

`TwilioAuthenticatedReadAuthority -> bounded request -> SecretReference boundary -> resolver/lease seam -> Twilio-specific GET transport seam -> bounded provider normalization`

C5-C3C0 permits only `READ_HEALTH` and `READ_EVIDENCE`. Request specifications are GET only. A capability is consumed on the first trusted authorization attempt. Transport execution is limited to one attempt with no retry and no fallback.

`SecretReference`, `SecretResolverPort`, and `EphemeralSecretLease` remain the credential-delivery contracts. C5-B `OFFLINE_DENY_ONLY` remains unchanged and C5-C3A remains the trusted Twilio read authority.

C5-C3C0 is offline validation only. It does not perform real macOS Keychain resolution, credential access, provider network access, SMS delivery, deployment, database authority changes, or Ubuntu mutation.

Canonical SHOP_AI regression is file-isolated. C5-C3C0 closed with 53 test files passing, 928 tests passed, and 1 known baseline deselection.

<!-- SHOP_AI_001C-C5-C3C-H1 -->
## C5-C3C-H1 Authenticated Read Authority Hardening

AIControlCenter remains the sole authority for provider-specific
authenticated-read capabilities.

The Twilio authority now maintains only bounded in-memory capability
state. Retired records are pruned after their bounded retention
window. An issuance ID that collides with any still-retained record
fails closed; it is never silently reused.

The following invariants remain unchanged:

- Twilio provider source must match exactly.
- READ_HEALTH and READ_EVIDENCE remain the only admitted C5-C3C reads.
- Capability binding covers provider, operation, request identity,
  correlation identity, service SID, and verification SID where applicable.
- The first trusted authorization attempt consumes the capability.
- C5-B generic network authorization remains OFFLINE_DENY_ONLY.
- Provider transport is GET-only with one attempt, zero retry, and
  zero fallback.
- Provider observations are evidence only; C4 remains the sole durable
  lifecycle/reconciliation writer.
- UNKNOWN_OUTCOME cannot become terminal C4 truth automatically.
- No provider credential, raw response, phone number, or secret becomes
  durable application state.

H1 itself performs no provider network, credential resolution,
Keychain access, SMS operation, deployment, or Ubuntu mutation.

Validation evidence: 936 SHOP_AI tests passed with the single known
baseline deselection. Code commit `ce29a16bb06c21eed92c515d909ee3afbf3ae067`.
