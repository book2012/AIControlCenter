# AI Shopping Platform Architecture

## Current SHOP_ORDER authority — 001A/001B COMPLETE for repository foundation

`SHOP_ORDER_001A` is complete at `65f39d299e53a9be1687bfe46c71fe8c4787b4e4`. `SHOP_ORDER_001B` is complete at `c6b3e3b1578501d4a9845cf00a5895e29e6da065`. These milestones define the AIControlCenter-owned order-create contract and durable operation ledger only; they do not enable a WooCommerce writer or runtime mutation.

### Create boundary

`trusted customer/session boundary`
→ `OrderCreateAuthority`
→ `OrderCreateCommand`
→ `SQLiteOrderCreateLedger`
→ `OrderCreateService`
→ future `OrderCreatePort` implementation.

The customer intent carries only an existing opaque CustomerId, canonical product/variation/quantity, idempotency key, correlation/audit references and UTC request time. Price, totals, currency, tax, discounts, billing/shipping/contact data, payment state and raw provider metadata are not caller authority.

### Durable ambiguity policy

The Mac Control Plane ledger claims before any future provider invocation. Durable states are `CLAIMED`, `COMPLETED`, `TERMINAL_FAILED`, and `UNKNOWN_OUTCOME`. An ambiguous external or post-write failure enters `UNKNOWN_OUTCOME`, where automatic retry is prohibited. Only explicit reconciliation may resolve that quarantine. Operation identity and audit rows are immutable/delete-denied. Same-session refreshed authorization may replay an already completed operation without a second provider write, while another command or session conflicts.

### Validation and activation boundary

- Order/read regression: **83 passed**.
- Existing customer/session security regression: **244 passed, 1 warning**.
- New Order core/ledger contains no HTTP client, Woo credential, Woo write endpoint or non-GET provider transport.
- README requires no change because there is still no customer-facing create route, operator workflow, runtime activation or deployment procedure.
- No Production DB was created or migrated and no Production runtime was changed.

Next: `SHOP_ORDER_001C` must bind the existing trusted CustomerSessionBoundary to OrderCreateAuthority and exercise the service through an inert/fake writer. A real WooCommerce write adapter is a later, separately reviewed milestone.


## Current authoritative SHOP_AI_001C-C3 closeout — COMPLETE for foundation scope only

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

<!-- PUBLIC-STOREFRONT-V2-ACTIVATION-02:BEGIN -->
## Final public ingress topology — Public Storefront V2

Public Storefront V2 is effective under the one-shot authority
`PUBLIC-STOREFRONT-V2-ACTIVATION-02` at source HEAD
`8f1298e6856c4b3df7c8c73be5b3d347841f3ef7`. Host Caddy is the only public
edge. For `https://bokstory.duckdns.org/`, the public root and WordPress
fallback route to WordPress at `127.0.0.1:58082`; the exact GET-only Shopping
API allowlist routes to AIControlCenter at `127.0.0.1:58081`.

The dev host is `https://dev.bokstory.duckdns.org/`. Public Basic Auth is
absent, while dev Basic Auth remains separated and enforced. Public WordPress
admin/login/XMLRPC/wp-json exposure is denied, private and Control Plane
namespaces are denied, and Shopping writes are not publicly proxied. The
legacy `/homepage/storefront` route redirects with HTTP 301. `rest_route`
ambiguity protection is part of the public routing guard.

Live external validation passed for the public root HTTP 200, the Shopping
GET-only allowlist, private/Control Plane path denial, the `rest_route`
ambiguity guard, the legacy redirect, and dev HTTP 401 authentication.

AIControlCenter remains the sole Control Plane and owns Shopping business logic
and orchestration. WordPress remains the CMS and WooCommerce remains the
Commerce Engine. No public route grants WooCommerce write authority or use.

### Activation governance boundary

Activation-02 consumed its authorization exactly once after fresh pre-reload
re-observation, attempted Caddy reload exactly once, recorded reload count `1`,
and loaded V2. WordPress and database generations were unchanged. The cutover
performed no automatic retry or rollback and no Docker, Colima, WordPress,
WooCommerce, database, or Ubuntu lifecycle mutation. Activation-03 is
superseded historical evidence, not current authority; its focused regression
contained one pre-existing baseline failure, the base and Activation-02
candidate failure sets were equivalent, and Activation-02 introduced zero new
Activation-03 failures.

The next Shopping milestone is read-only-first WooCommerce order data
integration, `READ_ORDER`: monitoring, then validation, with write operations
deferred until separately governed. This topology closeout does not assert that
the entire platform is production-ready.
<!-- PUBLIC-STOREFRONT-V2-ACTIVATION-02:END -->
